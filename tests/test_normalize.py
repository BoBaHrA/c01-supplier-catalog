from decimal import Decimal

from c01.normalize import parse_decimal, parse_packaging, parse_stock


def test_decimal_comma_and_currency():
    assert parse_decimal(" 19,95 € ", ["€", "EUR"]) == (Decimal("19.95"), False)


def test_decimal_bad_character_is_error():
    assert parse_decimal("12,5O", ["€"]) == (None, True)


def test_stock_zero_is_not_blank():
    assert parse_stock("0") == (0, False)
    assert parse_stock("") == (None, False)


def test_packaging_equivalent_units():
    units = {"piece": ["pc", "pcs"], "g": ["g"], "kg": ["kg"], "ml": ["ml"], "l": ["l"]}
    assert parse_packaging("500 g", units) == (Decimal("500"), "g", False)
    assert parse_packaging("0,5 kg", units) == (Decimal("500.0"), "g", False)
