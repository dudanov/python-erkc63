import dataclasses as dc
import datetime as dt
from decimal import Decimal
from typing import Annotated, Any, Self

from mashumaro import DataClassDictMixin, pass_through
from mashumaro.config import BaseConfig
from mashumaro.types import SerializationStrategy

DateAjax = Annotated[dt.date, "DateAjax"]
DateString = Annotated[dt.date, "DateString"]
DecimalString = Annotated[Decimal, "DecimalString"]
IntNullable = Annotated[int, "IntNullable"]
NormalizedString = Annotated[str, "NormalizedString"]
ReceiptAjax = Annotated[str, "ReceiptAjax"]
Serial = Annotated[str, "Serial"]


def ajax_attr(value: str, attr: str) -> str:
    attr = f' data-{attr}="'
    start = value.index(attr) + len(attr)
    end = value.index('"', start)
    return value[start:end]


def dmy_to_date(value: str) -> dt.date:
    d, m, y = map(int, value[-8:].split("."))
    return dt.date(2000 + y, m, d)


class DecimalStrategy(SerializationStrategy):
    def deserialize(self, value: str) -> Decimal:
        value = value.replace(" ", "")
        value = value.replace(",", ".")
        return Decimal(value)


class MeterSerialStrategy(SerializationStrategy):
    def deserialize(self, value: str) -> str:
        start = value.rindex("№") + 1
        return value[start:].lstrip()


class IntNullableStrategy(SerializationStrategy):
    def deserialize(self, value: str) -> int:
        return int(value) if value.isdecimal() else 0


class NormalizeStrategy(SerializationStrategy):
    def deserialize(self, value: str) -> str:
        return " ".join(value.split())


class ReceiptStrategy(SerializationStrategy):
    def deserialize(self, value: str) -> str:
        return ajax_attr(value, "receipt")


class DateStrategy(SerializationStrategy):
    def __init__(self, *, ajax: bool = False):
        self.ajax = ajax

    def deserialize(self, value: str) -> dt.date:
        if self.ajax:
            value = ajax_attr(value, "sort")

        return dmy_to_date(value)


@dc.dataclass
class ModelBase(DataClassDictMixin):
    class Config(BaseConfig):
        lazy_compilation = True
        serialization_strategy = {
            DateAjax: DateStrategy(ajax=True),
            DateString: DateStrategy(),
            DecimalString: DecimalStrategy(),
            dt.date: pass_through,
            IntNullable: IntNullableStrategy(),
            NormalizedString: NormalizeStrategy(),
            ReceiptAjax: ReceiptStrategy(),
            Serial: MeterSerialStrategy(),
        }

    @classmethod
    def from_args(cls, *args: Any) -> Self:
        fields = (x.name for x in dc.fields(cls))
        return cls.from_dict(dict(zip(fields, args)))
