import re
from decimal import Decimal
from typing import Mapping, cast

from bs4 import Tag

from ..types import PublicMeterInfo
from ..utils import str_to_date
from .parser import parse_html_divclass

_RE_RAWID = re.compile(r"rowId")


def parse_meters(html: str) -> Mapping[int, PublicMeterInfo]:
    """
    Парсит HTML страницу с информацией по приборам учета.

    Возвращает словарь `идентификатор - информация о приборе учета`.
    """

    result: dict[int, PublicMeterInfo] = {}

    for meter in parse_html_divclass(html, "block-sch"):
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
