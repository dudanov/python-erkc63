import datetime as dt

from .utils import parse_dmy


def ajax_attr(tag: str, attr: str) -> str:
    """Возвращает атрибут данных из тега AJAX-запроса"""

    attr = f' data-{attr}="'
    end = tag.index('"', start := tag.index(attr) + len(attr))

    return tag[start:end]


def ajax_dmy(tag: str) -> dt.date:
    """Возвращает дату из атрибута тега AJAX-запроса вида `dd.mm.yy`"""

    return parse_dmy(ajax_attr(tag, "sort"))


def ajax_receipt(tag: str) -> str:
    """Возвращает из тега AJAX-запроса идентификатор запроса квитанции"""

    return ajax_attr(tag, "receipt")
