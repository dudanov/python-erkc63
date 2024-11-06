import dataclasses as dc
import datetime as dt


@dc.dataclass
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
