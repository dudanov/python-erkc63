import dataclasses as dc
import io

import pymupdf
from PIL import Image

type PilImage = Image.Image


@dc.dataclass(slots=True)
class AccrualImages:
    page: bytes
    codes: list[bytes]


def pix_save(pix: pymupdf.Pixmap, max_rect: tuple[int, int]) -> bytes:
    """Сохраняет Pixmap в 8-битный оптимизированный `PNG` с палитрой `WEB`."""

    try:
        img = pix.pil_image()
        img = img.copy()

    finally:
        pix = None  # type: ignore[assignment]

    bio = io.BytesIO()

    img.thumbnail(max_rect)
    img = img.convert(mode="P", palette=Image.Palette.WEB)
    img.save(bio, format="png", optimize=True)

    return bio.getvalue()


def qr_png(
    page: pymupdf.Page,
    img_name: str,
    max_rect: tuple[int, int],
) -> bytes:
    """Извлекает изображение со страницы `PDF` в данные `PNG` формата."""

    if not img_name:
        raise ValueError("Имя изображения не может быть пустой строкой.")

    for img_info in page.get_images():
        xref, name = img_info[0], img_info[7]

        if name != img_name:
            continue

        pix = pymupdf.Pixmap(page.parent, xref)

        return pix_save(pix, max_rect)

    raise FileNotFoundError("QR код на странице PDF не найден.")


def page_png(page: pymupdf.Page, max_rect: tuple[int, int]) -> bytes:
    """
    Рендерит страницу `PDF` в данные изображения `PNG` формата.
    Итоговый размер пропорционально вписывается в указанные ограничения, по умолчанию 4К (3840 x 2160).
    """

    factor = min(x / y for x, y in zip(max_rect, page.rect[2:]))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(factor, factor))

    return pix_save(pix, max_rect)


# 'img2', 'img4' - основной счет
# 'img0' - счет пени
def accrual_images(
    data: bytes | None,
    images: list[str],
    max_rect: tuple[int, int] = (3840, 2160),
):
    if not data:
        return

    if not all(x > 0 for x in max_rect):
        raise ValueError("Ограничения max_rect должны быть больше нуля.")

    with pymupdf.open(stream=data) as doc:
        page = doc[0]

        return AccrualImages(
            page=page_png(page, max_rect),
            codes=[qr_png(page, x, max_rect) for x in images],
        )
