import pytest
from app.discount_service import calculate_discounted_price


def test_discount_calculation():
    # 100 with 20% discount should be 80.0, NOT 120.0
    assert calculate_discounted_price(100.0, 0.20) == 80.0
    assert calculate_discounted_price(50.0, 0.50) == 25.0


def test_zero_discount():
    assert calculate_discounted_price(100.0, 0.0) == 100.0


def test_invalid_price():
    with pytest.raises(ValueError):
        calculate_discounted_price(-10.0, 0.1)

