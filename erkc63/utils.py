import datetime as dt
import re
from typing import Any


def date_first_day(_date: dt.date) -> dt.date:
    """Возвращает дату первого числа месяца."""

    return dt.date(_date.year, _date.month, 1)


def date_last_accrual(accrual_day: int = 25) -> dt.date:
    """Возвращает дату последнего расчетного периода."""

    if (today := dt.date.today()).day > accrual_day:
        return dt.date(today.year, today.month, 1)

    if today.month != 1:
        return dt.date(today.year, today.month - 1, 1)

    return dt.date(today.year - 1, 12, 1)


def first_int(_str: str) -> int:
    """Возвращает первое целое число в строке."""

    for idx, sym in enumerate(_str):
        if not sym.isdigit():
            _str = _str[:idx]
            break

    return int(_str)


def to_float(_str: Any) -> float:
    """Преобразует строку в число."""

    return float(str(_str).replace(",", ".").replace(" ", ""))


def str_to_date(_str: str) -> dt.date:
    """Преобразует строку вида `dd.mm.yy` в дату."""

    return dt.datetime.strptime(_str, "%d.%m.%y").date()


def data_attr(_str: str) -> str:
    """Извлекает строку из атрибута данных тэга."""

    if m := re.search(r' data-\w+="([\w/.+=]+)"', _str):
        return m.group(1)

    raise ValueError


def date_attr(_str: str) -> dt.date:
    return str_to_date(data_attr(_str))


def date_to_str(_date: dt.date) -> str:
    """Преобразует дату в строку вида `dd.mm.YYYY`."""

    return _date.strftime("%d.%m.%Y")


def str_normalize(_str: str) -> str:
    """Нормализует строку, удаляя лишние пробелы."""

    return " ".join(_str.split())
