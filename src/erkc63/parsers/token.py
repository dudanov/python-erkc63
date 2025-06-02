from typing import cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer


def parse_token(html: str) -> str:
    """Извлекает CSRF-токен сессии из страницы"""

    x = SoupStrainer("meta", {"name": "csrf-token"})
    tags = BeautifulSoup(html, "lxml", parse_only=x).contents

    return str(cast(Tag, tags[0])["content"])
