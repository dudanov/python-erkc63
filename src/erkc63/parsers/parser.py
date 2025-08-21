import importlib.util
from typing import List, Tuple, cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer

if importlib.util.find_spec("lxml") is not None:
    HTML_PARSER = "lxml"

else:
    HTML_PARSER = "html.parser"


def _parse_tags(html: str, ss: SoupStrainer) -> List[Tag]:
    soup = BeautifulSoup(html, HTML_PARSER, parse_only=ss)
    return cast(List[Tag], soup.contents)


def parse_html_divclass(html: str, cls_prefix: str) -> List[Tag]:
    """Возвращает список тегов `div`, имеющих класс с указанным префиксом"""

    ss = SoupStrainer(
        name="div",
        class_=lambda x: x is not None
        and any(x.startswith(cls_prefix) for x in x.split()),
    )

    return _parse_tags(html, ss)


def parse_accounts(html: str) -> Tuple[int, ...]:
    """Возвращает список лицевых счетов из HTML страницы."""

    menu = parse_html_divclass(html, "dropdown-menu")[0]
    accounts = cast(List[Tag], menu("a")[:-2])  # нижние 2 ссылки не аккаунты
    accounts = [int(cast(str, x.string)) for x in accounts]

    # сортировка вторичных счетов
    if len(accounts) > 2:
        accounts[1:] = sorted(accounts[1:])

    return tuple(accounts)


def parse_token(html: str) -> str:
    """Извлекает CSRF-токен сессии из страницы"""

    ss = SoupStrainer("meta", {"name": "csrf-token"})
    return str(_parse_tags(html, ss)[0]["content"])
