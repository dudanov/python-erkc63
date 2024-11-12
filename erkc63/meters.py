import dataclasses as dc
import datetime as dt
import re
from types import MappingProxyType
from typing import cast

from bs4 import BeautifulSoup, Tag

from .utils import str_to_date

_RE_RAWID = re.compile(r"rowId")


@dc.dataclass(frozen=True)
class MeterInfo:
    name: str
    """Ресурс учета"""
    serial: str
    """Серийный номер"""

    def __eq__(self, other: "MeterInfo") -> bool:
        return self.name == other.name and self.serial == other.serial


@dc.dataclass(frozen=True, eq=False)
class PublicMeterInfo(MeterInfo):
    """
    Информация о приборе учета.

    Результат парсинга HTML-страницы.
    """

    date: dt.date
    """Дата последнего показания"""
    value: float
    """Последнее показание"""


@dc.dataclass(frozen=True)
class MeterValue:
    """Показание счетчика"""

    date: dt.date
    """Дата"""
    value: float
    """Значение"""
    consumption: float
    """Расход"""
    source: str
    """Источник"""


@dc.dataclass(frozen=True, eq=False)
class MeterInfoHistory(MeterInfo):
    """Счетчик с архивом показаний"""

    history: tuple[MeterValue, ...]
    """Архив показаний"""


def get_meters_from_page(html: str) -> MappingProxyType[int, PublicMeterInfo]:
    """
    Парсит HTML страницу с информацией по приборам учета.

    Возвращает словарь `идентификатор - информация о приборе учета`.
    """

    result: dict[int, PublicMeterInfo] = {}

    bs = BeautifulSoup(html, "html.parser")
    form = cast(Tag, bs.find("form", id="sendCountersValues"))

    for meter in form.find_all("div", class_="block-sch"):
        meter = cast(Tag, meter)

        name = cast(Tag, meter.find("span", class_="type"))

        if not name.text:
            continue

        serial = cast(Tag, name.find_next("span"))
        date = cast(Tag, meter.find(class_="block-note"))
        value = cast(Tag, date.find_next_sibling())

        name, serial = name.text, serial.text.rsplit("№", 1)[-1]
        date = str_to_date(date.text.strip().removeprefix("от "))
        value = float(value.text.strip())

        id = cast(Tag, meter.find("input", {"name": _RE_RAWID}))
        id = int(cast(str, id["value"]))

        result[id] = PublicMeterInfo(name, serial, date, value)

    return MappingProxyType(result)
