import datetime as dt
from typing import cast

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
    x1 = x.find(attr) + len(attr)
    x2 = x.find('"', x1)
    return x[x1:x2]


def parse_dmy(x: str) -> dt.date:
    d, m, y = map(int, parse_attr(x, "sort").split("."))
    return dt.date(y + 2000, m, d)


def parse_receipt(x: str) -> str:
    return parse_attr(x, "receipt")
