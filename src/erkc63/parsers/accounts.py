import dataclasses as dc
from typing import cast

from bs4 import Tag

from ..types import AccountInfo
from .parser import parse_html_divclass


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
            field.name: next(tags[idx].stripped_strings)
            for field, idx in zip(
                dc.fields(AccountInfo),
                (0, 1, 2, 3, 5, 7, 9, 11, 13, 14, 16, 18, 20, 22),
                strict=True,
            )
        }
    )
