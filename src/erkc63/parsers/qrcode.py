import dataclasses as dc
import io

import pymupdf
from PIL import Image

type PilImage = Image.Image


@dc.dataclass(slots=True, frozen=True)
class AccrualFiles:
    """Изображения счета ЕРКЦ"""

    source: bytes
    """Исходный PDF"""
    page: bytes
    """PNG изображение страницы счета"""
    codes: tuple[bytes, ...]
    """PNG изображения QR-кодов оплаты счета"""


# Сохраняет Pixmap в 8-битный оптимизированный PNG в палитре WEB
def _png(pix: pymupdf.Pixmap) -> bytes:
    bio = io.BytesIO()

    img = pix.pil_image()
    img = img.convert(mode="P", palette=Image.Palette.WEB)
    img.save(bio, format="png", optimize=True)

    return bio.getvalue()


# Рендерит страницу в данные PNG вписывающегося в указанное разрешение
def _page(page: pymupdf.Page, xy: tuple[int, int]) -> bytes:
    width, height = page.rect.width, page.rect.height
    scale = min(xy[0] / width, xy[1] / height)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))

    return _png(pix)


# Извлекает изображение со страницы в данные PNG
def _img(page: pymupdf.Page, img_name: str) -> bytes:
    for item in page.get_images():
        xref, name = item[0], item[7]

        if name != img_name:
            continue

        pix = pymupdf.Pixmap(page.parent, xref)

        return _png(pix)

    raise FileNotFoundError("Изображение на странице не найдено.")


def _accrual(data: bytes, xy: tuple[int, int], *images: str):
    with pymupdf.open(stream=data) as doc:
        page = doc[0]
        width, height = page.rect.width, page.rect.height

        if height > width:
            # Только у счета на пени портретная ориентация.
            # Заполнен только в начале. Обрежем пополам.
            page.set_cropbox(pymupdf.Rect(0, 0, width, height / 2))

        return data, _page(page, xy), tuple(map(lambda x: _img(page, x), images))


def erkc_files(pdf: bytes, xy: tuple[int, int]) -> AccrualFiles:
    return AccrualFiles(*_accrual(pdf, xy, "img2", "img4"))


def peni_files(pdf: bytes, xy: tuple[int, int]) -> AccrualFiles:
    return AccrualFiles(*_accrual(pdf, xy, "img0"))
