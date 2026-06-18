import dataclasses as dc
import itertools as it
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Iterator, Mapping, Self, cast

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
    consumption: Decimal
    """Потребление"""

    @classmethod
    def from_json(cls, data: list[list[Any]]) -> Mapping[str, Self]:
        def _items() -> Iterator[tuple[str, Self]]:
            for args in data:
                details = cls.from_args(*args)

                yield details.name, details

        return MappingProxyType(dict(_items()))


@dc.dataclass(slots=True)
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

    def _sum_attr(self, attr: str) -> Decimal:
        if not self.details:
            raise ErkcError("Отсутствует детализация по услугам.")

        return sum((getattr(x, attr) for x in self.details.values()), Decimal())

    @property
    def details_debt(self) -> Decimal:
        """Долг на начало расчетного периода"""

        return self._sum_attr("debt")

    @property
    def details_accrued(self) -> Decimal:
        """Начислено за расчетный период"""

        return self._sum_attr("accrued")

    @property
    def details_recalculation(self) -> Decimal:
        """Перерасчет"""

        return self._sum_attr("recalculation")

    @property
    def details_quality(self) -> Decimal:
        """Снято за качество"""

        return self._sum_attr("quality")

    @property
    def details_paid(self) -> Decimal:
        """Оплачено"""

        return self._sum_attr("paid")

    @property
    def details_payment(self) -> Decimal:
        """К оплате"""

        return self._sum_attr("payment")

    @property
    def is_correct(self) -> bool:
        """Корректен (сумма счета совпадает с суммой начислений по услугам)"""

        return self.payment == self.details_accrued

    @property
    def is_paid(self) -> bool:
        """Оплачен"""

        return self.details_payment <= 0

    @property
    def tariffs(self):
        """Тарифы по ресурсам"""

        assert self.details
        return {k: v.tariff for k, v in self.details.items()}


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
