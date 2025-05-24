import dataclasses as dc
import itertools as it
import re
from decimal import Decimal
from types import MappingProxyType
from typing import Any, cast

from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer

from .account import AccountInfo
from .errors import ParsingError
from .meters import PublicMeterInfo
from .utils import str_normalize, str_to_date

_RE_RAWID = re.compile(r"rowId")


def parse_accounts(html: str) -> list[int]:
    x = SoupStrainer("div", id="select_ls_dropdown")
    x = BeautifulSoup(html, "lxml", parse_only=x)
    menu = cast(Tag, x.contents[0])

    accounts: list[int] = []

    for x in cast(list[Tag], menu("a")[:-2]):  # крайние 2 ссылки не аккаунты
        id = str(x["href"]).rsplit("/", 1)[-1]
        accounts.append(int(id))

    # сортировка вторичных счетов
    if len(accounts) >= 3:
        accounts[1:] = sorted(accounts[1:])

    return accounts


def parse_token(html: str) -> str:
    x = SoupStrainer("meta", {"name": "csrf-token"})
    x = BeautifulSoup(html, "lxml", parse_only=x)

    return str(cast(Tag, x.contents[0])["content"])


def parse_account(html: str) -> AccountInfo:
    x = SoupStrainer("div", class_="widget-left")
    x = BeautifulSoup(html, "lxml", parse_only=x)
    wl = cast(Tag, x.contents[0])

    ws1 = cast(Tag, wl.find("div", class_="widget-section1"))
    ws1 = cast(list[Tag], ws1("div", class_="text-col-left"))

    ws2 = cast(Tag, wl.find("div", class_="widget-section2"))
    ws2 = cast(list[Tag], ws2("div", class_="text-col-right"))

    ws = (str_normalize(x.text) for x in it.chain(ws1, ws2))

    def _cnv(k, v):
        return k.type(v) if v != "-" else 0

    data: Any = (_cnv(*x) for x in zip(dc.fields(AccountInfo), ws))

    return AccountInfo(*data)


def parse_meters(html: str) -> MappingProxyType[int, PublicMeterInfo]:
    """
    Парсит HTML страницу с информацией по приборам учета.

    Возвращает словарь `идентификатор - информация о приборе учета`.
    """

    bs = BeautifulSoup(html, "lxml")

    if (form := cast(Tag, bs.find("form", id="sendCountersValues"))) is None:
        raise ParsingError("Не найдена форма отправки показаний счетчиков.")

    result: dict[int, PublicMeterInfo] = {}

    for meter in form("div", class_="block-sch"):
        meter = cast(Tag, meter)

        name = cast(Tag, meter.find("span", class_="type"))

        if not name.text:
            continue

        serial = cast(Tag, name.find_next("span"))
        date = cast(Tag, meter.find(class_="block-note"))
        value = cast(Tag, date.find_next_sibling())

        name, serial = name.text, serial.text.rsplit("№", 1)[-1]
        date = str_to_date(date.text.strip().removeprefix("от "))
        value = Decimal(value.text.strip())

        id = cast(Tag, meter.find("input", {"name": _RE_RAWID}))
        id = int(cast(str, id["value"]))

        result[id] = PublicMeterInfo(name, serial, date, value)

    return MappingProxyType(result)
