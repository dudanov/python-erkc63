import dataclasses as dc
import itertools as it
from decimal import Decimal
from functools import cached_property
from types import MappingProxyType
from typing import Any, Iterable, Iterator, Mapping, Self

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
class Accrual(ModelBase):
    """
    Квитанция.

    Объект ответа на запрос `getReceipts`.
    """

    account: int
    """Лицевой счет"""
    date: DateAjax
    """Дата формирования"""
    payment: DecimalString
    """Сумма"""
    peni: DecimalString
    """Пени"""
    payment_id: ReceiptAjax | None
    """Идентификатор квитанции для скачивания"""
    peni_id: ReceiptAjax | None
    """Идентификатор квитанции на пени для скачивания"""
    details: Mapping[str, AccrualDetalization] = dc.field(default_factory=dict)
    """Детализация услуг"""

    @classmethod
    def from_json(
        cls,
        data: list[list[Any]],
        account: int,
        limit: int | None = None,
    ) -> list[Self]:
        def _items() -> Iterator[Self]:
            # группируем результат запроса по дате (поле 0)
            for _, group in it.groupby(data, lambda k: k[0]):
                # основная запись и опциональная запись пени
                x, y = next(group), next(group, None)

                yield cls.from_args(account, *x[:3], x[-1], y and y[-1])

        return list(it.islice(_items(), limit))

    def _it_details(self) -> Iterable[AccrualDetalization]:
        if self.details:
            return self.details.values()

        raise ErkcError("В квитанции отсутствует детализация по услугам.")

    def _sum_attr(self, attr: str) -> Decimal:
        return sum((getattr(x, attr) for x in self._it_details()), Decimal())

    @cached_property
    def tariffs(self) -> Mapping[str, Decimal]:
        """Тарифы по ресурсам"""

        result = {x.name: x.tariff for x in self._it_details()}

        return MappingProxyType(result)

    @cached_property
    def details_debt(self) -> Decimal:
        """Долг на начало расчетного периода"""

        return self._sum_attr("debt")

    @cached_property
    def details_accrued(self) -> Decimal:
        """Начислено за расчетный период"""

        return self._sum_attr("accrued")

    @cached_property
    def details_recalculation(self) -> Decimal:
        """Перерасчет"""

        return self._sum_attr("recalculation")

    @cached_property
    def details_quality(self) -> Decimal:
        """Снято за качество"""

        return self._sum_attr("quality")

    @cached_property
    def details_paid(self) -> Decimal:
        """Оплачено"""

        return self._sum_attr("paid")

    @cached_property
    def details_payment(self) -> Decimal:
        """К оплате"""

        return self._sum_attr("payment")

    @cached_property
    def is_correct(self) -> bool:
        """Корректен (сумма счета совпадает с суммой начислений по услугам)"""

        x1 = self.details_debt + self.details_accrued  # "долг" + "начислено"
        x2 = self.details_paid + self.details_payment  # "оплачено" + "к оплате"

        return x1 == x2

    @cached_property
    def is_paid(self) -> bool:
        """Оплачен"""

        return self.details_payment <= 0


@dc.dataclass(slots=True)
class MonthAccrual(ModelBase):
    """
    Начисление.

    Объект ответа на запрос `accrualsHistory`.
    """

    account: int
    """Лицевой счет"""
    date: DateAjax
    """Дата"""
    debt: DecimalString
    """Долг на начало расчетного периода"""
    accrued: DecimalString
    """Начислено"""
    paid: DecimalString
    """Оплачено"""
    payment: DecimalString
    """К оплате"""
    details: Mapping[str, AccrualDetalization] = dc.field(default_factory=dict)
    """Детализация услуг"""

    @classmethod
    def from_json(
        cls,
        json: list[list[Any]],
        account: int,
        limit: int | None = None,
    ) -> list[Self]:
        def _items() -> Iterator[Self]:
            for args in json:
                accrual = cls.from_args(account, *args)

                # запрос поломан. возвращает нулевые начисления в невалидном диапазоне дат.
                # при первом нулевом начислении прерываем цикл, так как далее все начисления тоже нулевые.
                if not accrual.accrued:
                    break

                yield accrual

        return list(it.islice(_items(), limit))


Accruals = Accrual | MonthAccrual
