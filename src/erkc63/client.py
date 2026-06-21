from __future__ import annotations

import asyncio
import datetime as dt
import functools
import logging
from decimal import Decimal
from typing import (
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Coroutine,
    Final,
    Iterable,
    Mapping,
    Self,
)

import aiohttp
import yarl

from .errors import (
    AccountBindingError,
    AccountNotFound,
    AuthenticationError,
    AuthenticationRequired,
    SessionRequired,
)
from .parsers import (
    AccountInfo,
    Accrual,
    AccrualDetalization,
    Accruals,
    MeterHistory,
    MeterInfo,
    MeterValue,
    MonthAccrual,
    Payment,
    PublicAccountInfo,
    ajax_attr,
    date_last_accrual,
    date_to_dmy,
    dmy_to_date,
    parse_accounts,
    parse_token,
)

try:
    import orjson

    JSON_DECODER = orjson.loads

except ImportError:
    import json

    JSON_DECODER = json.loads

QRCODE_SUPPORT = True

try:
    from .parsers.qrcode import AccrualData, erkc_data, peni_data

except ImportError:
    QRCODE_SUPPORT = False


_LOGGER: Final = logging.getLogger(__name__)

_MIN_DATE: Final = dt.date(2018, 1, 1)
_MAX_DATE: Final = dt.date(2099, 12, 31)

_BASE_URL: Final = yarl.URL("https://lk.erkc63.ru")

type ClientMethod[T, **P] = Callable[Concatenate[ErkcClient, P], Coroutine[Any, Any, T]]


def api[T, **P](
    *,
    auth_required: bool = False,
    public: bool = False,
) -> Callable[[ClientMethod[T, P]], ClientMethod[T, P]]:
    """Декоратор методов клиента"""

    def decorator(func: ClientMethod[T, P]):
        @functools.wraps(func)
        def _wrapper(self: ErkcClient, *args: P.args, **kwargs: P.kwargs):
            if not self.opened:
                raise SessionRequired("Сессия не открыта.")

            if public:
                if self.authenticated:
                    raise AuthenticationRequired(
                        "Публичный API работает без аутентификации."
                    )

            elif auth_required:
                if not self.authenticated:
                    raise AuthenticationRequired("Требуется аутентификация.")

            return func(self, *args, **kwargs)

        return _wrapper

    return decorator


