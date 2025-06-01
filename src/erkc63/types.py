from __future__ import annotations

import dataclasses as dc
import datetime as dt
from decimal import Decimal
from typing import Mapping, cast

from .errors import ErkcError

type Accruals = Accrual | MonthAccrual


@dc.dataclass(frozen=True, slots=True)
class Payment:
    """
    Платеж.

    Объект ответа на запрос `paymentsHistory`.
    """

    date: dt.date
    """Дата"""
    summa: Decimal
    """Сумма"""
    provider: str
    """Платежный провайдер"""


@dc.dataclass
class PublicAccountInfo:
    """Открытая информация о лицевом счете."""

    account: int
    """Номер лицевого счета"""
    address: str
    """Адрес"""
    balance: Decimal
    """Задолженность"""
    peni: Decimal
    """Пени"""

    def __repr__(self) -> str:
        return (
            f"Лицевой счет:  {self.account}\n"
            f"Адрес:         {self.address}\n"
            f"Задолженность: {self.balance}\n"
            f"Пени:          {self.peni}\n"
        )


@dc.dataclass
class AccountInfo:
    """Информация о лицевом счете"""

    address: str
    """Адрес"""
    person: str
    """Собственник"""
    phone: str
    """Телефон"""
    email: str
    """Электронная почта"""
    account: int
    """Лицевой счет"""
    square: Decimal
    """Общая площадь"""
    registered: int
    """Зарегистрировано"""
    hosted: int
    """Проживает"""
    document: str
    """Право собственности"""
    k_oplate: Decimal
    """К оплате"""
    dolg: Decimal
    """Долг на начало периода"""
    nachisleno: Decimal
    """Начислено за период"""
    pereraschet: Decimal
    """Перерасчет на начало периода"""
    oplacheno: Decimal
    """Оплачено"""


@dc.dataclass(frozen=True)
class MeterInfo:
    name: str
    """Ресурс учета"""
    serial: str
    """Серийный номер"""

    def __eq__(self, other: MeterInfo) -> bool:
        return self.name == other.name and self.serial == other.serial


@dc.dataclass(frozen=True, eq=False)
class PublicMeterInfo(MeterInfo):
    """
    Информация о приборе учета.

    Результат парсинга HTML-страницы.
    """

    date: dt.date
    """Дата последнего показания"""
    value: Decimal
    """Последнее показание"""


@dc.dataclass(frozen=True)
class MeterValue:
    """Показание счетчика"""

    date: dt.date
    """Дата"""
    value: Decimal
    """Значение"""
    consumption: Decimal
    """Расход"""
    source: str
    """Источник"""


@dc.dataclass(frozen=True, eq=False)
class MeterInfoHistory(MeterInfo):
    """Счетчик с архивом показаний"""

    history: list[MeterValue]
    """Архив показаний"""


@dc.dataclass(frozen=True)
class AccrualDetalization:
    """Детализация услуги"""

    tariff: Decimal
    """Тариф"""
    saldo_in: Decimal
    """Входящее сальдо (долг на начало расчетного периода)"""
    billed: Decimal
    """Начислено"""
    reee: Decimal
    """Перерасчет"""
    quality: Decimal
    """Снято за качество"""
    payment: Decimal
    """Платеж"""
    saldo_out: Decimal
    """Исходящее сальдо (долг на конец расчетного периода)"""
    volume: Decimal
    """Объем"""


@dc.dataclass
class Accrual:
    """
    Квитанция.

    Объект ответа на запрос `getReceipts`.
    """

    account: int
    """Лицевой счет"""
    date: dt.date
    """Дата формирования"""
    summa: Decimal
    """Сумма"""
    peni: Decimal
    """Пени"""
    bill_id: str | None = None
    """Идентификатор квитанции для скачивания"""
    peni_id: str | None = None
    """Идентификатор квитанции на пени для скачивания"""
    details: Mapping[str, AccrualDetalization] | None = None
    """Детализация услуг"""

    def _sum(self, attr: str) -> Decimal:
        if self.details:
            x = sum(getattr(x, attr) for x in self.details.values())
            return cast(Decimal, x)

        raise ErkcError("Отсутствует детализация по услугам")

    @property
    def saldo_in(self) -> Decimal:
        """Входящее сальдо (долг на начало расчетного периода)"""
        return self._sum("saldo_in")

    @property
    def billed(self) -> Decimal:
        """Начислено"""
        return self._sum("billed")

    @property
    def reee(self) -> Decimal:
        """Перерасчет"""
        return self._sum("reee")

    @property
    def quality(self) -> Decimal:
        """Снято за качество"""
        return self._sum("quality")

    @property
    def payment(self) -> Decimal:
        """Платеж"""
        return self._sum("payment")

    @property
    def saldo_out(self) -> Decimal:
        """Исходящее сальдо (долг на конец расчетного периода)"""
        return self._sum("saldo_out")

    @property
    def is_correct(self) -> bool:
        """Корректен (сумма счета совпадает с суммой начислений по услугам)"""
        return self.summa == self.billed

    @property
    def is_paid(self) -> bool:
        """Оплачен"""
        return not self.saldo_out

    @property
    def tariffs(self):
        assert self.details
        return {k: v.tariff for k, v in self.details.items()}


@dc.dataclass
class MonthAccrual:
    """
    Начисление.

    Объект ответа на запрос `accrualsHistory`.
    """

    account: int
    """Лицевой счет"""
    date: dt.date
    """Дата"""
    saldo_in: Decimal
    """Входящее сальдо (долг на начало расчетного периода)"""
    summa: Decimal
    """Начислено"""
    payment: Decimal
    """Платеж"""
    saldo_out: Decimal
    """Исходящее сальдо (долг на конец расчетного периода)"""
    details: Mapping[str, AccrualDetalization] | None = None
    """Детализация услуг"""
