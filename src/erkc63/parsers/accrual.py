import dataclasses as dc
import itertools as it
from decimal import Decimal
from typing import Any, Iterator, Mapping, Self, cast

from ..errors import ErkcError
from .base import AjaxDate, AjaxReceipt, ModelBase


@dc.dataclass(slots=True, kw_only=True)
class AccrualDetalization(ModelBase):
    """Детализация услуги"""

    name: str
    """Название услуги"""
    tariff: Decimal
    """Тариф"""
    debt: Decimal
    """Долг на начало расчетного периода"""
    accrued: Decimal
    """Начислено за расчетный период"""
    recalculation: Decimal
    """Перерасчет"""
    quality: Decimal
    """Снято за качество"""
    paid: Decimal
    """Оплачено"""
    payment: Decimal
    """К оплате"""
    consumption: Decimal
    """Потреблено"""

    @classmethod
    def from_json(cls, json: list[list[Any]]) -> Mapping[str, Self]:
        def _gen() -> Iterator[tuple[str, Self]]:
            for args in json:
                details = cls.from_args(args)

                yield details.name, details

        return dict(_gen())


@dc.dataclass(slots=True, kw_only=True)
class Accrual(ModelBase):
    """
    Квитанция.

    Объект ответа на запрос `getReceipts`.
    """

    account: int
    """Лицевой счет"""
    date: AjaxDate
    """Дата формирования"""
    payment: Decimal
    """Сумма"""
    penalty: Decimal
    """Пени"""
    payment_id: AjaxReceipt | None = None
    """Идентификатор квитанции для скачивания"""
    penalty_id: AjaxReceipt | None = None
    """Идентификатор квитанции на пени для скачивания"""
    details: Mapping[str, AccrualDetalization] = dc.field(default_factory=dict)
    """Детализация услуг"""

    @classmethod
    def from_json(
        cls,
        json: list[list[Any]],
        account: int,
        limit: int | None = None,
    ) -> list[Self]:
        def _gen() -> Iterator[Self]:
            # группируем результат запроса по дате (поле 0)
            for _, group in it.groupby(json, lambda k: k[0]):
                # основная запись
                args: list[Any] = next(group)
                args = [account, *args[:3], args[-1]]

                # если есть запись пени - добавим в конец списка аргументов
                if x := next(group, None):
                    args.append(x[-1])

                yield cls.from_args(args)

        return list(it.islice(_gen(), limit))

    def _sum(self, attr: str) -> Decimal:
        if not self.details:
            raise ErkcError("Отсутствует детализация по услугам.")

        x = sum(getattr(x, attr) for x in self.details.values())
        return cast(Decimal, x)

    @property
    def details_debt(self) -> Decimal:
        """Долг на начало расчетного периода"""

        return self._sum("debt")

    @property
    def details_accrued(self) -> Decimal:
        """Начислено за расчетный период"""

        return self._sum("accrued")

    @property
    def details_recalculation(self) -> Decimal:
        """Перерасчет"""

        return self._sum("recalculation")

    @property
    def details_quality(self) -> Decimal:
        """Снято за качество"""

        return self._sum("quality")

    @property
    def details_paid(self) -> Decimal:
        """Оплачено"""

        return self._sum("paid")

    @property
    def details_payment(self) -> Decimal:
        """К оплате"""

        return self._sum("payment")

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


@dc.dataclass(slots=True, kw_only=True)
class MonthAccrual(ModelBase):
    """
    Начисление.

    Объект ответа на запрос `accrualsHistory`.
    """

    account: int
    """Лицевой счет"""
    date: AjaxDate
    """Дата"""
    debt: Decimal
    """Долг на начало расчетного периода"""
    accrued: Decimal
    """Начислено"""
    paid: Decimal
    """Оплачено"""
    payment: Decimal
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
        def _gen() -> Iterator[Self]:
            for args in json:
                args.insert(0, account)
                accrual = cls.from_args(args)

                # запрос поломан. возвращает нулевые начисления в невалидном диапазоне дат.
                # при первом нулевом начислении прерываем цикл, так как далее все начисления тоже нулевые.
                if not accrual.accrued:
                    break

                yield accrual

        return list(it.islice(_gen(), limit))


type Accruals = Accrual | MonthAccrual
