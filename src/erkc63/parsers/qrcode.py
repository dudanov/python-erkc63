import io
from functools import partial
from typing import Literal

from PIL.Image import Image, Palette
from pymupdf import Document, Identity, Matrix, Page, Pixmap

from .base import normalize, str_decimal

PdfSupported = Literal["erkc", "peni"]
QrSupported = Literal["erkc", "kapremont", "peni"]


image_convert = partial(Image.convert, mode="P", palette=Palette.WEB)
"""Конвертирует изображение в 8-битное с палитрой `WEB`."""


def image_save(image: Image) -> bytes:
    """Сохраняет изображение в 8-битный оптимизированный `PNG` с палитрой `WEB`."""

    bio = io.BytesIO()
    image.save(bio, format="png", optimize=True)
    data = bio.getvalue()

    return data


def get_image_from_page(
    page: Page,
    image_name: str,
    max_rect: tuple[int, int] = (3840, 2160),
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
    max_rect: tuple[int, int] = (3840, 2160),
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
    _pdf: dict[PdfSupported, bytes]
    _qrcode: dict[QrSupported, Image]

    def __init__(
        self,
        pdf_erkc: bytes | None,
        pdf_peni: bytes | None,
        *,
        max_rect: tuple[int, int] = (3840, 2160),
    ):
        self._pdf, self._qrcode = {}, {}

        if pdf_erkc:
            page = Document(stream=pdf_erkc)[0]
            self._pdf["erkc"] = page_to_png(page, max_rect)
            self._qrcode["erkc"] = get_image_from_page(page, "img2", max_rect)
            self._qrcode["kapremont"] = get_image_from_page(
                page, "img4", max_rect
            )

            # сумма начисления за капремонт
            dd = str_decimal(page.get_textbox((680, 460, 720, 470)))
            print(dd)

            # сумма начисления за капремонт
            dd = str_decimal(page.get_textbox((786, 460, 820, 470)))
            print(dd)

            # ЕЛС
            dd = normalize(page.get_textbox((375, 75, 420, 81)))
            print(dd)

            # к оплате
            dd = str_decimal(page.get_textbox((150, 165, 225, 177)))
            print(dd)

        if pdf_peni:
            page = Document(stream=pdf_peni)[0]
            self._pdf["peni"] = page_to_png(page, max_rect)
            self._qrcode["peni"] = get_image_from_page(page, "img0", max_rect)

    def qr(self, qr: QrSupported) -> bytes | None:
        if (image := self._qrcode.get(qr)) is None:
            return

        return image_save(image)

    def qr_erkc(self) -> bytes | None:
        """QR-код оплаты коммунальных услуг."""

        return self.qr("erkc")

    def qr_kapremont(self) -> bytes | None:
        """QR-код оплаты капитального ремонта."""

        return self.qr("kapremont")

    def qr_peni(self) -> bytes | None:
        """QR-код оплаты пени."""

        return self.qr("peni")

    def pdf(self, pdf: PdfSupported) -> bytes | None:
        """Возвращает указанный счет в формате `PNG`."""

        return self._pdf.get(pdf)

    def pdf_erkc(self) -> bytes | None:
        """Счет основной в формате `PNG`."""

        return self.pdf("erkc")

    def pdf_peni(self) -> bytes | None:
        """Счет на пени в формате `PNG`."""

        return self.pdf("peni")
