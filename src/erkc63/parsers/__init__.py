import datetime as dt

from .account import AccountInfo, PublicAccountInfo
from .accrual import Accrual, AccrualDetalization, Accruals, MonthAccrual
from .base import ajax_attr, dmy_to_date
from .meter import MeterInfoHistory, MeterValue, PublicMeterInfo
from .parser import parse_accounts, parse_token
from .payment import Payment


def date_last_accrual(accrual_day: int = 25) -> dt.date:
    """Возвращает дату последнего расчетного периода."""

    if (today := dt.date.today()).day > accrual_day:
        return dt.date(today.year, today.month, 1)

    if today.month != 1:
        return dt.date(today.year, today.month - 1, 1)

    return dt.date(today.year - 1, 12, 1)


def date_to_str(x: dt.date) -> str:
    """Преобразует дату в строку вида `dd.mm.YYYY`."""

    return x.strftime("%d.%m.%Y")


__all__ = [
    "AccountInfo",
    "Accrual",
    "AccrualDetalization",
    "Accruals",
    "ajax_attr",
    "date_last_accrual",
    "date_to_str",
    "dmy_to_date",
    "MeterInfoHistory",
    "MeterValue",
    "MonthAccrual",
    "parse_accounts",
    "parse_token",
    "Payment",
    "PublicAccountInfo",
    "PublicMeterInfo",
]
