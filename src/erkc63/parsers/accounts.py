import dataclasses as dc
from decimal import Decimal
from typing import Any, Iterator, cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer

from ..types import AccountInfo
from ..utils import str_normalize

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

    x = SoupStrainer("div", id="select_ls_dropdown")
    x = BeautifulSoup(html, "lxml", parse_only=x)

    menu = cast(Tag, x.contents[0])
    accounts = cast(list[Tag], menu("a")[:-2])  # нижние 2 ссылки не аккаунты
    accounts = [int(cast(str, x.string)) for x in accounts]

    # сортировка вторичных счетов
    if len(accounts) > 2:
        accounts[1:] = sorted(accounts[1:])

    return accounts


def parse_account(html: str) -> AccountInfo:
    """Парсит главную страницу лицевого счета со сводной информацией"""

    x = SoupStrainer(
        name="div",
        class_=lambda k: k is not None and k.find("text-col-") != -1,
    )

    tags = BeautifulSoup(html, "lxml", parse_only=x).contents

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
