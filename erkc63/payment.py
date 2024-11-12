import dataclasses as dc
import datetime as dt


@dc.dataclass(frozen=True)
class Payment:
    """
    Платеж.

    Объект ответа на запрос `paymentsHistory`.
    """

    date: dt.date
    """Дата"""
    summa: float
    """Сумма"""
    provider: str
    """Платежный провайдер"""
