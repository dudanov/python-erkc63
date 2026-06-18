import dataclasses as dc
import itertools as it
from abc import ABC, abstractmethod
from decimal import Decimal
from functools import cached_property
from operator import attrgetter
from types import MappingProxyType
from typing import Any, Iterable, Iterator, Mapping, Self, override

from ..errors import ErkcError
from .base import DateAjax, DecimalString, ModelBase, ReceiptAjax


@dc.dataclass(slots=True)
class AccrualDetalization(ModelBase):
    """Детализация услуги"""

    name: str
    """Название услуги"""
    tariff: DecimalString
    """Тариф"""
    debt: DecimalString
    """Долг на начало расчетного периода"""
    accrued: DecimalString
    """Начислено за расчетный период"""
    recalculation: DecimalString
    """Перерасчет"""
    quality: DecimalString
    """Снято за качество"""
    paid: DecimalString
    """Оплачено"""
    payment: DecimalString
    """К оплате"""
    consumption: DecimalString
    """Потребление"""

    @classmethod
    def from_json(cls, data: list[list[Any]]) -> Mapping[str, Self]:
        return MappingProxyType({x[0]: cls.from_args(*x) for x in data})


@dc.dataclass
class AccrualBase(ABC, ModelBase):
    account: int
    """Номер лицевого счета"""
    date: DateAjax
    """Дата формирования квитанции"""
    payment: DecimalString
    """Сумма к оплате"""
    details: Mapping[str, AccrualDetalization]
    """Детализация услуг"""

    def _it_details(self) -> Iterable[AccrualDetalization]:
        if self.details:
            return self.details.values()

        raise ErkcError("В квитанции отсутствует детализация по услугам.")

    def _sum_attr(self, attr: str) -> Decimal:
        return sum(map(attrgetter(attr), self._it_details()), Decimal())

    @cached_property
    def tariffs(self) -> Mapping[str, Decimal]:
        """Тарифы по услугам (из детализации)"""

        return MappingProxyType({x.name: x.tariff for x in self._it_details()})

    @cached_property
    def sum_debt(self) -> Decimal:
        """Долг на начало расчетного периода (из детализации)"""

        return self._sum_attr("debt")

    @cached_property
    def sum_accrued(self) -> Decimal:
        """Начислено за расчетный период (из детализации)"""

        return self._sum_attr("accrued")

    @cached_property
    def sum_recalculation(self) -> Decimal:
        """Перерасчет (из детализации)"""

        return self._sum_attr("recalculation")

    @cached_property
    def sum_quality(self) -> Decimal:
        """Снято за качество (из детализации)"""

        return self._sum_attr("quality")

    @cached_property
    def sum_paid(self) -> Decimal:
        """Оплачено (из детализации)"""

        return self._sum_attr("paid")

    @cached_property
    def sum_payment(self) -> Decimal:
        """Сумма к оплате (из детализации)"""

        return self._sum_attr("payment")

    @cached_property
    def is_correct(self) -> bool:
        """Проверка корректности (сверка с детализацией)"""

        if self.sum_payment != self.payment:
            return False

        x1 = self.sum_debt + self.sum_accrued
        x2 = self.sum_paid + self.sum_payment

        return x1 == x2

    @property
    def is_paid(self) -> bool:
        """Оплачен"""

        return self.payment <= 0

    @classmethod
    @abstractmethod
    def _it(
        cls,
        data: list[list[Any]],
        account: int,
    ) -> Iterator[Self]: ...

    @classmethod
    def from_json(
        cls,
        data: list[list[Any]],
        account: int,
        limit: int | None = None,
    ) -> list[Self]:
        return list(it.islice(cls._it(data, account), limit))


@dc.dataclass
class Accrual(AccrualBase):
    """
    Квитанция.

    Объект ответа на запрос `getReceipts`.
    """

    peni: DecimalString
    """Пени к оплате"""
    payment_id: ReceiptAjax | None
    """Идентификатор основной квитанции на оплату"""
    peni_id: ReceiptAjax | None
    """Идентификатор квитанции на оплату пени"""

    @classmethod
    @override
    def _it(cls, data, account) -> Iterator[Self]:
        # группируем результат запроса по дате (поле 0)
        for _, group in it.groupby(data, lambda k: k[0]):
            # основная запись и опциональная запись пени
            x, y = next(group), next(group, None)

            yield cls.from_args(
                account, x[0], x[1], {}, x[2], x[-1], y and y[-1]
            )


@dc.dataclass
class MonthAccrual(AccrualBase):
    """
    Начисление.

    Объект ответа на запрос `accrualsHistory`.
    """

    debt: DecimalString
    """Долг на начало расчетного периода"""
    accrued: DecimalString
    """Начислено"""
    paid: DecimalString
    """Оплачено"""

    @classmethod
    @override
    def _it(cls, data, account) -> Iterator[Self]:
        for x in data:
            accrual = cls.from_args(account, x[0], x[4], {}, x[1], x[2], x[3])

            # запрос поломан. возвращает нулевые начисления в невалидном диапазоне дат.
            # при первом нулевом начислении прерываем цикл, так как далее все начисления тоже нулевые.
            if not accrual.accrued:
                break

            yield accrual


type Accruals = Accrual | MonthAccrual
