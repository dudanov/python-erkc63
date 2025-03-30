import io
from functools import partial
from importlib import resources
from typing import Literal, overload

import pymupdf
from PIL import Image

from .utils import str_normalize, to_decimal

QrSupported = Literal["erkc", "kapremont", "peni"]

_PAID_LOGO = Image.open(
    resources.files().joinpath("images", "paid.png").open("rb")
).convert("RGBA")

_pil_to_png = partial(Image.Image.save, format="png", optimize=True)


def _paid_logo(size: float) -> Image.Image:
    img = _PAID_LOGO.copy()
    img.thumbnail((size, size), Image.Resampling.BICUBIC)

    return img


@overload
def _img_to_png(img: Image.Image) -> bytes: ...


@overload
def _img_to_png(img: Image.Image, file: io.BufferedWriter) -> None: ...


def _img_to_png(
    img: Image.Image, file: io.BufferedWriter | None = None
) -> bytes | None:
    img = img.convert("P", palette=Image.Palette.WEB)

    if file is None:
        _pil_to_png(img, bio := io.BytesIO())

        return bio.getvalue()

    _pil_to_png(img, file)


def _img_paid(img_data: bytes, paid_scale: float) -> bytes:
    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    # Resize the logo to logo_max_size
    logo = _paid_logo(min(img.width, img.height) * paid_scale)
    # Calculate the center of the QR code
    box = (img.width - logo.width) // 2, (img.height - logo.height) // 2
    img.paste(logo, box, logo)

    return _img_to_png(img)


def _doc_img(doc: pymupdf.Document, name: str) -> bytes:
    for x in doc.get_page_images(0):
        if x[7] == name:
            return pymupdf.Pixmap(doc, x[0]).tobytes()

    raise FileNotFoundError("Image %s not found.", name)


def _page_img(
    page: pymupdf.Page,
    max_width: int = 3840,
    max_height: int = 2160,
    filename: str | None = None,
) -> bytes | None:
    width, height = page.rect[2:]
    scale = min(max_width / width, max_height / height)
    matrix = pymupdf.Matrix(pymupdf.Identity).prescale(scale, scale)
    img: Image.Image = page.get_pixmap(matrix=matrix).pil_image()  # type: ignore

    if not filename:
        return _img_to_png(img)

    with open(filename, "wb") as file:
        _img_to_png(img, file)


class QrCodes:
    _codes: dict[QrSupported, bytes]
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
            doc = pymupdf.Document(stream=pdf_erkc)
            self._codes["erkc"] = _doc_img(doc, "img2")
            self._codes["kapremont"] = _doc_img(doc, "img4")
            page = doc[0]
            with open("pdf.pdf", "wb") as f:
                f.write(pdf_erkc)

            _page_img(page, filename="pdf.png")

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
            doc = pymupdf.Document(stream=pdf_peni)
            self._codes["peni"] = _doc_img(doc, "img0")

    def qr(self, qr: QrSupported, *, paid: bool = False) -> bytes | None:
        if img := self._codes.get(qr):
            return _img_paid(img, self._paid_scale) if paid else img

    def erkc(self, *, paid: bool = False) -> bytes | None:
        """QR-код оплаты коммунальных услуг."""

        return self.qr("erkc", paid=paid)

    def kapremont(self, *, paid: bool = False) -> bytes | None:
        """QR-код оплаты капитального ремонта."""

        return self.qr("kapremont", paid=paid)

    def peni(self, *, paid: bool = False) -> bytes | None:
        """QR-код оплаты пени."""

        return self.qr("peni", paid=paid)
