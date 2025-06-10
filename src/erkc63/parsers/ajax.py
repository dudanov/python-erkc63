import datetime as dt

from .utils import parse_dmy


def ajax_attr(x: str, attr: str) -> str:
    """Возвращает атрибут данных из тега AJAX-запроса"""

    attr = f' data-{attr}="'
    end = x.index('"', start := x.index(attr) + len(attr))

    return x[start:end]


def ajax_dmy(x: str) -> dt.date:
    """Возвращает дату из атрибута тега AJAX-запроса вида `dd.mm.yy`"""

    return parse_dmy(ajax_attr(x, "sort"))


def ajax_receipt(x: str) -> str:
    """Возвращает из тега AJAX-запроса идентификатор запроса квитанции"""

    return ajax_attr(x, "receipt")
