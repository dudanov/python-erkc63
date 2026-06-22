# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025-2026 Sergey Dudanov <sergey.dudanov@gmail.com>

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
