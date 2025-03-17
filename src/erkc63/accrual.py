import dataclasses as dc
import datetime as dt
from decimal import Decimal
from typing import Mapping, cast

from .errors import ErkcError


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


Accruals = Accrual | MonthAccrual
