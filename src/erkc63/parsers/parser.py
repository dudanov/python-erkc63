# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025-2026 Sergey Dudanov <sergey.dudanov@gmail.com>

import importlib.util
from typing import Final, cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer

HTML_PARSER: Final = "lxml" if importlib.util.find_spec("lxml") else "html.parser"


def _parse_tags(html: str, ss: SoupStrainer) -> list[Tag]:
    soup = BeautifulSoup(html, HTML_PARSER, parse_only=ss)
    return cast(list[Tag], soup.contents)


def parse_html_divclass(html: str, cls_prefix: str) -> list[Tag]:
    """Возвращает список тегов `div`, имеющих класс с указанным префиксом"""

    ss = SoupStrainer(
        name="div",
        class_=lambda x: (
            x is not None and any(x.startswith(cls_prefix) for x in x.split())
        ),
    )

    return _parse_tags(html, ss)


def parse_accounts(html: str) -> tuple[int, ...]:
    """Возвращает список лицевых счетов из HTML страницы."""

    menu = parse_html_divclass(html, "dropdown-menu")[0]
    accounts = cast(list[Tag], menu("a")[:-2])  # нижние 2 ссылки не аккаунты
    accounts = [int(cast(str, x.string)) for x in accounts]

    # сортировка вторичных счетов
    if len(accounts) > 2:
        accounts[1:] = sorted(accounts[1:])

    return tuple(accounts)


def parse_token(html: str) -> str:
    """Извлекает CSRF-токен сессии из страницы"""

    ss = SoupStrainer("meta", {"name": "csrf-token"})
    return str(_parse_tags(html, ss)[0]["content"])
