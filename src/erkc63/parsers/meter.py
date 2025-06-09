import dataclasses as dc
import datetime as dt
import logging
from decimal import Decimal
from typing import Mapping, Self, cast

from bs4 import Tag
from mashumaro import DataClassDictMixin, field_options
from mashumaro.config import BaseConfig

from .parser import parse_html_divclass
from .utils import parse_dmy

_LOGGER = logging.getLogger(__name__)


def parse_serial(x: str) -> str:
    start = x.rindex("№") + 1
    return x[start:].lstrip()


def parse_date(x: str) -> dt.date:
    return parse_dmy(x[3:])


@dc.dataclass(slots=True, kw_only=True)
class PublicMeterInfo(DataClassDictMixin):
    """Информация о приборе учета."""

    name: str
    """Ресурс учета"""
    serial: str = dc.field(metadata=field_options(deserialize=parse_serial))
    """Серийный номер"""
    date: dt.date = dc.field(metadata=field_options(deserialize=parse_date))
    """Дата последнего показания"""
    value: Decimal
    """Последнее показание"""

    class Config(BaseConfig):
        lazy_compilation = True

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
                data = {k.name: v for k, v in zip(dc.fields(cls), data)}

                yield id, cls.from_dict(data)

        return dict(_items())
