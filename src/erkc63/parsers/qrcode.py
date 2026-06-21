import dataclasses as dc
import io
from typing import Self

import pymupdf
from PIL import Image

type PilImage = Image.Image


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


@dc.dataclass(slots=True, frozen=True)
class AccrualData:
    """Данные счета"""

    source: bytes
    """Исходный PDF"""
    page: bytes
    """PNG изображение страницы счета"""
    qrs: tuple[bytes, ...]
    """PNG изображения QR-кодов оплаты счета"""

    @classmethod
    def from_data(cls, pdf: bytes, xy: tuple[int, int], *images: str) -> Self:
        with pymupdf.open(stream=pdf) as doc:
            page = doc[0]
            width, height = page.rect.width, page.rect.height

            if height > width:
                # Только у счета на пени портретная ориентация.
                # Заполнен только в начале. Обрежем пополам.
                page.set_cropbox(pymupdf.Rect(0, 0, width, height / 2))

            return cls(
                source=pdf,
                page=_page(page, xy),
                qrs=tuple(map(lambda x: _img(page, x), images)),
            )

    @classmethod
    def from_erkc_data(cls, pdf: bytes, xy: tuple[int, int]) -> Self:
        return cls.from_data(pdf, xy, "img2", "img4")

    @classmethod
    def from_peni_data(cls, pdf: bytes, xy: tuple[int, int]) -> Self:
        return cls.from_data(pdf, xy, "img0")
