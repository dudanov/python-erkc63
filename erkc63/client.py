import asyncio
import dataclasses as dc
import datetime as dt
import itertools as it
import logging
import re
from typing import Any, Coroutine, Iterable, Mapping, Sequence, cast

import aiohttp
import bs4
import yarl

from .account import AccountInfo, PublicAccountInfo
from .accrual import Accrual, AccrualDetalization, Accruals, MonthAccrual
from .bills import QrCodes
from .errors import (
    AccountBindingError,
    AccountNotFound,
    AuthorizationError,
    AuthorizationRequired,
    ParsingError,
    SessionRequired,
)
from .meters import MeterInfoHistory, MeterValue, PublicMeterInfo, get_meters_from_page
from .payment import Payment
from .utils import (
    data_attr,
    date_attr,
    date_last_accrual,
    date_to_str,
    str_normalize,
    str_to_date,
    to_float,
)

_LOGGER = logging.getLogger(__name__)

_MIN_DATE = dt.date(2001, 1, 1)
_MAX_DATE = dt.date(2099, 12, 31)

_BASE_URL = yarl.URL("https://lk.erkc63.ru")


class ErkcClient:
    """
    Клиент ЕРКЦ
    """

    _cli: aiohttp.ClientSession
    """Клиентская сессия"""
    _login: str | None
    """Логин (адрес электронной почты)"""
    _password: str | None
    """Пароль"""
    _token: str | None
    """Токен сессии"""
    _accounts: tuple[int, ...] | None
    """Лицевые счета, привязанные к аккаунту"""

    def __init__(
        self,
        login: str | None = None,
        password: str | None = None,
        *,
        session: aiohttp.ClientSession | None = None,
        **kwargs,
    ) -> None:
        self._cli = session or aiohttp.ClientSession(**kwargs)
        self._cli._base_url = _BASE_URL
        self._login = login
        self._password = password
        self._accounts = None
        self._token = None

    async def __aenter__(self):
        try:
            await self.open()

        except Exception:
            await self.close()
            raise

        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    def _post(self, path: str, **data: Any):
        if self._token is None:
            raise SessionRequired("Запрос требует открытой сессии")

        data["_token"] = self._token
        return self._cli.post(path, data=data)

    def _get(self, path: str, **params: Any):
        return self._cli.get(path, params=params)

    async def _ajax(self, func: str, account: int | None, **params: Any) -> Any:
        async with self._get(f"/ajax/{self._account(account)}/{func}", **params) as x:
            return await x.json()

    def _history(
        self, what: str, account: int | None, start: dt.date, end: dt.date
    ) -> Coroutine[Any, Any, Sequence[Sequence[str]]]:
        params = {"from": date_to_str(start), "to": date_to_str(end)}

        return self._ajax(f"{what}History", account, **params)

    def _update_accounts(self, html: str):
        """Обновляет доступные клиенту лицевые счета"""

        bs, ids = bs4.BeautifulSoup(html, "html.parser"), []
        tag = cast(bs4.Tag, bs.find("div", {"id": "select_ls_dropdown"}))

        for x in tag.find_all("a", {"href": re.compile(r"/\d+$")}):
            ids.append(int(cast(bs4.Tag, x).text.rsplit("/", 1)[-1]))

        _LOGGER.debug(f"Привязанные лицевые счета: {ids}")

        self._accounts = tuple(ids)

    @property
    def opened(self) -> bool:
        """Сессия открыта"""

        return self._token is not None

    @property
    def authorized(self) -> bool:
        """Авторизация в аккаунте выполнена"""

        return self._accounts is not None

    @property
    def accounts(self) -> tuple[int, ...]:
        """Лицевые счета привязанные к аккаунту"""

        if self._accounts is None:
            raise AuthorizationRequired("Требуется авторизация")

        return self._accounts

    @property
    def account(self) -> int:
        """Основной лицевой счет"""

        if x := self.accounts:
            return x[0]

        raise AccountNotFound("Основной лицевой счет не привязан")

    def _account(self, account: int | None) -> int:
        """Если лицевой счет не указан - возвращает основной, иначе выполняет проверку на привязку"""

        if account is None:
            return self.account

        if account in self.accounts:
            return account

        raise AccountNotFound("Лицевой счет %d не привязан", account)

    async def open(self) -> None:
        """Открытие сессии"""

        if self._token:
            _LOGGER.warning("Сессия уже открыта. Токен: %s", self._token)
            return

        _LOGGER.debug("Открытие новой сессии")

        async with self._get("/login") as x:
            html = await x.text()

        bs = bs4.BeautifulSoup(html, "html.parser")
        token = cast(bs4.Tag, bs.find("meta", {"name": "csrf-token"}))
        self._token = cast(str, token["content"])

        _LOGGER.debug("Сессия открыта. Токен: %s", self._token)

        if self._login and self._password:
            await self.login()

    async def login(
        self,
        login: str | None = None,
        password: str | None = None,
    ) -> None:
        """Авторизация в аккаунте"""

        if self.authorized:
            _LOGGER.warning("Клиент уже авторизован в аккаунте %s", self._login)
            return

        login, password = login or self._login, password or self._password

        if not (login and password):
            raise ValueError("Не указаны логин и пароль")

        _LOGGER.debug("Вход в аккаунт %s", login)

        async with self._post("/login", login=login, password=password) as x:
            if x.url == x.history[0].url:
                raise AuthorizationError("Ошибка входа. Проверьте логин и пароль")

            _LOGGER.debug("Вход в аккаунт %s успешно выполнен", login)

            html = await x.text()

        self._update_accounts(html)

        # Сохраняем актуальную пару логин-пароль
        self._login, self._password = login, password

    async def logout(self) -> None:
        """Выход из аккаунта"""

        if self.authorized:
            _LOGGER.debug("Выход из аккаунта %s", self._login)

            async with self._get("/logout"):
                self._accounts = None

    async def close(self) -> None:
        """Выход из аккаунта и закрытие сессии"""

        try:
            if self.authorized:
                await self.logout()

        finally:
            if self._token is not None:
                _LOGGER.debug("Закрытие сессии. Токен: %s", self._token)
                self._token = None

            await self._cli.close()

    async def qr_codes(self, accrual: Accrual) -> QrCodes:
        """Загрузка PDF версии квитанции (основной и пени)"""

        async def _get_pdf(id: str | None) -> bytes | None:
            if id is None:
                return

            try:
                json = await self._ajax("getReceipt", accrual.account, receiptId=id)

            except Exception:
                return

            async with self._get(json["file"]) as x:
                return await x.read()

        return QrCodes(await _get_pdf(accrual.bill_id), await _get_pdf(accrual.peni_id))

    async def year_accruals(
        self,
        year: int | None = None,
        *,
        account: int | None = None,
        limit: int | None = None,
        include_details: bool = False,
    ) -> tuple[Accrual, ...]:
        """Запрос квитанций за год"""

        account = self._account(account)

        resp: Sequence[Sequence[str]] = await self._ajax(
            "getReceipts", account, year=year or date_last_accrual().year
        )

        db: dict[dt.date, Accrual] = {}

        for data in resp:
            date = date_attr(data[0])

            if limit and limit == len(db) and date not in db:
                break

            record = db.setdefault(
                date,
                Accrual(
                    account=account,
                    date=date,
                    summa=to_float(data[1]),
                    peni=to_float(data[2]),
                ),
            )

            id = data_attr(data[5])

            match data[3]:
                case "общая":
                    record.bill_id = id
                case "пени":
                    record.peni_id = id
                case _:
                    raise ParsingError

        result = tuple(db.values())

        if include_details:
            await self.update_accruals(result)

        return result

    async def update_accrual(self, accrual: Accruals) -> None:
        """Обновление детализированных данных квитанции или начисления"""

        resp: list[list[str]] = await self._ajax(
            "accrualsDetalization",
            accrual.account,
            month=accrual.date.strftime("01.%m.%y"),
        )

        accrual.details = {
            str_normalize(x[0]): AccrualDetalization(*map(to_float, x[1:]))
            for x in resp
        }

    def update_accruals(self, accruals: Iterable[Accruals]):
        """Обновление детализированных данных квитанций или начислений"""

        return asyncio.gather(*map(self.update_accrual, accruals))

    async def meters_history(
        self,
        *,
        start: dt.date = _MIN_DATE,
        end: dt.date = _MAX_DATE,
        account: int | None = None,
    ) -> tuple[MeterInfoHistory, ...]:
        """Запрос счетчиков лицевого счета с историей показаний"""

        assert start <= end

        db: dict[tuple[str, str], list[MeterValue]] = {}

        while True:
            history = await self._history("counters", account, start, end)

            # Лимит записей ответа сервера - 25. Контроль превышения на случай изменения API.
            assert (num := len(history)) <= 25

            # Возможен баг: если в один день число записей больше лимита,
            # то сервер не сможет вернуть полный результат ни при каких условиях.
            # Этот случай крайне маловероятен, но условие добавлено.
            last_request = num < 25 or start == end

            for _, key, date, value, consumption, source in history:
                end = str_to_date(date[27:35])

                # игнорируем записи без потребления
                if not (consumption := float(consumption)):
                    continue

                value = MeterValue(end, float(value), consumption, source)

                name, serial = key.split(", счетчик №", 1)
                db.setdefault((name, serial), []).append(value)

            if last_request:
                break

        # Исключаем дублирование записей из наложенных ответов и конвертируем в кортеж
        return tuple(
            MeterInfoHistory(*k, tuple(dict.fromkeys(v))) for k, v in db.items()
        )

    async def accruals_history(
        self,
        *,
        start: dt.date = _MIN_DATE,
        end: dt.date = _MAX_DATE,
        account: int | None = None,
        include_details: bool = False,
    ) -> tuple[MonthAccrual, ...]:
        """Запрос начислений за заданный период"""

        account = self._account(account)

        resp = await self._history("accruals", account, start, end)

        result = []

        for date, *floats in resp:
            floats: Any = map(to_float, floats)
            accrual = MonthAccrual(account, date_attr(date), *floats)

            # запрос поломан. возвращает нулевые начисления в невалидном диапазоне дат.
            # при первом нулевом начислении прерываем цикл, так как далее все начисления тоже нулевые.
            if not accrual.summa:
                break

            result.append(accrual)

        if include_details:
            await self.update_accruals(result)

        return tuple(result)

    async def payments_history(
        self,
        *,
        start: dt.date = _MIN_DATE,
        end: dt.date = _MAX_DATE,
        account: int | None = None,
    ) -> tuple[Payment, ...]:
        """Запрос истории платежей"""

        resp = await self._history("payments", account, start, end)
        result = (Payment(date_attr(x), to_float(y), z) for x, y, z in resp)

        # Ответ содержит нулевые платежи (внутренние перерасчеты). Применим фильтр.
        return tuple(x for x in result if x.summa)

    async def account_info(self, account: int | None = None):
        """Запрос информации о лицевом счете"""

        account = self._account(account)

        async with self._get(f"/account/{account}") as x:
            html = await x.text()

        bs = bs4.BeautifulSoup(html, "html.parser")
        wl = cast(bs4.Tag, bs.find("div", class_="widget-left"))

        ws1 = cast(bs4.Tag, wl.find("div", class_="widget-section1"))
        ws1 = cast(bs4.Tag, ws1.find_all("div", class_="text-col-left"))

        ws2 = cast(bs4.Tag, wl.find("div", class_="widget-section2"))
        ws2 = cast(list[bs4.Tag], ws2.find_all("div", class_="text-col-right"))

        ws = (str_normalize(x.text) for x in it.chain(ws1, ws2))

        def _cnv(k, v):
            return k.type(v) if v != "-" else 0

        data: Any = (_cnv(*x) for x in zip(dc.fields(AccountInfo), ws))

        return AccountInfo(*data)

    async def account_add(
        self,
        account: int | PublicAccountInfo,
        last_bill_amount: float = 0,
    ) -> None:
        """
        Привязка лицевого счета к аккаунту личного кабинета.

        Параметры:
        - `account`: номер или публичная информация о лицевом счете
        - `last_bill_amount`: сумма последнего начисления.
        Может быть взята автоматически из публичной информации о счете.
        """

        if isinstance(account, PublicAccountInfo):
            last_bill_amount = last_bill_amount or account.balance
            account = account.account

        if account in self.accounts:
            _LOGGER.info("Лицевой счет %d уже привязан к аккаунту", account)
            return

        if last_bill_amount <= 0:
            raise ValueError("Сумма последнего начисления не указана")

        _LOGGER.debug("Привязка лицевого счета %d", account)

        async with self._post(
            "/account/add", account=account, summ=last_bill_amount
        ) as x:
            html = await x.text()

        self._update_accounts(html)

        if account not in self.accounts:
            raise AccountBindingError("Не удалось привязать лицевой счет %d", account)

    async def account_rm(self, account: int) -> None:
        """Отвязка лицевого счета от лицевого счета"""

        if account not in self.accounts:
            _LOGGER.info("Лицевой счет %d не привязан к аккаунту", account)
            return

        async with self._post(f"/account/{account}/remove") as x:
            html = await x.text()

        self._update_accounts(html)

        if account in self.accounts:
            raise AccountBindingError("Не удалось отвязать лицевой счет %d", account)

    async def _set_meters_values(
        self,
        path: str,
        values: Mapping[int, float],
    ) -> None:
        if not values:
            return

        async with self._get(path) as x:
            html = await x.text()

        data: dict[str, Any] = {}
        meters = get_meters_from_page(html)

        # Если используем без авторизации - извлечем номер лицевого счета
        # из пути запроса и добавим в данные запроса
        if not path.startswith("/account"):
            data["ls"] = int(path.rsplit("/", 1)[-1])

        for id, value in values.items():
            if m := meters.get(id):
                if value > m.value:
                    data[f"counters[{id}_0][value]"] = value
                    data[f"counters[{id}_0][rawId]"] = id
                    data[f"counters[{id}_0][tarif]"] = 0

                    continue

                raise ValueError(
                    f"Новое значение счетчика {id} должно быть выше текущего {m.value}"
                )

            raise ValueError(f"Счетчик {id} не найден")

        async with self._post(path, **data):
            pass

    async def meters_info(
        self, account: int | None = None
    ) -> Mapping[int, PublicMeterInfo]:
        """
        Запрос информации о приборах учета лицевого счета.

        Возвращает словарь `ресурс - информация о приборе учета`.

        Включает следующую информацию:
        - Внутренний идентификатор (для отправки новых показаний)
        - Серийный номер
        - Дата последнего показания
        - Последнее показание
        """

        async with self._get(f"/account/{self._account(account)}/counters") as x:
            html = await x.text()

        return get_meters_from_page(html)

    def _public_api(self):
        if self.authorized:
            raise ValueError("Публичный API функционирует без авторизации")

    async def pub_meters_info(self, account: int) -> Mapping[int, PublicMeterInfo]:
        """
        Запрос публичной информации о приборах учета по лицевому счету.

        Возвращает словарь `ресурс - информация о приборе учета`.

        Включает следующую информацию:
        - Внутренний идентификатор (для отправки новых показаний)
        - Серийный номер
        - Дата последнего показания
        - Последнее показание
        """

        self._public_api()

        async with self._get(f"/counters/{account}") as x:
            html = await x.text()

        return get_meters_from_page(html)

    async def pub_set_meters_values(
        self,
        account: int,
        values: Mapping[int, float],
    ):
        """Отправка без авторизации новых показаний приборов учета"""

        self._public_api()

        await self._set_meters_values(f"/counters/{account}", values)

    async def pub_account_info(self, account: int) -> PublicAccountInfo | None:
        """Запрос открытой информации по лицевому счету"""

        self._public_api()

        async with self._get("/payment/checkLS", ls=account) as x:
            json: Mapping[str, Any] = await x.json()

        if json["checkLS"]:
            return PublicAccountInfo(
                account,
                str_normalize(json["address"]),
                to_float(json["balanceSumma"]),
                to_float(json["balancePeni"]),
            )

        _LOGGER.info("Лицевой счет %d не найден", account)

    async def pub_accounts_info(
        self, *accounts: int
    ) -> Mapping[int, PublicAccountInfo]:
        """Запрос открытой информацию по лицевым счетам"""

        self._public_api()

        result = await asyncio.gather(*map(self.pub_account_info, accounts))

        return {x.account: x for x in result if x}
