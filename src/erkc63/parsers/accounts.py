from typing import Final, cast

from bs4 import Tag

from ..types import AccountInfo
from .parser import parse_html_divclass

_MAP_ACCOUNT_INFO: Final = {
    0: "address",
    1: "person",
    2: "phone",
    3: "email",
    5: "account",
    7: "total_area",
    9: "people_registered",
    11: "people_lives",
    13: "ownership",
    14: "payment",
    16: "debt",
    18: "accrued",
    20: "recalculation",
    22: "paid",
}
"""Словарь соответствия индекса тега и имени поля `AccountInfo`."""


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
            for idx, field in _MAP_ACCOUNT_INFO.items()
        }
    )
