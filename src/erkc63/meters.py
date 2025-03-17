from __future__ import annotations

import dataclasses as dc
import datetime as dt
from decimal import Decimal


@dc.dataclass(frozen=True)
class MeterInfo:
    name: str
    """Ресурс учета"""
    serial: str
    """Серийный номер"""

    def __eq__(self, other: MeterInfo) -> bool:
        return self.name == other.name and self.serial == other.serial


@dc.dataclass(frozen=True, eq=False)
class PublicMeterInfo(MeterInfo):
    """
    Информация о приборе учета.

    Результат парсинга HTML-страницы.
    """

    date: dt.date
    """Дата последнего показания"""
    value: Decimal
    """Последнее показание"""


@dc.dataclass(frozen=True)
class MeterValue:
    """Показание счетчика"""

    date: dt.date
    """Дата"""
    value: Decimal
    """Значение"""
    consumption: Decimal
    """Расход"""
    source: str
    """Источник"""


@dc.dataclass(frozen=True, eq=False)
class MeterInfoHistory(MeterInfo):
    """Счетчик с архивом показаний"""

    history: list[MeterValue]
    """Архив показаний"""
