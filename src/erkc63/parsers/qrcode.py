import io
from typing import Literal

import pymupdf
from PIL import Image

type PilImage = Image.Image

type PdfSupported = Literal["erkc", "peni"]
type QrSupported = Literal["erkc", "kapremont", "peni"]


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


def pdf_img_to_png(
    page: pymupdf.Page, img_name: str, max_rect: tuple[int, int]
) -> bytes:
    """Извлекает изображение со страницы `PDF` в `Image`."""

    if not img_name:
        raise ValueError("Имя изображения не может быть пустой строкой.")

    for img_info in page.get_images():
        xref, name = img_info[0], img_info[7]

        if name != img_name:
            continue

        pix = pymupdf.Pixmap(page.parent, xref)

        return pix_save(pix, max_rect)

    raise FileNotFoundError(f"Изображение '{img_name}' не найдено.")


def pdf_page_to_png(page: pymupdf.Page, max_rect: tuple[int, int]) -> bytes:
    """
    Рендерит страницу `PDF` в `Image`.
    Размер изображения пропорционально вписывается в указанные ограничения, по умолчанию 4К (3840 x 2160).
    """

    factor = min(x / y for x, y in zip(max_rect, page.rect[2:]))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(factor, factor))

    return pix_save(pix, max_rect)


class QrCodes:
    _pdf_data: dict[PdfSupported, bytes]
    _qr_png: dict[QrSupported, bytes]

    def __init__(
        self,
        pdf_erkc: bytes | None,
        pdf_peni: bytes | None,
        *,
        max_rect: tuple[int, int] = (3840, 2160),
    ):
        if not all(x > 0 for x in max_rect):
            raise ValueError("Ограничения max_rect должны быть больше нуля.")

        self._pdf_data = {}
        self._qr_png = {}

        if pdf_erkc:
            page = pymupdf.Document(stream=pdf_erkc)[0]
            self._pdf_data["erkc"] = pdf_page_to_png(page, max_rect)
            self._qr_png["erkc"] = pdf_img_to_png(page, "img2", max_rect)
            self._qr_png["kapremont"] = pdf_img_to_png(page, "img4", max_rect)

        if pdf_peni:
            page = pymupdf.Document(stream=pdf_peni)[0]
            self._pdf_data["peni"] = pdf_page_to_png(page, max_rect)
            self._qr_png["peni"] = pdf_img_to_png(page, "img0", max_rect)

    def _qr(self, qr: QrSupported) -> bytes | None:
        return self._qr_png.get(qr)

    def _pdf(self, pdf: PdfSupported) -> bytes | None:
        """Возвращает указанный счет в формате `PNG`."""

        return self._pdf_data.get(pdf)

    @property
    def qr_erkc(self) -> bytes | None:
        """QR-код оплаты коммунальных услуг."""

        return self._qr("erkc")

    @property
    def qr_kapremont(self) -> bytes | None:
        """QR-код оплаты капитального ремонта."""

        return self._qr("kapremont")

    @property
    def qr_peni(self) -> bytes | None:
        """QR-код оплаты пени."""

        return self._qr("peni")

    @property
    def pdf_erkc(self) -> bytes | None:
        """Счет основной в формате `PNG`."""

        return self._pdf("erkc")

    @property
    def pdf_peni(self) -> bytes | None:
        """Счет на пени в формате `PNG`."""

        return self._pdf("peni")
