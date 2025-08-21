import asyncio
import io
from functools import partial
from importlib import resources
from typing import Dict, Literal, Tuple

import aiofiles
from PIL import Image as PILImage
from PIL.Image import Image, Palette
from pymupdf import Document, Identity, Matrix, Page, Pixmap

from .base import decimal, normalize

PdfSupported = Literal["erkc", "peni"]
QrSupported = Literal["erkc", "kapremont", "peni"]


async def read_logo() -> Image:
    png = resources.files("erkc63.images").joinpath("paid.png")

    async with aiofiles.open(str(png)) as f:
        return PILImage.open(f.buffer).convert("RGBA")


PAID_LOGO = asyncio.run(read_logo())

image_convert = partial(Image.convert, mode="P", palette=Palette.WEB)
"""Конвертирует изображение в 8-битное с палитрой `WEB`."""


def image_save(image: Image) -> bytes:
    """Сохраняет изображение в 8-битный оптимизированный `PNG` с палитрой `WEB`."""

    bio = io.BytesIO()
    image.save(bio, format="png", optimize=True)
    data = bio.getvalue()

    return data


def image_set_paid(image: Image, paid_scale: float) -> Image:
    """Ставит штамп `ОПЛАЧЕН` на изображении."""

    assert 0 < paid_scale <= 1

    image = image.convert("RGB")
    px = int(min(image.width, image.height) * paid_scale)
    box = (image.width - px) // 2, (image.height - px) // 2

    logo = PAID_LOGO.resize((px, px))
    image.paste(logo, box, logo)

    return image_convert(image)


def get_image_from_page(
    page: Page,
    image_name: str,
    max_rect: Tuple[int, int] = (3840, 2160),
) -> Image:
    """Извлекает изображение со страницы `PDF` в `Image`."""

    assert image_name

    for image in page.get_images():
        if image[7] == image_name:
            image = Pixmap(page.parent, image[0]).pil_image()
            image.thumbnail(max_rect)

            return image_convert(image)

    raise FileNotFoundError(f"Изображение '{image_name}' не найдено.")


def page_to_png(
    page: Page,
    max_rect: Tuple[int, int] = (3840, 2160),
) -> bytes:
    """
    Рендерит страницу `PDF` в `Image`.
    Размер изображения пропорционально вписывается в указанные ограничения, по-умолчанию 4К (3840 x 2160).
    """

    assert all(x > 0 for x in max_rect)

    factor: float = min(x / y for x, y in zip(max_rect, page.rect[2:]))
    matrix = Matrix(Identity).prescale(factor, factor)
    image: Image = page.get_pixmap(matrix=matrix).pil_image()  # type: ignore

    return image_save(image_convert(image))


class QrCodes:
    _pdf: Dict[PdfSupported, bytes]
    _qrcode: Dict[QrSupported, Image]
    _paid_scale: float

    def __init__(
        self,
        pdf_erkc: bytes | None,
        pdf_peni: bytes | None,
        *,
        max_rect: Tuple[int, int] = (3840, 2160),
        paid_scale: float = 0.65,
    ):
        assert 0 < paid_scale <= 1
        self._pdf, self._qrcode = {}, {}
        self._paid_scale = paid_scale

        if pdf_erkc:
            page = Document(stream=pdf_erkc)[0]
            self._pdf["erkc"] = page_to_png(page, max_rect)
            self._qrcode["erkc"] = get_image_from_page(page, "img2", max_rect)
            self._qrcode["kapremont"] = get_image_from_page(
                page, "img4", max_rect
            )

            # сумма начисления за капремонт
            dd = decimal(page.get_textbox((680, 460, 720, 470)))
            print(dd)

            # сумма начисления за капремонт
            dd = decimal(page.get_textbox((786, 460, 820, 470)))
            print(dd)

            # ЕЛС
            dd = normalize(page.get_textbox((375, 75, 420, 81)))
            print(dd)

            # к оплате
            dd = decimal(page.get_textbox((150, 165, 225, 177)))
            print(dd)

        if pdf_peni:
            page = Document(stream=pdf_peni)[0]
            self._pdf["peni"] = page_to_png(page, max_rect)
            self._qrcode["peni"] = get_image_from_page(page, "img0", max_rect)

    def qr(self, qr: QrSupported, *, paid: bool = False) -> bytes | None:
        if (image := self._qrcode.get(qr)) is None:
            return

        if paid:
            image = image_set_paid(image, self._paid_scale)

        return image_save(image)

    def qr_erkc(self, *, paid: bool = False) -> bytes | None:
        """QR-код оплаты коммунальных услуг."""

        return self.qr("erkc", paid=paid)

    def qr_kapremont(self, *, paid: bool = False) -> bytes | None:
        """QR-код оплаты капитального ремонта."""

        return self.qr("kapremont", paid=paid)

    def qr_peni(self, *, paid: bool = False) -> bytes | None:
        """QR-код оплаты пени."""

        return self.qr("peni", paid=paid)

    def pdf(self, pdf: PdfSupported) -> bytes | None:
        """Возвращает указанный счет в формате `PNG`."""

        return self._pdf.get(pdf)

    def pdf_erkc(self) -> bytes | None:
        """Счет основной в формате `PNG`."""

        return self.pdf("erkc")

    def pdf_peni(self) -> bytes | None:
        """Счет на пени в формате `PNG`."""

        return self.pdf("peni")
