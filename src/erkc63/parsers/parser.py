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


def parse_accounts(html: str) -> tuple[int, ...]:
    """Возвращает список лицевых счетов из HTML страницы."""

    (menu,) = parse_html_divclass(html, "dropdown-menu")
    accounts = cast(list[Tag], menu("a")[:-2])  # нижние 2 ссылки не аккаунты
    accounts = [int(cast(str, x.string)) for x in accounts]

    # сортировка вторичных счетов
    if len(accounts) > 2:
        accounts[1:] = sorted(accounts[1:])

    return tuple(accounts)


def parse_token(html: str) -> str:
    """Извлекает CSRF-токен сессии из страницы"""

    x = SoupStrainer("meta", {"name": "csrf-token"})
    tags = BeautifulSoup(html, "lxml", parse_only=x).contents

    return str(cast(Tag, tags[0])["content"])
