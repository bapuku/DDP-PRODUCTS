"""
Property-based tests - GTIN validation, recycled content (Hypothesis).
"""
import re
import pytest
from hypothesis import given, strategies as st, assume

from app.models.dpp_base import gtin14_checksum, validate_gtin14


@given(st.integers(min_value=10**12, max_value=10**13 - 1))
def test_gtin13_to_14_roundtrip(n: int):
    s = str(n).zfill(13)
    assert len(s) == 13
    full = validate_gtin14(s)
    assert len(full) == 14
    assert full[:13] == s
    assert int(full[13]) == gtin14_checksum(s)


@given(st.text(alphabet="0123456789", min_size=14, max_size=14))
def test_valid_14_digit_checksum(s: str):
    assume(s[:13].isdigit())
    check = gtin14_checksum(s[:13])
    if int(s[13]) == check:
        assert validate_gtin14(s) == s


@given(st.floats(min_value=0, max_value=100), st.floats(min_value=0, max_value=100))
def test_recycled_content_sum_bounded(cobalt_pct: float, lithium_pct: float):
    assume(cobalt_pct + lithium_pct <= 100)
    from app.models.clusters import BatteryPassportCluster6
    c6 = BatteryPassportCluster6(
        pre_consumer_recycled_content_pct={"cobalt": cobalt_pct, "lithium": lithium_pct},
        post_consumer_recycled_content_pct={},
    )
    assert c6.pre_consumer_recycled_content_pct["cobalt"] == cobalt_pct
    assert c6.pre_consumer_recycled_content_pct["lithium"] == lithium_pct
