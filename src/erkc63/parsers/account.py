import dataclasses as dc
from typing import Any, Self

from mashumaro import field_options

from .base import DecimalString, IntNullable, ModelBase, NormalizedString
from .parser import parse_html_divclass


@dc.dataclass(slots=True)
class PublicAccountInfo(ModelBase):
    """Открытая информация о лицевом счете."""

    account: int
    """Номер лицевого счета"""
    address: NormalizedString
    """Адрес"""
    payment: DecimalString = dc.field(
        metadata=field_options(alias="balanceSumma")
    )
    """К оплате"""
    peni: DecimalString = dc.field(metadata=field_options(alias="balancePeni"))
    """Пени"""

    @classmethod
    def from_json(cls, data: dict[str, Any], account: int) -> Self | None:
        """Конструктор из JSON-ответа публичного API."""

        if data["checkLS"]:
            data["account"] = account

            return cls.from_dict(data)


@dc.dataclass(slots=True)
class AccountInfo(ModelBase):
    """Информация о лицевом счете"""

    account: int  # 5
    """Лицевой счет"""
    address: NormalizedString  # 0
    """Адрес жилого помещения"""
    payment: DecimalString  # 14
    """К оплате"""
    debt: DecimalString  # 16
    """Долг на начало периода"""
    accrued: DecimalString  # 18
    """Начислено за период"""
    recalculation: DecimalString  # 20
    """Перерасчет на начало периода"""
    paid: DecimalString  # 22
    """Оплачено"""
    owner: str  # 1
    """Собственник"""
    phone: str  # 2
    """Телефон"""
    email: str  # 3
    """Электронная почта"""
    total_area: DecimalString  # 7
    """Общая площадь жилого помещения"""
    people_registered: IntNullable  # 9
    """Зарегистрировано"""
    people_lives: IntNullable  # 11
    """Проживает"""
    ownership: str  # 13
    """Право собственности"""

    @classmethod
    def from_html(cls, html: str) -> Self:
        """Конструктор из HTML главной страницы лицевого счета."""

        tags = parse_html_divclass(html, "text-col-")
        args = (
            next(tags[x].stripped_strings)
            for x in [5, 0, 14, 16, 18, 20, 22, 1, 2, 3, 7, 9, 11, 13]
        )

        return cls.from_args(*args)
