import dataclasses as dc
import datetime as dt
import itertools as it
import logging
from decimal import Decimal
from typing import Iterator, List, Mapping, Self, Tuple, cast

from bs4 import Tag

from .base import DateString, DecimalString, ModelBase, Serial
from .parser import parse_html_divclass

_LOGGER = logging.getLogger(__name__)


@dc.dataclass(slots=True, kw_only=True)
class MeterInfo(ModelBase):
    """Информация о приборе учета"""

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
    """Показание прибора учета"""

    date: dt.date
    """Дата"""
    value: Decimal
    """Значение"""
    consumption: Decimal
    """Расход"""
    source: str
    """Источник"""


@dc.dataclass(slots=True, kw_only=True)
class MeterHistory(ModelBase):
    """История показаний прибора учета"""

    name: str
    """Ресурс учета"""
    serial: Serial
    """Серийный номер"""
    values: List[MeterValue] = dc.field(metadata={"deserialize": list})
    """История показаний"""

    @classmethod
    def from_tuple(cls, x: Tuple[str, List[MeterValue]]) -> Self:
        """Создает объект из кортежа ключа прибора учета
        (ресурс, серийный номер) и списка показаний."""

        key, values = x

        def _values() -> Iterator[MeterValue]:
            for _, group in it.groupby(values, lambda x: x.date):
                if not (result := next(group)).consumption:
                    for x in group:
                        if x.consumption:
                            result = x
                            break

                yield result

        return cls.from_args(*key.split(",", 1), _values())