class ErkcClient:
    """Клиент личного кабинета ЕРКЦ."""

    _session: aiohttp.ClientSession
    _login: str | None
    _password: str | None
    _token: str | None
    _accounts: tuple[int, ...] | None

    def __init__(
        self,
        login: str | None = None,
        password: str | None = None,
        *,
        session: aiohttp.ClientSession | None = None,
        auth: bool | None = None,
        close_connector: bool | None = None,
    ) -> None:
        """Инициализация клиента.

        Parameters:
            login: E-mail личного кабинета. Опционально.
            password: Пароль личного кабинета. Опционально.
            session: Внешняя клиентская сессия `aiohttp.ClientSession`. Опционально.
            auth: Авторизоваться при открытии. Если не указано, будет `True` при указании `login` and `password`.
            close_connector: Закрыть коннектор сессии при закрытии. Если не указано, будет `True` если `session` также не указан.
        """

        self._session = session or aiohttp.ClientSession()
        self._login = login
        self._password = password
        self._accounts = None
        self._token = None
        self._auth = bool(login and password) if auth is None else auth
        self._close_connector = (
            session is None if close_connector is None else close_connector
        )

    async def __aenter__(self) -> Self:
        try:
            await self.open()

        except Exception:
            await self.close()
            raise

        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    def __call__(self, *, auth: bool) -> Self:
        self._auth = auth
        return self

    def _post(
        self,
        path: str,
        **data: Any,
    ):
        data["_token"] = self._token
        _LOGGER.debug("POST: path=%r, data=%r", path, data)

        return self._session.post(_BASE_URL.joinpath(path), data=data)

    def _get(
        self,
        path: str,
        **params: Any,
    ):
        _LOGGER.debug("GET: path=%r, params=%r", path, params)

        return self._session.get(_BASE_URL.joinpath(path), params=params)

    async def _ajax(
        self,
        func: str,
        account: int | str | None,
        **params: Any,
    ) -> Any:
        path = f"ajax/{self._account(account)}/{func}"

        async with self._get(path, **params) as resp:
            return await resp.json(loads=JSON_DECODER)

    def _history(
        self,
        what: str,
        account: int | str | None,
        start: dt.date,
        end: dt.date,
    ) -> Awaitable[list[list[Any]]]:
        params = {"from": date_to_dmy(start), "to": date_to_dmy(end)}

        return self._ajax(f"{what}History", account, **params)

    def _update_token(self, html: str) -> None:
        self._token = parse_token(html)
        _LOGGER.debug("CSRF токен: %r", self._token)

    def _update_accounts(self, html: str) -> None:
        self._accounts = parse_accounts(html)
        _LOGGER.debug("Привязанные лицевые счета: %r", self._accounts)

    @property
    def connector_closed(self) -> bool:
        """Коннектор сессии закрыт."""

        return self._session.closed

    @property
    def opened(self) -> bool:
        """Сессия открыта."""

        return self._token is not None

    @property
    def authenticated(self) -> bool:
        """Клиент аутентифицирован."""

        return self._accounts is not None

    @property
    def accounts(self) -> tuple[int, ...]:
        """Привязанные лицевые счета."""

        if self._accounts is None:
            raise AuthenticationRequired("Требуется аутентификация.")

        return self._accounts

    @property
    def account(self) -> int:
        """Основной лицевой счет."""

        if x := self.accounts:
            return x[0]

        raise AccountNotFound("Отсутствует основной лицевой счет.")

    def _account(self, account: int | str | None) -> int:
        if account is None:
            return self.account

        try:
            account = int(account)

        except ValueError:
            raise ValueError("Лицевой счет не является целым числом.") from None

        if account <= 0:
            raise ValueError("Лицевой счет должен быть больше нуля.")

        if account in self.accounts:
            return account

        raise AccountNotFound(f"Лицевой счет {account} не найден.")

    async def open(
        self,
        login: str | None = None,
        password: str | None = None,
        auth: bool | None = None,
    ) -> None:
        """Открыть сессию с опциональной авторизацией в личном кабинете.

        Parameters:
            login: E-mail личного кабинета. Опционально. Будет сохранен в клиенте в случае успешной аутентификации.
            password: Пароль личного кабинета. Опционально. Будет сохранен в клиенте в случае успешной аутентификации.
            auth: Авторизоваться при открытии. Если не указано, берет из клиента.

        Raises:
            AuthenticationError: При ошибке аутентификации.
        """

        if not self.opened:
            _LOGGER.debug("Открытие сессии")
            # "Открытие сессии" происходит с помощью захвата CSRF-токена со страницы аутентификации
            async with self._get("login") as resp:
                self._update_token(await resp.text())

        if auth is None:
            auth = self._auth

        if not auth or self.authenticated:
            # Аутентификация не требуется или уже выполнена
            return

        # Параметры аутентификации либо из параметров метода, либо из клиента
        login, password = login or self._login, password or self._password

        if not (login and password):
            raise AuthenticationError("Не указаны параметры входа.")

        _LOGGER.debug("Аутентификация в личном кабинете %r", login)

        # POST-запрос аутентификации
        async with self._post("login", login=login, password=password) as resp:
            # При успешной аутентификации происходит редирект на страницу личного кабинета,
            # иначе - на ту же страницу (URL идентичен)
            if resp.url == resp.history[0].url:
                raise AuthenticationError("Неверные параметры входа.")

            # Аутентификация успешна. Читаем доступные лицевые счета.
            self._update_accounts(await resp.text())

        _LOGGER.debug("Аутентификация в личном кабинете %r выполнена", login)

        # Сохраняем актуальную пару логин-пароль
        self._login, self._password = login, password

    async def close(self, close_connector: bool | None = None) -> None:
        """
        Выход из личного кабинета и закрытие сессии.

        Parameters:
            close_connector: Закрыть сессию и коннектор. Если не указан, параметр берется из клиента.
        """

        if close_connector is None:
            close_connector = self._close_connector

        try:
            if self.authenticated:
                _LOGGER.debug("Выход из личного кабинета %r", self._login)

                async with self._get("logout") as resp:
                    # Выход из аккаунта выполняет редирект на страницу аутентификации
                    # с обновленным CSRF-токеном. Обновляем его.
                    self._update_token(await resp.text())

                self._accounts = None

        finally:
            if close_connector:
                _LOGGER.debug("Закрытие сессии")
                # Если коннектор требуется закрыть, то закрываем и удаляем CSRF-токен.
                await self._session.close()
                self._token = None

    @api(auth_required=True)
    async def get_pdf(
        self,
        account: int | str | None,
        receipt_id: str | None,
    ) -> bytes | None:
        if receipt_id is None:
            return

        account = self._account(account)

        try:
            resp = await self._ajax("getReceipt", account, receiptId=receipt_id)
            filename: str = resp["fileName"]
            path = f"account/{account}/receipts/download"

            async with self._get(path, kvit=filename) as resp:
                _LOGGER.debug(
                    "Загрузка квитанции %r, размер %d байт",
                    filename,
                    resp.content_length,
                )

                return await resp.read()

        except aiohttp.ClientResponseError:
            _LOGGER.debug("Ошибка загрузки квитанции")

    async def get_accrual_erkc_data(
        self,
        accrual: Accrual,
        *,
        max_xy: tuple[int, int] = (3840, 2160),
    ) -> AccrualData | None:
        if pdf := await self.get_pdf(accrual.account, accrual.payment_id):
            return await asyncio.to_thread(erkc_data, pdf, max_xy)

    async def get_accrual_peni_data(
        self,
        accrual: Accrual,
        *,
        max_xy: tuple[int, int] = (3840, 2160),
    ) -> AccrualData | None:
        if pdf := await self.get_pdf(accrual.account, accrual.peni_id):
            return await asyncio.to_thread(peni_data, pdf, max_xy)

    @api(auth_required=True)
    async def year_accruals(
        self,
        year: int | None = None,
        *,
        account: int | str | None = None,
        limit: int | None = None,
        include_details: bool = False,
    ) -> list[Accrual]:
        """Запрос квитанций лицевого счета за год.

        Если год не уточняется - используется текущий.

        Parameters:
            year: год.
            account: номер лицевого счета. Если `None` - будет использоваться
                основной лицевой счет личного кабинета.
            limit: кол-во последних квитанций в ответе. По-умолчанию все квитанции за год.
            include_details: дополнительный запрос детализированных затрат на каждую
                квитанцию в полученном результате. По-умолчанию: `False`.
        """

        account = self._account(account)

        resp: list[list[str]] = await self._ajax(
            func="getReceipts",
            account=account,
            year=year or date_last_accrual().year,
        )

        result = Accrual.from_json(resp, account, limit)

        if include_details:
            await self.update_accruals(result)

        return result

    @api(auth_required=True)
    async def update_accrual(self, accrual: Accruals) -> None:
        """Обновление детализированных данных квитанции или начисления.

        Parameters:
            accrual: квитанция/начисление для обновления.
        """

        json: list[list[str]] = await self._ajax(
            "accrualsDetalization",
            accrual.account,
            month=accrual.date.strftime("01.%m.%y"),
        )

        accrual.details = AccrualDetalization.from_json(json)

    @api(auth_required=True)
    async def update_accruals(self, accruals: Iterable[Accruals]) -> None:
        """Обновление детализированных данных квитанций или начислений.

        Parameters:
            accruals: квитанции/начисления для обновления.
        """

        async with asyncio.TaskGroup() as tg:
            for x in accruals:
                tg.create_task(self.update_accrual(x))

    @api(auth_required=True)
    async def meters_history(
        self,
        *,
        start: dt.date | None = None,
        end: dt.date | None = None,
        account: int | str | None = None,
    ) -> list[MeterHistory]:
        """Запрос счетчиков лицевого счета с историей показаний.

        Если даты не уточняются - результат будет включать все доступные показания.

        Parameters:
            start: дата начала периода.
            end: дата окончания периода (включается в ответ).
            account: номер лицевого счета. Если `None` - будет использоваться основной лицевой счет личного кабинета.
        """

        API_LIMIT = 25  # лимит записей ответа сервера

        start, end = start or _MIN_DATE, end or _MAX_DATE
        assert start <= end

        db: dict[str, list[MeterValue]] = {}

        while True:
            _LOGGER.debug("Запрос истории счетчиков с %r по %r", start, end)

            history = await self._history("counters", account, start, end)

            assert (num := len(history)) <= API_LIMIT, (
                f"Превышен лимит в {API_LIMIT} записей ответа сервера. "
                f"Получено {num}. Возможно изменен API."
            )

            for x in history:
                lst = db.setdefault(x[1], [])
                end = dmy_to_date(ajax_attr(x[2], "sort"))
                lst.append(MeterValue.from_args(end, *x[3:]))

            if num != API_LIMIT:
                return list(map(MeterHistory.from_tuple, db.items()))

    @api(auth_required=True)
    async def accruals_history(
        self,
        *,
        start: dt.date | None = None,
        end: dt.date | None = None,
        account: int | str | None = None,
        limit: int | None = None,
        include_details: bool = False,
    ) -> list[MonthAccrual]:
        """Запрос начислений за заданный период.

        Если даты не уточняются - результат будет включать все доступные показания.

        Parameters:
            start: дата начала периода.
            end: дата окончания периода (включается в ответ).
            account: номер лицевого счета. Если `None` - будет использоваться
                основной лицевой счет личного кабинета.
            limit: кол-во последних квитанций в ответе. По-умолчанию все квитанции за год.
            include_details: дополнительный запрос детализированных затрат на каждое
                начисление в полученном результате. По-умолчанию: `False`.
        """

        account = self._account(account)
        start, end = start or _MIN_DATE, end or _MAX_DATE

        assert start <= end

        history = await self._history("accruals", account, start, end)

        result = MonthAccrual.from_json(history, account, limit)

        if include_details:
            await self.update_accruals(result)

        return result

    @api(auth_required=True)
    async def payments_history(
        self,
        *,
        start: dt.date | None = None,
        end: dt.date | None = None,
        account: int | str | None = None,
    ) -> list[Payment]:
        """Запрос истории платежей за заданный период.

        Если даты не уточняются - результат будет включать все доступные показания.

        Parameters:
            start: дата начала периода.
            end: дата окончания периода (включается в ответ).
            account: номер лицевого счета. Если `None` - будет использоваться
                основной лицевой счет личного кабинета.
        """

        start, end = start or _MIN_DATE, end or _MAX_DATE

        assert start <= end

        history = await self._history("payments", account, start, end)
        result = (Payment.from_args(*x) for x in history)

        # Ответ содержит нулевые платежи (внутренние перерасчеты). Применим фильтр.
        return [x for x in result if x.payment]

    @api(auth_required=True)
    async def account_info(
        self,
        account: int | str | None = None,
    ) -> AccountInfo:
        """Запрос информации о лицевом счете.

        Parameters:
            account: номер лицевого счета. Если `None` - используется основной счет.
        """

        async with self._get(f"account/{self._account(account)}") as x:
            return AccountInfo.from_html(await x.text())

    @api(auth_required=True)
    async def account_add(
        self,
        account: int | str | PublicAccountInfo,
        last_payment: Decimal = Decimal(),
    ) -> None:
        """Привязка лицевого счета к аккаунту личного кабинета.

        Parameters:
            account: номер или публичная информация о лицевом счете
            last_bill_amount: сумма последнего начисления.
                Может быть взята автоматически из публичной информации о счете.
        """

        if isinstance(account, PublicAccountInfo):
            last_payment = last_payment or account.payment
            account = account.account

        assert (account := int(account)) > 0

        if account in self.accounts:
            return

        if last_payment <= 0:
            raise AccountBindingError("Не указана сумма последнего начисления.")

        _LOGGER.debug("Привязка лицевого счета %d", account)

        async with self._post(
            "account/add",
            account=account,
            summ=last_payment,
        ) as x:
            self._update_accounts(await x.text())

        if account not in self.accounts:
            raise AccountBindingError(f"Не удалось привязать лицевой счет {account}.")

    @api(auth_required=True)
    async def account_rm(self, account: int | str) -> None:
        """Отвязка лицевого счета от аккаунта личного кабинета.

        Parameters:
            account: номер лицевого счета.
        """

        assert (account := int(account)) > 0

        if account not in self.accounts:
            _LOGGER.debug("Лицевой счет %d не привязан", account)
            return

        async with self._post(f"account/{account}/remove") as x:
            self._update_accounts(await x.text())

        if account in self.accounts:
            raise AccountBindingError(f"Не удалось отвязать лицевой счет {account}.")

    async def _set_meters_values(
        self,
        path: str,
        values: Mapping[int, Decimal],
    ) -> None:
        if not values:
            return

        async with self._get(path) as x:
            meters = MeterInfo.meters_from_html(await x.text())

        data: dict[str, Any] = {}

        # Если используем без аутентификации - извлечем номер лицевого счета
        # из пути запроса и добавим в данные запроса
        if not path.startswith("account"):
            data["ls"] = int(path.rsplit("/", 1)[-1])

        for id, value in values.items():
            if m := meters.get(id):
                if value > m.value:
                    data[f"counters[{id}_0][value]"] = value
                    data[f"counters[{id}_0][rawId]"] = id
                    data[f"counters[{id}_0][tarif]"] = 0

                    continue

                raise ValueError(
                    f"Новое значение счетчика {id} должно быть выше {m.value}."
                )

            raise ValueError(f"Счетчик {id} не найден.")

        async with self._post(path, **data) as x:
            await x.text()

    @api(auth_required=True)
    async def meters_info(
        self, account: int | str | None = None
    ) -> Mapping[int, MeterInfo]:
        """Запрос информации о приборах учета по лицевому счету.

        Возвращает словарь `идентификатор - информация о приборе учета`.

        Включает следующую информацию:
        - Внутренний идентификатор (для отправки новых показаний)
        - Серийный номер
        - Дата последнего показания
        - Последнее показание
        """

        async with self._get(f"account/{self._account(account)}/counters") as x:
            return MeterInfo.meters_from_html(await x.text())

    @api(auth_required=True)
    async def set_meters_values(
        self,
        values: Mapping[int, Decimal],
        *,
        account: int | str | None = None,
    ) -> None:
        """Передача новых показаний приборов учета.

        Parameters:
            values: словарь `идентификатор прибора - новое показание`.
            account: номер лицевого счета.
        """

        await self._set_meters_values(
            f"account/{self._account(account)}/counters", values
        )

    @api(public=True)
    async def pub_meters_info(self, account: int | str) -> Mapping[int, MeterInfo]:
        """Запрос публичной информации о приборах учета по лицевому счету.

        Возвращает словарь `идентификатор - информация о приборе учета`.

        Включает следующую информацию:
        - Внутренний идентификатор (для отправки новых показаний)
        - Серийный номер
        - Дата последнего показания
        - Последнее показание

        Parameters:
            account: номер лицевого счета.
        """

        assert (account := int(account)) > 0

        async with self._get(f"counters/{account}") as x:
            return MeterInfo.meters_from_html(await x.text())

    @api(public=True)
    async def pub_set_meters_values(
        self,
        account: int | str,
        values: Mapping[int, Decimal],
    ) -> None:
        """Передача новых показаний приборов учета без аутентификации.

        Parameters:
            account: номер лицевого счета.
            values: словарь `идентификатор прибора - новое показание`.
        """

        assert (account := int(account)) > 0

        await self._set_meters_values(f"counters/{account}", values)

    @api(public=True)
    async def pub_account_info(self, account: int | str) -> PublicAccountInfo | None:
        """Запрос открытой информации по лицевому счету.

        Parameters:
            account: номер лицевого счета.
        """

        assert (account := int(account)) > 0

        async with self._get("payment/checkLS", ls=account) as x:
            json: dict[str, Any] = await x.json(loads=JSON_DECODER)

        _LOGGER.debug("JSON ответ: %r", json)

        return PublicAccountInfo.from_json(json, account)

    @api(public=True)
    async def pub_accounts_info(
        self, accounts: Iterable[int | str]
    ) -> Mapping[int, PublicAccountInfo]:
        """Запрос открытой информации по лицевым счетам.

        Parameters:
            accounts: номера лицевых счетов.
        """

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self.pub_account_info(x)) for x in accounts]

        return {x.account: x for task in tasks if (x := task.result())}
