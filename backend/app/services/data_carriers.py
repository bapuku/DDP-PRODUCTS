"""
Data carriers service - QR (PNG/SVG), NFC NDEF payload, RFID SGTIN-96 (GS1 EPC).
ESPR / Battery Reg data carrier requirements.
"""
from typing import Any

import structlog

log = structlog.get_logger()


def gs1_digital_link(gtin: str, serial: str, base_url: str = "https://dpp.example.eu") -> str:
    """Build GS1 Digital Link URI (e.g. https://dpp.example.eu/01/01234567890123/21/SN123)."""
    g = "".join(c for c in str(gtin) if c.isdigit()).zfill(14)
    return f"{base_url.rstrip('/')}/01/{g}/21/{serial or ''}"


def sgtin96_hex(gtin: str, serial: str) -> str:
    """Encode GTIN-14 + serial as EPC SGTIN-96 hex string (24 hex chars)."""
    g = "".join(c for c in str(gtin) if c.isdigit()).zfill(14)
    ser = str(serial or "").zfill(7)[:7]
    try:
        company = int(g[:7].lstrip("0") or "0")
        item = int(g[7:14])
        serial_int = int(ser) if ser.isdigit() else hash(ser) % (2**38)
    except (ValueError, TypeError):
        company, item, serial_int = 0, 0, 0
    val = (1 << 88) | (company << 41) | (item << 17) | serial_int
    return hex(val)[2:].zfill(24)


def nfc_ndef_uri(gtin: str, serial: str, base_url: str = "https://dpp.example.eu") -> str:
    """NFC NDEF URI record payload (URN or HTTPS)."""
    return gs1_digital_link(gtin, serial, base_url)


def qr_data(gtin: str, serial: str, base_url: str = "https://dpp.example.eu") -> str:
    """QR code data string (same as Digital Link)."""
    return gs1_digital_link(gtin, serial, base_url)


def generate_qr_png(data: str, size: int = 5, border: int = 2) -> bytes:
    """Generate QR code as PNG bytes. Requires qrcode[pil]."""
    try:
        import qrcode
        img = qrcode.make(data, version=1, box_size=size, border=border)
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        log.warning("qrcode_not_available")
        return b""


def generate_qr_svg(data: str, size: int = 128) -> str:
    """Generate QR code as SVG string. Requires qrcode."""
    try:
        import qrcode
        import qrcode.image.svg
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(data, image_factory=factory)
        return img.to_string().decode("utf-8") if hasattr(img, "to_string") else ""
    except (ImportError, AttributeError) as e:
        log.warning("qrcode_svg_unavailable", error=str(e))
        return ""


def carrier_payload(gtin: str, serial: str, base_url: str = "https://dpp.example.eu") -> dict[str, Any]:
    """Return full carrier payload: qr_data, qr_png_base64, qr_svg, nfc_ndef_uri, rfid_epc_sgtin96."""
    data = qr_data(gtin, serial, base_url)
    png_b64 = ""
    png_bytes = generate_qr_png(data)
    if png_bytes:
        import base64
        png_b64 = base64.standard_b64encode(png_bytes).decode("ascii")
    svg = generate_qr_svg(data)
    return {
        "qr_data": data,
        "gs1_digital_link": data,
        "qr_png_base64": png_b64,
        "qr_svg": svg,
        "nfc_ndef_uri": nfc_ndef_uri(gtin, serial, base_url),
        "rfid_epc_sgtin96": sgtin96_hex(gtin, serial),
    }
