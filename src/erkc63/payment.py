import dataclasses as dc
import datetime as dt
from decimal import Decimal


@dc.dataclass(frozen=True)
class Payment:
    """
    Платеж.

    Объект ответа на запрос `paymentsHistory`.
    """

    date: dt.date
    """Дата"""
    summa: Decimal
    """Сумма"""
    provider: str
    """Платежный провайдер"""
