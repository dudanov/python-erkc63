import dataclasses as dc

from .base import DateAjax, DecimalString, ModelBase


@dc.dataclass(slots=True)
class Payment(ModelBase):
    """
    Платеж.

    Объект ответа на запрос `paymentsHistory`.
    """

    date: DateAjax
    """Дата"""
    payment: DecimalString
    """Сумма"""
    provider: str
    """Платежный провайдер"""
