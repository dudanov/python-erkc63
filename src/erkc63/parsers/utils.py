import datetime as dt


def date_last_accrual(accrual_day: int = 25) -> dt.date:
    """Возвращает дату последнего расчетного периода."""

    if (today := dt.date.today()).day > accrual_day:
        return dt.date(today.year, today.month, 1)

    if today.month != 1:
        return dt.date(today.year, today.month - 1, 1)

    return dt.date(today.year - 1, 12, 1)


def str_to_date(x: str) -> dt.date:
    """Преобразует строку вида `dd.mm.yy` в дату."""

    d, m, y = map(int, x[-8:].split("."))
    return dt.date(2000 + y, m, d)


def date_to_str(x: dt.date) -> str:
    """Преобразует дату в строку вида `dd.mm.YYYY`."""

    return x.strftime("%d.%m.%Y")


def ajax_attr(value: str, attr: str) -> str:
    attr = f' data-{attr}="'
    start = value.index(attr) + len(attr)
    end = value.index('"', start)
    return value[start:end]
