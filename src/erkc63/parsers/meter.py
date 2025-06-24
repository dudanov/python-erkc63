import dataclasses as dc
import datetime as dt
import itertools as it
import logging
from decimal import Decimal
from typing import Mapping, Self, cast

from bs4 import Tag

from .base import DateString, DecimalString, ModelBase, Serial
from .parser import parse_html_divclass

_LOGGER = logging.getLogger(__name__)


@dc.dataclass(slots=True, kw_only=True)
class PublicMeterInfo(ModelBase):
    """Информация о приборе учета."""

    name: str
    """Ресурс учета"""
    serial: Serial
    """Серийный номер"""
    date: DateString
    """Дата последнего показания"""
    value: DecimalString
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

    date: dt.date
    """Дата"""
    value: Decimal
    """Значение"""
    consumption: Decimal
    """Расход"""
    source: str
    """Источник"""

    @property
    def previous(self) -> Decimal:
        return self.value - self.consumption


@dc.dataclass(slots=True, kw_only=True)
class MeterInfoHistory(ModelBase):
    """Счетчик с архивом показаний"""

    name: str
    """Ресурс учета"""
    serial: Serial
    """Серийный номер"""
    history: list[MeterValue] = dc.field(metadata={"deserialize": list})
    """Архив показаний"""

    @classmethod
    def from_tuple(cls, value: tuple[str, list[MeterValue]]) -> Self:
        """Создает объект из кортежа, полученного из кэша."""

        key, history = value

        def _filter():
            for _, group in it.groupby(history, lambda x: x.date):
                if not (result := next(group)).consumption:
                    for x in group:
                        if x.consumption:
                            result = x
                            break

                yield result

        return cls.from_args(*key.split(",", 1), _filter())
