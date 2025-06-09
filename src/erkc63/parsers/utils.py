import datetime as dt
from decimal import Decimal
from typing import Any


def date_last_accrual(accrual_day: int = 25) -> dt.date:
    """Возвращает дату последнего расчетного периода."""

    if (today := dt.date.today()).day > accrual_day:
        return dt.date(today.year, today.month, 1)

    if today.month != 1:
        return dt.date(today.year, today.month - 1, 1)

    return dt.date(today.year - 1, 12, 1)


def str_to_date(x: str) -> dt.date:
    """Преобразует строку вида `dd.mm.yy` в дату."""

    return dt.datetime.strptime(x, "%d.%m.%y").date()


def date_to_str(x: dt.date) -> str:
    """Преобразует дату в строку вида `dd.mm.YYYY`."""

    return x.strftime("%d.%m.%Y")


def str_normalize(x: str) -> str:
    """Нормализует строку, удаляя лишние пробелы."""

    return " ".join(x.split())


def parse_dmy(x: str) -> dt.date:
    """Возвращает дату из строки вида `dd.mm.yy`"""

    d, m, y = map(int, x.split("."))

    return dt.date(2000 + y, m, d)


def parse_decimal(x: Any) -> Decimal:
    """Преобразует строку в число"""

    return Decimal(str(x).replace(" ", "").replace(",", "."))
