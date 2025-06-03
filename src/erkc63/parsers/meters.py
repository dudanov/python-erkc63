from typing import Mapping, cast

from bs4 import Tag

from ..types import PublicMeterInfo
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
            id = int(cast(str, cast(Tag, meter("input")[1])["value"]))

            data = {
                "name": name,
                "serial": serial[serial.rfind("№") + 1 :].lstrip(),
                "date": "20{2}-{1}-{0}".format(*date[3:].split(".")),
                "value": value,
            }

            yield id, PublicMeterInfo.from_dict(data)

    return dict(_items())
