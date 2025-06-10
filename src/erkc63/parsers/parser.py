import dataclasses as dc
from typing import Any, Iterable, Self, Sequence, cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer
from mashumaro import DataClassDictMixin


@dc.dataclass
class ModelBase(DataClassDictMixin):
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


def parse_html_divclass(html: str, cls_prefix: str) -> list[Tag]:
    """Возвращает список тегов `div`, имеющих класс с указанным префиксом"""

    x = SoupStrainer(
        name="div",
        class_=lambda x: x is not None
        and any(k.startswith(cls_prefix) for k in x.split()),
    )

    return cast(list[Tag], BeautifulSoup(html, "lxml", parse_only=x).contents)
