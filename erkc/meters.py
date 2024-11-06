import dataclasses as dc
import datetime as dt
import re
from typing import cast

import bs4

from .utils import str_to_date


@dc.dataclass
class PublicMeterInfo:
    """
    Информация о приборе учета.

    Результат парсинга HTML-страницы.
    """

    id: int
    """Идентификатор."""
    serial: str
    """Серийный номер."""
    date: dt.date
    """Дата последнего значения."""
    value: float
    """Последнее принятое значение."""


@dc.dataclass
class MeterValue:
    """Запись показания счетчика"""

    date: dt.date
    """Дата показания"""
    value: float
    """Значение"""
    consumption: float
    """Расход"""
    reason: str
    """Источник"""


@dc.dataclass
class MeterDescription:
    """Счетчик с архивом показаний"""

    name: str
    """Ресурс учета"""
    serial: str
    """Серийный номер"""
    values: tuple[MeterValue, ...]
    """Архив показаний"""


def parse_meters(resp: str) -> dict[str, PublicMeterInfo]:
    """
    Парсит страницу с информацией по приборам учета.

    Возвращает словарь `ресурс - прибор учета`.
    """

    bs = bs4.BeautifulSoup(resp, "html.parser")
    form = cast(bs4.Tag, bs.find("form", id="sendCountersValues"))
    result: dict[str, PublicMeterInfo] = {}

    for meter in form.find_all("div", class_="block-sch"):
        meter = cast(bs4.Tag, meter)

        res = cast(bs4.Tag, meter.find("span", class_="type"))

        if not res.text:
            continue

        sn = cast(bs4.Tag, res.find_next("span"))
        date = cast(bs4.Tag, meter.find(class_="block-note"))
        val = cast(bs4.Tag, date.find_next_sibling())

        res, sn = res.text, sn.text.rsplit("№", 1)[-1]
        date = str_to_date(date.text.strip().removeprefix("от "))
        val = float(val.text.strip())

        id = cast(bs4.Tag, meter.find("input", {"name": re.compile(r"rowId")}))
        id = int(cast(str, id["value"]))

        result[res] = PublicMeterInfo(id, sn, date, val)

    return result
