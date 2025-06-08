import datetime as dt
from decimal import Decimal
from typing import Any, cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer


def parse_html_divclass(html: str, cls: str) -> list[Tag]:
    """Возвращает список тегов `div` указанного класса"""

    x = SoupStrainer(
        name="div",
        class_=lambda x: x is not None and x.find(cls) != -1,
    )

    return cast(list[Tag], BeautifulSoup(html, "lxml", parse_only=x).contents)


def parse_attr(x: str, attr: str) -> str:
    attr = f' data-{attr}="'
    x1 = x.index(attr) + len(attr)
    x2 = x.index('"', x1)

    return x[x1:x2]


def parse_dmy(x: str) -> dt.date:
    x = parse_attr(x, "sort")
    d, m, y = map(int, x.split("."))

    return dt.date(y + 2000, m, d)


def parse_receipt(x: str) -> str:
    return parse_attr(x, "receipt")


def parse_decimal(x: Any) -> Decimal:
    """Преобразует строку в число."""

    return Decimal(str(x).replace(" ", "").replace(",", "."))
