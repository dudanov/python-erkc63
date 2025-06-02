import dataclasses as dc
from decimal import Decimal
from typing import Any, Iterator, cast

from bs4 import Tag

from ..types import AccountInfo
from ..utils import str_normalize
from .parser import parse_html_divclass

_POS_TYPES = tuple(
    (pos, str(field.type))
    for pos, field in zip(
        [0, 1, 2, 3, 5, 7, 9, 11, 13, 14, 16, 18, 20, 22],  # позиции тегов
        dc.fields(AccountInfo),  # поля
        strict=True,
    )
)


def parse_accounts(html: str) -> list[int]:
    """Парсит меню выбора лицевого счета"""

    menu = cast(Tag, parse_html_divclass(html, "dropdown-menu")[0])
    accounts = cast(list[Tag], menu("a")[:-2])  # нижние 2 ссылки не аккаунты
    accounts = [int(cast(str, x.string)) for x in accounts]

    # сортировка вторичных счетов
    if len(accounts) > 2:
        accounts[1:] = sorted(accounts[1:])

    return accounts


def parse_account(html: str) -> AccountInfo:
    """Парсит главную страницу лицевого счета со сводной информацией"""

    tags = parse_html_divclass(html, "text-col-")

    def _args() -> Iterator[Any]:
        for pos, _type in _POS_TYPES:
            string = next(tags[pos].stripped_strings)

            match _type:
                case "str":
                    yield str_normalize(string)

                case "int":
                    yield int(string) if string != "-" else 0

                case "Decimal":
                    yield Decimal(string.replace(" ", ""))

                case _ as x:
                    raise TypeError(f"Неизвестный тип: '{x}'.")

    return AccountInfo(*_args())
