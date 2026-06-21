import datetime as dt

from .account import AccountInfo, PublicAccountInfo
from .accrual import Accrual, AccrualDetalization, Accruals, MonthAccrual
from .base import ajax_attr, dmy_to_date
from .meter import MeterHistory, MeterInfo, MeterValue
from .parser import parse_accounts, parse_token
from .payment import Payment

try:
    from .qrcode import AccrualData

    QRCODE_SUPPORT = True

except ImportError:
    QRCODE_SUPPORT = False


def date_last_accrual(accrual_day: int = 25) -> dt.date:
    """Возвращает дату последнего расчетного периода."""

    if (today := dt.date.today()).day > accrual_day:
        return dt.date(today.year, today.month, 1)

    if today.month != 1:
        return dt.date(today.year, today.month - 1, 1)

    return dt.date(today.year - 1, 12, 1)


def date_to_dmy(x: dt.date) -> str:
    """Преобразует дату в строку вида `dd.mm.YYYY`."""

    return f"{x.day:02}.{x.month:02}.{x.year}"


__all__ = [
    "AccountInfo",
    "Accrual",
    "AccrualData",
    "AccrualDetalization",
    "Accruals",
    "ajax_attr",
    "date_last_accrual",
    "date_to_dmy",
    "dmy_to_date",
    "MeterHistory",
    "MeterInfo",
    "MeterValue",
    "MonthAccrual",
    "parse_accounts",
    "parse_token",
    "Payment",
    "PublicAccountInfo",
    "QRCODE_SUPPORT",
]
