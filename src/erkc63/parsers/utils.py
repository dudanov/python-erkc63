import datetime as dt


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


def first_int(x: str) -> int:
    """Возвращает первое целое число в строке."""

    for idx, sym in enumerate(x):
        if not sym.isdigit():
            x = x[:idx]
            break

    return int(x)


def str_to_date(x: str) -> dt.date:
    """Преобразует строку вида `dd.mm.yy` в дату."""

    return dt.datetime.strptime(x, "%d.%m.%y").date()


def date_to_str(x: dt.date) -> str:
    """Преобразует дату в строку вида `dd.mm.YYYY`."""

    return x.strftime("%d.%m.%Y")


def str_date_to_iso(x: str) -> str:
    """Преобразует дату `dd.mm.yy` в дату ISO `YYYY-mm-dd`."""

    return "20{2}-{1}-{0}".format(*x.split("."))


def str_normalize(x: str) -> str:
    """Нормализует строку, удаляя лишние пробелы."""

    return " ".join(x.split())
