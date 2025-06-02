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
        name, serial, date, value = meter.stripped_strings

        if not name:
            continue

        serial = serial.rsplit("№", 1)[-1]
        date, value = str_to_date(date.removeprefix("от ")), Decimal(value)

        id = int(cast(str, cast(Tag, meter("input")[1])["value"]))
        result[id] = PublicMeterInfo(name, serial, date, value)

    return result
