import dataclasses as dc
import datetime as dt
import logging
from decimal import Decimal
from typing import Mapping, Self, cast

from bs4 import Tag

from .base import AjaxDate, ModelBase, Serial
from .parser import parse_html_divclass

_LOGGER = logging.getLogger(__name__)


@dc.dataclass(slots=True, kw_only=True)
class PublicMeterInfo(ModelBase):
    """Информация о приборе учета."""

    name: str
    """Ресурс учета"""
    serial: Serial
    """Серийный номер"""
    date: dt.date
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

                yield id, cls.from_args(*data)

        return dict(_items())


@dc.dataclass(slots=True, kw_only=True)
class MeterValue(ModelBase):
    """Показание счетчика"""

    date: AjaxDate
    """Дата"""
    value: Decimal
    """Значение"""
    consumption: Decimal
    """Расход"""
    source: str
    """Источник"""


@dc.dataclass(slots=True, kw_only=True)
class MeterInfoHistory(ModelBase):
    """Счетчик с архивом показаний"""

    name: str
    """Ресурс учета"""
    serial: Serial
    """Серийный номер"""
    history: list[MeterValue] = dc.field(default_factory=list)
    """Архив показаний"""

    @classmethod
    def from_string(cls, key: str, history: list[MeterValue]) -> Self:
        x = cls.from_args(*key.split(",", 1))
        x.history = history
        return x
