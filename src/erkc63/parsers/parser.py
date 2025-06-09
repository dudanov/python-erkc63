import datetime as dt
from decimal import Decimal
from typing import Any, cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer


def parse_html_divclass(html: str, cls_prefix: str) -> list[Tag]:
    """Возвращает список тегов `div`, имеющих класс с указанным префиксом"""

    x = SoupStrainer(
        name="div",
        class_=lambda x: x is not None
        and any(k.startswith(cls_prefix) for k in x.split()),
    )

    return cast(list[Tag], BeautifulSoup(html, "lxml", parse_only=x).contents)


def ajax_attr(tag: str, attr: str) -> str:
    """Возвращает атрибут данных из тега AJAX-запроса"""

    attr = f' data-{attr}="'
    x2 = tag.index('"', x1 := tag.index(attr) + len(attr))

    return tag[x1:x2]


def ajax_dmy(tag: str) -> dt.date:
    """Возвращает дату из тега AJAX-запроса"""

    d, m, y = map(int, ajax_attr(tag, "sort").split("."))

    return dt.date(2000 + y, m, d)


def ajax_receipt(x: str) -> str:
    """Возвращает из тега AJAX-запроса идентификатор запроса квитанции"""

    return ajax_attr(x, "receipt")


def parse_decimal(x: Any) -> Decimal:
    """Преобразует строку в число"""

    return Decimal(str(x).replace(" ", "").replace(",", "."))
