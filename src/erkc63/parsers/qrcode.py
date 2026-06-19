import dataclasses as dc
import io
import itertools as it
from typing import Final

import pymupdf
from PIL import Image

type PilImage = Image.Image

QR_ERKC: Final = ("img2", "img4")
QR_PENI: Final = ("img0",)


@dc.dataclass(slots=True)
class AccrualImages:
    page: bytes
    codes: list[bytes]


# Сохраняет Pixmap в 8-битный оптимизированный PNG в палитре WEB
def _png(pix: pymupdf.Pixmap, rect: tuple[int, int]) -> bytes:
    bio = io.BytesIO()

    img = pix.pil_image()
    img.thumbnail(rect)
    img = img.convert(mode="P", palette=Image.Palette.WEB)
    img.save(bio, format="png", optimize=True)

    return bio.getvalue()


# Извлекает изображение со страницы в данные PNG
def _img(page: pymupdf.Page, rect: tuple[int, int], name: str) -> bytes:
    for item in page.get_images():
        img_xref, img_name = item[0], item[7]

        if img_name != name:
            continue

        pix = pymupdf.Pixmap(page.parent, img_xref)

        return _png(pix, rect)

    raise FileNotFoundError("Изображение на странице не найдено.")


# Рендерит страницу в данные PNG вписывающегося в указанное разрешение
def _page(page: pymupdf.Page, rect: tuple[int, int]) -> bytes:
    factor = min(x / y for x, y in zip(rect, page.rect[2:]))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(factor, factor))

    return _png(pix, rect)


def accrual_images(
    data: bytes | None,
    rect: tuple[int, int],
    images: tuple[str, ...],
) -> tuple[bytes, ...]:
    with pymupdf.open(stream=data) as doc:
        page = doc[0]

        return _page(page, rect), *map(lambda x: _img(page, rect, x), images)


def erkc_images(
    data: bytes | None, rect: tuple[int, int]
) -> AccrualImages | None:
    if not all(x > 0 for x in rect):
        raise ValueError("Ограничения max_rect должны быть больше нуля.")

    return accrual_images(data, rect, QR_ERKC)


def peni_images(
    data: bytes | None, rect: tuple[int, int]
) -> AccrualImages | None:
    return accrual_images(data, rect, QR_PENI)
