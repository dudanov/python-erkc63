import dataclasses as dc
import datetime as dt
import logging
from decimal import Decimal
from typing import Mapping, Self, cast

from bs4 import Tag
from mashumaro import DataClassDictMixin

from .parser import parse_html_divclass

_LOGGER = logging.getLogger(__name__)


@dc.dataclass(slots=True, kw_only=True)
class PublicMeterInfo(DataClassDictMixin):
    """Информация о приборе учета."""

    name: str
    """Ресурс учета"""
    serial: str = dc.field(
        metadata={"deserialize": lambda x: x[x.rfind("№") + 1 :].lstrip()}
    )
    """Серийный номер"""
    date: dt.date = dc.field(
        metadata={
            "deserialize": lambda x: "20{2}-{1}-{0}".format(*x[3:].split("."))
        }
    )
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
                data = {k.name: v for k, v in zip(dc.fields(cls), data)}

                yield id, cls.from_dict(data)

        return dict(_items())
