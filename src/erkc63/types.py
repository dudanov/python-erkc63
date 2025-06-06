from __future__ import annotations

import dataclasses as dc
import datetime as dt
from decimal import Decimal

from mashumaro.mixins.dict import DataClassDictMixin


@dc.dataclass(frozen=True, slots=True)
class Payment:
    """
    Платеж.

    Объект ответа на запрос `paymentsHistory`.
    """

    date: dt.date
    """Дата"""
    payment: Decimal
    """Сумма"""
    provider: str
    """Платежный провайдер"""


@dc.dataclass(frozen=True)
class MeterInfo(DataClassDictMixin):
    name: str
    """Ресурс учета"""
    serial: str
    """Серийный номер"""

    def __eq__(self, other: MeterInfo) -> bool:
        return self.name == other.name and self.serial == other.serial


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
