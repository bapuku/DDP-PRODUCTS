"""
Unit tests - Data carriers service: GS1 Digital Link, SGTIN-96, QR, NFC.
"""
import pytest

from app.services.data_carriers import (
    gs1_digital_link,
    sgtin96_hex,
    nfc_ndef_uri,
    qr_data,
    carrier_payload,
)


def test_gs1_digital_link():
    url = gs1_digital_link("01234567890123", "SN001", "https://dpp.example.eu")
    assert "01/" in url
    assert "21/" in url
    assert "01234567890123" in url or "12345678901230" in url
    assert "SN001" in url


def test_sgtin96_hex():
    hex_val = sgtin96_hex("01234567890123", "1")
    assert isinstance(hex_val, str)
    assert len(hex_val) == 24
    assert all(c in "0123456789abcdef" for c in hex_val)


def test_nfc_ndef_uri():
    uri = nfc_ndef_uri("01234567890123", "SN001")
    assert uri.startswith("https://") or "01/" in uri


def test_qr_data():
    data = qr_data("01234567890123", "SN001")
    assert "01/" in data and "21/" in data


def test_carrier_payload():
    payload = carrier_payload("01234567890123", "SN001")
    assert "qr_data" in payload
    assert "gs1_digital_link" in payload
    assert "nfc_ndef_uri" in payload
    assert "rfid_epc_sgtin96" in payload
    assert len(payload["rfid_epc_sgtin96"]) == 24
