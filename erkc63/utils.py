import datetime as dt
import re
from decimal import Decimal
from typing import Any


def date_first_day(value: dt.date) -> dt.date:
    """Возвращает дату первого числа месяца."""

    return dt.date(value.year, value.month, 1)


def date_last_accrual(accrual_day: int = 25) -> dt.date:
    """Возвращает дату последнего расчетного периода."""

    if (today := dt.date.today()).day > accrual_day:
        return dt.date(today.year, today.month, 1)

    if today.month != 1:
        return dt.date(today.year, today.month - 1, 1)

    return dt.date(today.year - 1, 12, 1)


def first_int(value: str) -> int:
    """Возвращает первое целое число в строке."""

    for idx, sym in enumerate(value):
        if not sym.isdigit():
            value = value[:idx]
            break

    return int(value)


def to_decimal(value: Any) -> Decimal:
    """Преобразует строку в число."""

    return Decimal(str(value).replace(" ", "").replace(",", "."))


def str_to_date(value: str) -> dt.date:
    """Преобразует строку вида `dd.mm.yy` в дату."""

    return dt.datetime.strptime(value, "%d.%m.%y").date()


def data_attr(value: str) -> str:
    """Извлекает строку из атрибута данных тэга."""

    if m := re.search(r' data-\w+="([\w/.+=]+)"', value):
        return m.group(1)

    raise ValueError


def date_attr(value: str) -> dt.date:
    return str_to_date(data_attr(value))


def date_to_str(value: dt.date) -> str:
    """Преобразует дату в строку вида `dd.mm.YYYY`."""

    return value.strftime("%d.%m.%Y")


def str_normalize(value: str) -> str:
    """Нормализует строку, удаляя лишние пробелы."""

    return " ".join(value.split())
