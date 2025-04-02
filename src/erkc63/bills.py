import io
from functools import partial
from importlib import resources
from typing import Literal

from PIL import Image as PILImage
from PIL.Image import Image, Palette
from pymupdf import Document, Identity, Matrix, Page, Pixmap

from .utils import str_normalize, to_decimal

PdfSupported = Literal["erkc", "peni"]
QrSupported = Literal["erkc", "kapremont", "peni"]

_PAID_LOGO = PILImage.open(
    resources.files().joinpath("images", "paid.png").open("rb")
).convert("RGBA")
"""Изображение штампа `ОПЛАЧЕН` с альфа-каналом."""

image_convert = partial(Image.convert, mode="P", palette=Palette.WEB)
"""Конвертирует изображение в 8-битное с палитрой `WEB`."""


def image_save(image: Image, filename: str | None = None) -> bytes:
    """Сохраняет изображение в 8-битный оптимизированный `PNG` с палитрой `WEB`."""

    bio = io.BytesIO()
    image.save(bio, format="png", optimize=True)
    data = bio.getvalue()

    if filename:
        with open(filename, "wb") as file:
            file.write(data)

    return data


def image_set_paid(image: Image, paid_scale: float) -> Image:
    """Ставит штамп `ОПЛАЧЕН` на изображении."""

    assert 0 < paid_scale <= 1

    image = image.convert("RGB")
    px = int(min(image.width, image.height) * paid_scale)
    box = (image.width - px) // 2, (image.height - px) // 2

    logo = _PAID_LOGO.resize((px, px))
    image.paste(logo, box, logo)

    return image_convert(image)


def get_image_from_pdfpage(
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

    raise FileNotFoundError("Image '%s' not found.", image_name)


def pdfpage_to_png(
    page: Page,
    max_rect: tuple[int, int] = (3840, 2160),
    filename: str | None = None,
) -> bytes:
    """
    Рендерит страницу `PDF` в `Image`.
    Размер изображения пропорционально вписывается в указанные ограничения, по-умолчанию 4К (3840 x 2160).
    """

    assert all(x > 0 for x in max_rect)

    factor: float = min(x / y for x, y in zip(max_rect, page.rect[2:]))
    matrix = Matrix(Identity).prescale(factor, factor)
    image: Image = page.get_pixmap(matrix=matrix).pil_image()  # type: ignore

    return image_save(image_convert(image), filename)


class QrCodes:
    _codes: dict[QrSupported, Image]
    _paid_scale: float
    _pdf: dict[PdfSupported, bytes]

    def __init__(
        self,
        pdf_erkc: bytes | None,
        pdf_peni: bytes | None,
        *,
        max_rect: tuple[int, int] = (3840, 2160),
        paid_scale: float = 0.65,
    ) -> None:
        assert 0 < paid_scale <= 1

        self._codes = {}
        self._paid_scale = paid_scale

        if pdf_erkc:
            page = Document(stream=pdf_erkc)[0]
            self._pdf["erkc"] = pdfpage_to_png(page, max_rect)
            self._codes["erkc"] = get_image_from_pdfpage(page, "img2", max_rect)
            self._codes["kapremont"] = get_image_from_pdfpage(
                page, "img4", max_rect
            )

            dd = to_decimal(
                page.get_textbox((680, 460, 720, 470))
            )  # сумма начисления за капремонт
            print(dd)

            dd = to_decimal(
                page.get_textbox((786, 460, 820, 470))
            )  # сумма начисления за капремонт
            print(dd)

            dd = str_normalize(page.get_textbox((375, 75, 420, 81)))  # ЕЛС
            print(dd)

            dd = to_decimal(page.get_textbox((150, 165, 225, 177)))  # к оплате
            print(dd)

        if pdf_peni:
            page = Document(stream=pdf_peni)[0]
            self._pdf["peni"] = pdfpage_to_png(page, max_rect)
            self._codes["peni"] = get_image_from_pdfpage(page, "img0", max_rect)

    def qr(
        self,
        qr: QrSupported,
        filename: str | None = None,
        *,
        paid: bool = False,
    ) -> bytes | None:
        if (image := self._codes.get(qr)) is None:
            return

        if paid:
            image = image_set_paid(image, self._paid_scale)

        return image_save(image, filename)

    def qr_erkc(
        self,
        filename: str | None = None,
        *,
        paid: bool = False,
    ) -> bytes | None:
        """QR-код оплаты коммунальных услуг."""

        return self.qr("erkc", filename, paid=paid)

    def qr_kapremont(
        self,
        filename: str | None = None,
        *,
        paid: bool = False,
    ) -> bytes | None:
        """QR-код оплаты капитального ремонта."""

        return self.qr("kapremont", filename, paid=paid)

    def qr_peni(
        self,
        filename: str | None = None,
        *,
        paid: bool = False,
    ) -> bytes | None:
        """QR-код оплаты пени."""

        return self.qr("peni", filename, paid=paid)

    def pdf(
        self,
        pdf: PdfSupported,
        filename: str | None = None,
    ) -> bytes | None:
        """Возвращает указанный счет в формате `PNG`."""

        if (data := self._pdf.get(pdf)) and filename:
            with open(filename, "wb") as file:
                file.write(data)

        return data

    def pdf_erkc(self, filename: str | None = None) -> bytes | None:
        """Счет основной в формате `PNG`."""

        return self.pdf("erkc", filename)

    def pdf_peni(self, filename: str | None = None) -> bytes | None:
        """Счет на пени в формате `PNG`."""

        return self.pdf("peni", filename)
