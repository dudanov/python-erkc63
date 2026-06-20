import asyncio
import dataclasses as dc
import io

import pymupdf
from PIL import Image

type PilImage = Image.Image


@dc.dataclass(slots=True)
class ErkcImages:
    """Изображения счета ЕРКЦ"""

    source: bytes
    """Исходный PDF"""
    page: bytes
    """Страница счета"""
    code: bytes
    """Основной QR-код"""
    kap_code: bytes
    """QR-код капремонта"""


@dc.dataclass(slots=True)
class PeniImages:
    """Изображения счета пени"""

    source: bytes
    """Исходный PDF"""
    page: bytes
    """Страница счета"""
    code: bytes
    """Основной QR-код"""


# Сохраняет Pixmap в 8-битный оптимизированный PNG в палитре WEB
def _png(pix: pymupdf.Pixmap, rect: tuple[int, int]) -> bytes:
    bio = io.BytesIO()

    img = pix.pil_image()
    img.thumbnail(rect)
    img = img.convert(mode="P", palette=Image.Palette.WEB)
    img.save(bio, format="png", optimize=True)

    return bio.getvalue()


# Рендерит страницу в данные PNG вписывающегося в указанное разрешение
def _page(page: pymupdf.Page, rect: tuple[int, int]) -> bytes:
    factor = min(x / y for x, y in zip(rect, page.rect[2:]))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(factor, factor))

    return _png(pix, rect)


# Извлекает изображение со страницы в данные PNG
def _img(page: pymupdf.Page, rect: tuple[int, int], name: str) -> bytes:
    for item in page.get_images():
        img_xref, img_name = item[0], item[7]

        if img_name != name:
            continue

        pix = pymupdf.Pixmap(page.parent, img_xref)

        return _png(pix, rect)

    raise FileNotFoundError("Изображение на странице не найдено.")


def _accrual(data: bytes, rect: tuple[int, int], *images: str) -> list[bytes]:
    if not all(x > 0 for x in rect):
        raise ValueError("Ограничения должны быть больше нуля.")

    def _items():
        with pymupdf.open(stream=data) as doc:
            page = doc[0]
            width, height = page.rect[2:]

            if height > width:
                # Только у счета на пени портретная ориентация.
                # Заполнен только в начале. Обрежем пополам.
                page.set_cropbox(pymupdf.Rect(0, 0, width, height / 2))

            yield _page(page, rect)

            for name in images:
                yield _img(page, rect, name)

    return list(_items())


async def erkc_images(data: bytes, rect: tuple[int, int]) -> ErkcImages:
    return ErkcImages(
        data, *await asyncio.to_thread(_accrual, data, rect, "img2", "img4")
    )


async def peni_images(data: bytes, rect: tuple[int, int]) -> PeniImages:
    return PeniImages(
        data, *await asyncio.to_thread(_accrual, data, rect, "img0")
    )
