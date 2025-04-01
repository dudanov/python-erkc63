import io
from functools import partial
from importlib import resources
from typing import Literal

from PIL import Image as PILImage
from PIL.Image import Image, Palette
from pymupdf import Document, Identity, Matrix, Page, Pixmap

from .utils import str_normalize, to_decimal

QrSupported = Literal["erkc", "erkc_pdf", "kapremont", "peni", "peni_pdf"]

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


def get_image_from_pdfpage(page: Page, image_name: str) -> Image:
    """Извлекает изображение со страницы `PDF` в `Image`."""

    assert image_name

    for image in page.get_images():
        if image[7] == image_name:
            return image_convert(Pixmap(page.parent, image[0]).pil_image())

    raise FileNotFoundError("Image '%s' not found.", image_name)


def pdfpage_to_image(
    page: Page,
    max_rect: tuple[int, int] = (3840, 2160),
) -> Image:
    """
    Рендерит страницу `PDF` в `Image`.
    Размер изображения пропорционально вписывается в указанные ограничения, по-умолчанию 4К (3840 x 2160).
    """

    assert all(x > 0 for x in max_rect)

    factor: float = min(x / y for x, y in zip(max_rect, page.rect[2:]))
    matrix = Matrix(Identity).prescale(factor, factor)

    return image_convert(page.get_pixmap(matrix=matrix).pil_image())  # type: ignore


class QrCodes:
    _codes: dict[QrSupported, Image]
    _paid_scale: float

    def __init__(
        self,
        pdf_erkc: bytes | None,
        pdf_peni: bytes | None,
        *,
        paid_scale: float = 0.65,
    ) -> None:
        assert 0 < paid_scale <= 1

        self._codes = {}
        self._paid_scale = paid_scale

        if pdf_erkc:
            page = Document(stream=pdf_erkc)[0]
            self._codes["erkc_pdf"] = pdfpage_to_image(page)
            self._codes["erkc"] = get_image_from_pdfpage(page, "img2")
            self._codes["kapremont"] = get_image_from_pdfpage(page, "img4")

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
            self._codes["peni_pdf"] = pdfpage_to_image(page)
            self._codes["peni"] = get_image_from_pdfpage(page, "img0")

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

    def erkc(
        self, filename: str | None = None, *, paid: bool = False
    ) -> bytes | None:
        """QR-код оплаты коммунальных услуг."""

        return self.qr("erkc", filename, paid=paid)

    def kapremont(
        self, filename: str | None = None, *, paid: bool = False
    ) -> bytes | None:
        """QR-код оплаты капитального ремонта."""

        return self.qr("kapremont", filename, paid=paid)

    def peni(
        self, filename: str | None = None, *, paid: bool = False
    ) -> bytes | None:
        """QR-код оплаты пени."""

        return self.qr("peni", filename, paid=paid)
