import io
from importlib import resources
from typing import Literal

import pymupdf
from PIL import Image

QrSupported = Literal["erkc", "kapremont", "peni"]

_PAID_LOGO = Image.open(
    resources.files().joinpath("images", "paid.png").open("rb")
).convert("RGBA")


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


def _page_img(doc: pymupdf.Document, name: str) -> bytes:
    for img in doc.get_page_images(0):
        if img[7] == name:
            return pymupdf.Pixmap(doc, img[0]).tobytes()

    raise FileNotFoundError("Image %s not found.", name)


class QrCodes:
    _codes: dict[QrSupported, bytes]
    _paid_scale: float

    def __init__(
        self,
        pdf_erkc: bytes,
        pdf_peni: bytes,
        *,
        paid_scale: float = 0.65,
    ) -> None:
        assert 0 < paid_scale <= 1

        self._codes = {}
        self._paid_scale = paid_scale

        if pdf_erkc:
            page = pymupdf.Document(stream=pdf_erkc)
            self._codes["erkc"] = _page_img(page, "img2")
            self._codes["kapremont"] = _page_img(page, "img4")

        if pdf_peni:
            page = pymupdf.Document(stream=pdf_peni)
            self._codes["peni"] = _page_img(page, "img0")

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
