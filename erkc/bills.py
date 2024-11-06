import io
from pathlib import Path
from typing import Literal

from PIL import Image
from pypdf import PageObject, PdfReader

QrSupported = Literal["erkc", "kapremont", "peni"]

assert __package__

_PAID_LOGO = Image.open(Path(__package__) / "paid.png").convert("RGBA")


def _paid_logo(size: float) -> Image.Image:
    img = _PAID_LOGO.copy()
    img.thumbnail((size, size), Image.Resampling.BICUBIC)

    return img


def _img_to_png(img: Image.Image) -> bytes:
    bio = io.BytesIO()
    img = img.convert("P", palette=Image.Palette.WEB)
    img.save(bio, format="png", optimize=True)

    return bio.getvalue()


def _img_paid(img_data: bytes, paid_scale: float) -> bytes:
    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    # Resize the logo to logo_max_size
    logo = _paid_logo(min(img.width, img.height) * paid_scale)
    # Calculate the center of the QR code
    box = (img.width - logo.width) // 2, (img.height - logo.height) // 2
    img.paste(logo, box, logo)

    return _img_to_png(img)


def _page_img(page: PageObject, name: str) -> bytes:
    for img in page.images:
        if img.name == name:
            return img.data

    raise FileNotFoundError("Image %s not found.", name)


class QrCodes:
    _codes: dict[QrSupported, bytes]
    _paid_scale: float

    def __init__(
        self,
        pdf_erkc: bytes | None,
        pdf_peni: bytes | None,
        paid_scale: float = 0.65,
    ) -> None:
        assert 0 < paid_scale <= 1

        self._paid_scale = paid_scale
        self._codes = {}

        if pdf_erkc:
            page = PdfReader(io.BytesIO(pdf_erkc)).pages[0]
            self._codes["erkc"] = _page_img(page, "img2.png")
            self._codes["kapremont"] = _page_img(page, "img4.png")

        if pdf_peni:
            page = PdfReader(io.BytesIO(pdf_peni)).pages[0]
            self._codes["peni"] = _page_img(page, "img0.png")

    def qr(self, qr: QrSupported, paid: bool = False) -> bytes | None:
        if img := self._codes.get(qr):
            return _img_paid(img, self._paid_scale) if paid else img

    def erkc(self, is_paid: bool = False) -> bytes | None:
        """QR-код оплаты коммунальных услуг."""

        return self.qr("erkc", is_paid)

    def kapremont(self, is_paid: bool = False) -> bytes | None:
        """QR-код оплаты капитального ремонта."""

        return self.qr("kapremont", is_paid)

    def peni(self, is_paid: bool = False) -> bytes | None:
        """QR-код оплаты пени."""

        return self.qr("peni", is_paid)
