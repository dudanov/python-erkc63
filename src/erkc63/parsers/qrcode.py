import asyncio
import dataclasses as dc
import io

import pymupdf
from PIL import Image

type PilImage = Image.Image


@dc.dataclass(slots=True)
class AccrualFiles:
    """Изображения счета ЕРКЦ"""

    source: bytes
    """Исходный PDF"""
    page: bytes
    """PNG изображение страницы счета"""
    codes: tuple[bytes, ...]
    """PNG изображения QR-кодов оплаты счета"""


# Сохраняет Pixmap в 8-битный оптимизированный PNG в палитре WEB
def _png(pix: pymupdf.Pixmap, xy: tuple[int, int]) -> bytes:
    bio = io.BytesIO()

    img = pix.pil_image()
    img.thumbnail(xy)
    img = img.convert(mode="P", palette=Image.Palette.WEB)
    img.save(bio, format="png", optimize=True)

    return bio.getvalue()


# Рендерит страницу в данные PNG вписывающегося в указанное разрешение
def _page(page: pymupdf.Page, xy: tuple[int, int]) -> bytes:
    factor = min(x / y for x, y in zip(xy, page.rect[2:]))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(factor, factor))

    return _png(pix, xy)


# Извлекает изображение со страницы в данные PNG
def _img(page: pymupdf.Page, xy: tuple[int, int], img_name: str) -> bytes:
    for item in page.get_images():
        xref, name = item[0], item[7]

        if name != img_name:
            continue

        pix = pymupdf.Pixmap(page.parent, xref)

        return _png(pix, xy)

    raise FileNotFoundError("Изображение на странице не найдено.")


def _accrual(data: bytes, xy: tuple[int, int], *images: str):
    with pymupdf.open(stream=data) as doc:
        page = doc[0]
        width, height = page.rect[2:]

        if height > width:
            # Только у счета на пени портретная ориентация.
            # Заполнен только в начале. Обрежем пополам.
            page.set_cropbox(pymupdf.Rect(0, 0, width, height / 2))

        return data, _page(page, xy), tuple(map(lambda x: _img(page, xy, x), images))


async def erkc_files(pdf: bytes, xy: tuple[int, int]) -> AccrualFiles:
    return AccrualFiles(*await asyncio.to_thread(_accrual, pdf, xy, "img2", "img4"))


async def peni_files(pdf: bytes, xy: tuple[int, int]) -> AccrualFiles:
    return AccrualFiles(*await asyncio.to_thread(_accrual, pdf, xy, "img0"))
