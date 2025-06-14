import dataclasses as dc
import datetime as dt
from decimal import Decimal
from typing import Annotated, Any, Iterable, Self, Sequence

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig

type Address = Annotated[str, "Address"]
type AjaxDate = Annotated[dt.date, "AjaxDate"]
type AjaxReceipt = Annotated[str, "AjaxReceipt"]
type JsonDecimal = Annotated[Decimal, "JsonDecimal"]


def _parse_int(x: str) -> int:
    return int(x) if x.isdecimal() else 0


def _parse_decimal(x: Any) -> Decimal:
    return Decimal(str(x).replace(" ", ""))


def parse_dmy(x: str) -> dt.date:
    """Возвращает дату из строки вида `dd.mm.yy`"""

    d, m, y = map(int, x.split("."))

    return dt.date(2000 + y, m, d)


def _parse_json_decimal(x: str) -> Decimal:
    return Decimal(x.replace(" ", "").replace(",", "."))


def _ajax_attr(x: str, attr: str) -> str:
    """Возвращает атрибут данных из тега AJAX-запроса"""

    attr = f' data-{attr}="'
    end = x.index('"', start := x.index(attr) + len(attr))

    return x[start:end]


def _ajax_dmy(x: str) -> dt.date:
    """Возвращает дату из атрибута тега AJAX-запроса вида `dd.mm.yy`"""

    return parse_dmy(_ajax_attr(x, "sort"))


def _ajax_receipt(x: str) -> str:
    """Возвращает из тега AJAX-запроса идентификатор запроса квитанции"""

    return _ajax_attr(x, "receipt")


def _str_normalize(x: str) -> str:
    """Нормализует строку, удаляя лишние пробелы."""

    return " ".join(x.split())


@dc.dataclass
class ModelBase(DataClassDictMixin):
    class Config(BaseConfig):
        lazy_compilation = True
        serialization_strategy = {
            Address: {"deserialize": _str_normalize},
            AjaxDate: {"deserialize": _ajax_dmy},
            AjaxReceipt: {"deserialize": _ajax_receipt},
            Decimal: {"deserialize": _parse_decimal},
            JsonDecimal: {"deserialize": _parse_json_decimal},
        }

    @classmethod
    def from_args(
        cls,
        args: Sequence[Any],
        indexes: Iterable[int] | None = None,
    ) -> Self:
        fields = (x.name for x in dc.fields(cls))

        if indexes is None:
            return cls.from_dict(dict(zip(fields, args)))

        return cls.from_dict({k: args[idx] for k, idx in zip(fields, indexes)})
