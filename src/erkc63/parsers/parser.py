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
