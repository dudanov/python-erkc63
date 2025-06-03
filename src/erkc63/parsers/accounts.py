from typing import Final, cast

from bs4 import Tag

from ..types import AccountInfo
from .parser import parse_html_divclass

_ACCOUNT_INFO: Final = (
    ("address", 0),
    ("person", 1),
    ("phone", 2),
    ("email", 3),
    ("account", 5),
    ("total_area", 7),
    ("people_registered", 9),
    ("people_lives", 11),
    ("ownership", 13),
    ("payment", 14),
    ("debt", 16),
    ("accrued", 18),
    ("recalculation", 20),
    ("paid", 22),
)
"""Кортеж из пар поле `AccountInfo` - индекс тега на странице."""


def parse_accounts(html: str) -> list[int]:
    """Парсит меню выбора лицевого счета"""

    menu = parse_html_divclass(html, "dropdown-menu")[0]
    accounts = cast(list[Tag], menu("a")[:-2])  # нижние 2 ссылки не аккаунты
    accounts = [int(cast(str, x.string)) for x in accounts]

    # сортировка вторичных счетов
    if len(accounts) > 2:
        accounts[1:] = sorted(accounts[1:])

    return accounts


def parse_account(html: str) -> AccountInfo:
    """Парсит главную страницу лицевого счета со сводной информацией"""

    tags = parse_html_divclass(html, "text-col-")

    return AccountInfo.from_dict(
        {
            field: next(tags[idx].stripped_strings)
            for field, idx in _ACCOUNT_INFO
        }
    )
