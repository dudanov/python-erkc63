import dataclasses as dc
from decimal import Decimal
from typing import Any, Self, cast

from bs4 import Tag
from mashumaro.config import BaseConfig
from mashumaro.mixins.dict import DataClassDictMixin

from .parser import parse_html_divclass
from .utils import parse_decimal, str_normalize


def parse_int(x: str) -> int:
    return int(x) if x.isdecimal() else 0


@dc.dataclass(slots=True, kw_only=True)
class PublicAccountInfo(DataClassDictMixin):
    """Открытая информация о лицевом счете."""

    account: int
    """Номер лицевого счета"""
    address: str
    """Адрес"""
    payment: Decimal
    """К оплате"""
    penalty: Decimal
    """Пени"""

    class Config(BaseConfig):
        lazy_compilation = True
        aliases = {
            "payment": "balanceSumma",
            "penalty": "balancePeni",
        }
        serialization_strategy = {
            str: {"deserialize": str_normalize},
            Decimal: {"deserialize": parse_decimal},
        }

    @classmethod
    def from_json(cls, json: dict[str, Any], account: int) -> Self | None:
        """Конструктор из JSON-ответа публичного API."""

        if json["checkLS"]:
            json["account"] = account
            return cls.from_dict(json)


@dc.dataclass(slots=True, kw_only=True)
class AccountInfo(DataClassDictMixin):
    """Информация о лицевом счете"""

    account: int = dc.field(metadata={"tag": 5})
    """Лицевой счет"""
    address: str = dc.field(metadata={"tag": 0})
    """Адрес жилого помещения"""
    payment: Decimal = dc.field(metadata={"tag": 14})
    """К оплате"""
    debt: Decimal = dc.field(metadata={"tag": 16})
    """Долг на начало периода"""
    accrued: Decimal = dc.field(metadata={"tag": 18})
    """Начислено за период"""
    recalculation: Decimal = dc.field(metadata={"tag": 20})
    """Перерасчет на начало периода"""
    paid: Decimal = dc.field(metadata={"tag": 22})
    """Оплачено"""
    owner: str = dc.field(metadata={"tag": 1})
    """Собственник"""
    phone: str = dc.field(metadata={"tag": 2})
    """Телефон"""
    email: str = dc.field(metadata={"tag": 3})
    """Электронная почта"""
    total_area: Decimal = dc.field(metadata={"tag": 7})
    """Общая площадь жилого помещения"""
    people_registered: int = dc.field(metadata={"tag": 9})
    """Зарегистрировано"""
    people_lives: int = dc.field(metadata={"tag": 11})
    """Проживает"""
    ownership: str = dc.field(metadata={"tag": 13})
    """Право собственности"""

    class Config(BaseConfig):
        lazy_compilation = True
        serialization_strategy = {
            str: {"deserialize": str_normalize},
            Decimal: {"deserialize": parse_decimal},
            int: {"deserialize": parse_int},
        }

    @classmethod
    def from_html(cls, html: str) -> Self:
        """Конструктор из HTML главной страницы лицевого счета."""

        tags = parse_html_divclass(html, "text-col-")

        return cls.from_dict(
            {
                x.name: next(tags[x.metadata["tag"]].stripped_strings)
                for x in dc.fields(cls)
            }
        )


def parse_accounts(html: str) -> tuple[int, ...]:
    """Возвращает список лицевых счетов из HTML страницы."""

    menu = parse_html_divclass(html, "dropdown-menu")[0]
    accounts = cast(list[Tag], menu("a")[:-2])  # нижние 2 ссылки не аккаунты
    accounts = [int(cast(str, x.string)) for x in accounts]

    # сортировка вторичных счетов
    if len(accounts) > 2:
        accounts[1:] = sorted(accounts[1:])

    return tuple(accounts)
