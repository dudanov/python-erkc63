import dataclasses as dc
import io

import pymupdf
from PIL import Image

type PilImage = Image.Image


@dc.dataclass(slots=True)
class AccrualImages:
    page: bytes
    codes: list[bytes]


def pix_save(pix: pymupdf.Pixmap, rect: tuple[int, int]) -> bytes:
    """Сохраняет Pixmap в 8-битный оптимизированный `PNG` с палитрой `WEB`."""

    bio = io.BytesIO()

    img = pix.pil_image()
    img.thumbnail(rect)
    img = img.convert(mode="P", palette=Image.Palette.WEB)
    img.save(bio, format="png", optimize=True)

    return bio.getvalue()


def img_png(page: pymupdf.Page, name: str, rect: tuple[int, int]) -> bytes:
    """Извлекает изображение со страницы `PDF` в данные `PNG` формата."""

    for item in page.get_images():
        img_xref, img_name = item[0], item[7]

        if img_name != name:
            continue

        pix = pymupdf.Pixmap(page.parent, img_xref)

        return pix_save(pix, rect)

    raise FileNotFoundError("Изображение на странице не найдено.")


def page_png(page: pymupdf.Page, rect: tuple[int, int]) -> bytes:
    """
    Рендерит страницу `PDF` в данные изображения `PNG` формата.
    Итоговый размер пропорционально вписывается в указанные ограничения, по умолчанию 4К (3840 x 2160).
    """

    factor = min(x / y for x, y in zip(rect, page.rect[2:]))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(factor, factor))

    return pix_save(pix, rect)


# 'img2', 'img4' - основной счет
# 'img0' - счет пени
def accrual_images(
    data: bytes | None,
    images: list[str],
    rect: tuple[int, int] = (3840, 2160),
):
    if not data:
        return

    if not all(x > 0 for x in rect):
        raise ValueError("Ограничения max_rect должны быть больше нуля.")

    with pymupdf.open(stream=data) as doc:
        page = doc[0]

        return AccrualImages(
            page=page_png(page, rect),
            codes=[img_png(page, x, rect) for x in images],
        )
