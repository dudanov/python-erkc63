import re
from decimal import Decimal
from typing import Mapping, cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer

from ..types import PublicMeterInfo
from ..utils import str_to_date

_RE_RAWID = re.compile(r"rowId")


def parse_meters(html: str) -> Mapping[int, PublicMeterInfo]:
    """
    Парсит HTML страницу с информацией по приборам учета.

    Возвращает словарь `идентификатор - информация о приборе учета`.
    """

    result: dict[int, PublicMeterInfo] = {}

    # Из-за особенности реализации парсинга в BeautifulSoup с использованием
    # фильтра SoupStrainer он не позволяет типичным образом работать с
    # multi-value атрибутами. Связался с автором, он внесет это в документацию.
    # Дал совет использовать лямбду для фильтрации атрибута class. Но обнаружил
    # другой баг с вызовом лямбды фильтра атрибута при отсутствии самого
    # атрибута тега. После исправления нужно будет убрать из лямбды проверку
    # `x is not None and `.
    x = SoupStrainer(
        "div", class_=lambda x: x is not None and "block-sch" in x.split()
    )
    x = BeautifulSoup(html, "lxml", parse_only=x)

    for meter in cast(list[Tag], x.contents):
        name = cast(Tag, meter.find("span", class_="type"))

        if not name.string:
            continue

        serial = cast(Tag, name.find_next("span"))
        date = cast(Tag, meter.find(class_="block-note"))
        value = cast(Tag, date.find_next_sibling())

        name, serial = name.text, serial.text.rsplit("№", 1)[-1]
        date = str_to_date(date.text.strip().removeprefix("от "))
        value = Decimal(value.text.strip())

        id = cast(Tag, meter.find("input", {"name": _RE_RAWID}))
        id = int(cast(str, id["value"]))

        result[id] = PublicMeterInfo(name, serial, date, value)

    return result
