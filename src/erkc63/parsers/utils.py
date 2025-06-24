import datetime as dt


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
