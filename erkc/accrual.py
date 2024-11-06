import dataclasses as dc
import datetime as dt
from typing import Mapping

from .errors import ErkcError


@dc.dataclass(frozen=True)
class AccrualDetalization:
    """Детализация услуги"""

    tariff: float
    """Тариф"""
    saldo_in: float
    """Входящее сальдо (долг на начало расчетного периода)"""
    billed: float
    """Начислено"""
    reee: float
    """Перерасчет"""
    quality: float
    """Снято за качество"""
    payment: float
    """Платеж"""
    saldo_out: float
    """Исходящее сальдо (долг на конец расчетного периода)"""
    volume: float
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
    summa: float
    """Сумма"""
    peni: float
    """Пени"""
    bill_id: str | None = None
    """Идентификатор квитанции для скачивания"""
    peni_id: str | None = None
    """Идентификатор квитанции на пени для скачивания"""
    details: Mapping[str, AccrualDetalization] | None = None
    """Детализация услуг"""

    def _sum(self, attr: str) -> float:
        if self.details:
            return sum(getattr(x, attr) for x in self.details.values())

        raise ErkcError("Отсутствует детализация по услугам")

    @property
    def saldo_in(self) -> float:
        """Входящее сальдо (долг на начало расчетного периода)"""
        return self._sum("saldo_in")

    @property
    def billed(self) -> float:
        """Начислено"""
        return self._sum("billed")

    @property
    def reee(self) -> float:
        """Перерасчет"""
        return self._sum("reee")

    @property
    def quality(self) -> float:
        """Снято за качество"""
        return self._sum("quality")

    @property
    def payment(self) -> float:
        """Платеж"""
        return self._sum("payment")

    @property
    def saldo_out(self) -> float:
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
    saldo_in: float
    """Входящее сальдо (долг на начало расчетного периода)"""
    summa: float
    """Начислено"""
    payment: float
    """Платеж"""
    saldo_out: float
    """Исходящее сальдо (долг на конец расчетного периода)"""
    details: Mapping[str, AccrualDetalization] | None = None
    """Детализация услуг"""


Accruals = Accrual | MonthAccrual
