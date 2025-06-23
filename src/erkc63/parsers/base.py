import dataclasses as dc
import datetime as dt
from decimal import Decimal
from typing import Annotated, Any, Self

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig
from mashumaro.types import SerializationStrategy

from .utils import ajax_attr, str_to_date

type NormalizedString = Annotated[str, "NormalizedString"]
"""Нормализованная строка, в которой удалены лишние пробелы."""
type AjaxDate = Annotated[dt.date, "AjaxDate"]
"""Дата, полученная из AJAX-ответа."""
type AjaxReceipt = Annotated[str, "AjaxReceipt"]
"""Идентификатор на скачивание PDF квитанции."""
type NullableInt = Annotated[int, "NullableInt"]
"""Целое число, у которого символ `-` означает 0."""
type Serial = Annotated[str, "Serial"]
"""Серийный номер счетчика, начинающийся с символа `№`."""


class DecimalStrategy(SerializationStrategy, use_annotations=True):
    def deserialize(self, value: str) -> Decimal:
        return Decimal(value.replace(" ", "").replace(",", "."))


class MeterSerialStrategy(SerializationStrategy):
    def deserialize(self, value: str) -> str:
        start = value.rindex("№") + 1
        return value[start:].lstrip()


class NullableIntStrategy(SerializationStrategy):
    def deserialize(self, value: str) -> int:
        return int(value) if value.isdecimal() else 0


class NormalizeStrategy(SerializationStrategy):
    def deserialize(self, value: str) -> str:
        return " ".join(value.split())


class AjaxStrategy(SerializationStrategy):
    def __init__(self, attr: str):
        self.attr = attr

    def deserialize(self, value: str) -> str:
        return ajax_attr(value, self.attr)


class DateStrategy(SerializationStrategy):
    def __init__(self, *, ajax: bool = False):
        self.ajax = AjaxStrategy("sort") if ajax else None

    def deserialize(self, value: str) -> dt.date:
        if self.ajax:
            value = self.ajax.deserialize(value)

        return str_to_date(value)


@dc.dataclass
class ModelBase(DataClassDictMixin):
    class Config(BaseConfig):
        lazy_compilation = True
        serialization_strategy = {
            NormalizedString: NormalizeStrategy(),
            AjaxDate: DateStrategy(ajax=True),
            AjaxReceipt: AjaxStrategy("receipt"),
            Decimal: DecimalStrategy(),
            dt.date: DateStrategy(),
            NullableInt: NullableIntStrategy(),
            Serial: MeterSerialStrategy(),
        }

    @classmethod
    def from_args(cls, *args: Any) -> Self:
        fields = (x.name for x in dc.fields(cls))
        return cls.from_dict(dict(zip(fields, args)))
