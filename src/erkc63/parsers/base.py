import dataclasses as dc
import datetime as dt
from decimal import Decimal
from typing import Annotated, Any, Self

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig

type Address = Annotated[str, "Address"]
type AjaxDate = Annotated[dt.date, "AjaxDate"]
type AjaxReceipt = Annotated[str, "AjaxReceipt"]
type JsonDecimal = Annotated[Decimal, "JsonDecimal"]
type NullableInt = Annotated[int, "NullableInt"]
type Serial = Annotated[str, "Serial"]


def _parse_serial(x: str) -> str:
    start = x.rindex("№") + 1
    return x[start:].lstrip()


def _parse_int(x: str) -> int:
    return int(x) if x.isdecimal() else 0


def _parse_decimal(x: Any) -> Decimal:
    return Decimal(str(x).replace(" ", ""))


def _parse_dmy(x: str) -> dt.date:
    start = x.rfind(" ") + 1
    d, m, y = map(int, x[start:].split("."))
    return dt.date(2000 + y, m, d)


def _parse_json_decimal(x: str) -> Decimal:
    return Decimal(x.replace(" ", "").replace(",", "."))


def _ajax_attr(x: str, attr: str) -> str:
    attr = f' data-{attr}="'
    end = x.index('"', start := x.index(attr) + len(attr))
    return x[start:end]


def _ajax_dmy(x: str) -> dt.date:
    return _parse_dmy(_ajax_attr(x, "sort"))


def _ajax_receipt(x: str) -> str:
    return _ajax_attr(x, "receipt")


def _str_normalize(x: str) -> str:
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
            dt.date: {"deserialize": _parse_dmy},
            JsonDecimal: {"deserialize": _parse_json_decimal},
            NullableInt: {"deserialize": _parse_int},
            Serial: {"deserialize": _parse_serial},
        }

    @classmethod
    def from_args(cls, *args: Any) -> Self:
        fields = (x.name for x in dc.fields(cls))
        return cls.from_dict(dict(zip(fields, args)))
