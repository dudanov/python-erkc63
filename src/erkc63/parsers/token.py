from typing import cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer


def parse_token(html: str) -> str:
    """Извлекает CSRF-токен сессии из страницы"""

    x = SoupStrainer("meta", {"name": "csrf-token"})
    x = BeautifulSoup(html, "lxml", parse_only=x)

    return str(cast(Tag, x.contents[0])["content"])
