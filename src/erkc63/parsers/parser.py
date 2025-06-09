from typing import cast

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
