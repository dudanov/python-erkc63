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


def parse_dmy(x: str) -> dt.date:
    """Возвращает дату из строки вида `dd.mm.yy`"""

    d, m, y = map(int, x.split("."))

    return dt.date(2000 + y, m, d)


def ajax_attr(tag: str, attr: str) -> str:
    """Возвращает атрибут данных из тега AJAX-запроса"""

    attr = f' data-{attr}="'
    end = tag.index('"', start := tag.index(attr) + len(attr))

    return tag[start:end]


def ajax_dmy(tag: str) -> dt.date:
    """Возвращает дату из атрибута тега AJAX-запроса вида `dd.mm.yy`"""

    return parse_dmy(ajax_attr(tag, "sort"))


def ajax_receipt(tag: str) -> str:
    """Возвращает из тега AJAX-запроса идентификатор запроса квитанции"""

    return ajax_attr(tag, "receipt")


def parse_decimal(x: Any) -> Decimal:
    """Преобразует строку в число"""

    return Decimal(str(x).replace(" ", "").replace(",", "."))
