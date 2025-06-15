import dataclasses as dc
from decimal import Decimal
from typing import Annotated, Any, Self, cast

from bs4 import Tag
from mashumaro.types import Alias

from .base import Address, JsonDecimal, ModelBase, NullableInt
from .parser import parse_html_divclass


@dc.dataclass(slots=True, kw_only=True)
class PublicAccountInfo(ModelBase):
    """Открытая информация о лицевом счете."""

    account: int
    """Номер лицевого счета"""
    address: Address
    """Адрес"""
    payment: Annotated[JsonDecimal, Alias("balanceSumma")]
    """К оплате"""
    penalty: Annotated[JsonDecimal, Alias("balancePeni")]
    """Пени"""

    @classmethod
    def from_json(cls, json: dict[str, Any], account: int) -> Self | None:
        """Конструктор из JSON-ответа публичного API."""

        if json["checkLS"]:
            json["account"] = account
            return cls.from_dict(json)


@dc.dataclass(slots=True, kw_only=True)
class AccountInfo(ModelBase):
    """Информация о лицевом счете"""

    account: int  # 5
    """Лицевой счет"""
    address: Address  # 0
    """Адрес жилого помещения"""
    payment: Decimal  # 14
    """К оплате"""
    debt: Decimal  # 16
    """Долг на начало периода"""
    accrued: Decimal  # 18
    """Начислено за период"""
    recalculation: Decimal  # 20
    """Перерасчет на начало периода"""
    paid: Decimal  # 22
    """Оплачено"""
    owner: str  # 1
    """Собственник"""
    phone: str  # 2
    """Телефон"""
    email: str  # 3
    """Электронная почта"""
    total_area: Decimal  # 7
    """Общая площадь жилого помещения"""
    people_registered: NullableInt  # 9
    """Зарегистрировано"""
    people_lives: NullableInt  # 11
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


def parse_accounts(html: str) -> tuple[int, ...]:
    """Возвращает список лицевых счетов из HTML страницы."""

    menu = parse_html_divclass(html, "dropdown-menu")[0]
    accounts = cast(list[Tag], menu("a")[:-2])  # нижние 2 ссылки не аккаунты
    accounts = [int(cast(str, x.string)) for x in accounts]

    # сортировка вторичных счетов
    if len(accounts) > 2:
        accounts[1:] = sorted(accounts[1:])

    return tuple(accounts)
