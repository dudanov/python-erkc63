from typing import Mapping, cast

from bs4 import Tag

from ..types import PublicMeterInfo
from ..utils import str_to_date
from .parser import parse_html_divclass


def parse_meters(html: str) -> Mapping[int, PublicMeterInfo]:
    """
    Парсит HTML страницу с информацией по приборам учета.

    Возвращает словарь `идентификатор - информация о приборе учета`.
    """

    def _items():
        for meter in parse_html_divclass(html, "block-sch"):
            if len(x := tuple(meter.stripped_strings)) != 4:
                continue

            name, serial, date, value = x

            serial = serial[serial.rfind("№") + 1 :]
            date = str_to_date(date.removeprefix("от ")).isoformat()

            id = int(cast(str, cast(Tag, meter("input")[1])["value"]))

            yield (
                id,
                PublicMeterInfo.from_dict(
                    {
                        "name": name,
                        "serial": serial,
                        "date": date,
                        "value": value,
                    }
                ),
            )

    return dict(_items())
