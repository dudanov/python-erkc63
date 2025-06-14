import dataclasses as dc
import datetime as dt
import logging
from decimal import Decimal
from typing import Mapping, Self, cast

from bs4 import Tag
from mashumaro import field_options

from .base import ModelBase, parse_dmy
from .parser import parse_html_divclass

_LOGGER = logging.getLogger(__name__)


def parse_serial(x: str) -> str:
    start = x.rindex("№") + 1
    return x[start:].lstrip()


def parse_date(x: str) -> dt.date:
    return parse_dmy(x[3:])


@dc.dataclass(slots=True, kw_only=True)
class PublicMeterInfo(ModelBase):
    """Информация о приборе учета."""

    name: str
    """Ресурс учета"""
    serial: str = dc.field(metadata=field_options(deserialize=parse_serial))
    """Серийный номер"""
    date: dt.date = dc.field(metadata=field_options(deserialize=parse_date))
    """Дата последнего показания"""
    value: Decimal
    """Последнее показание"""

    @classmethod
    def meters_from_html(cls, html: str) -> Mapping[int, Self]:
        """Возвращает словарь `идентификатор - информация о приборе учета`."""

        def _items():
            for meter in parse_html_divclass(html, "block-sch"):
                if len(data := tuple(meter.stripped_strings)) != 4:
                    _LOGGER.debug("Wrong meter data: %s", data)
                    continue

                _LOGGER.debug("Parsing meter data: %s", data)

                id = int(cast(str, cast(Tag, meter("input")[1])["value"]))

                yield id, cls.from_args(data)

        return dict(_items())
