from datetime import date
from decimal import Decimal

import pytest

from controller import AppError, Field, Option
from controller.field_types import (
    DATE,
    DECIMAL,
    INTEGER,
    MONEY,
    REFERENCE,
    UPPERCASE,
    YES_NO,
)
from controller.fields import reference


@pytest.mark.parametrize(
    ("field_type", "raw", "expected"),
    [
        (INTEGER, "12", 12),
        (DECIMAL, "2.5", Decimal("2.5")),
        (MONEY, "$1,250,000.50", Decimal("1250000.50")),
        (MONEY, "200000", Decimal(200000)),
        (DATE, "2004-06-18", date(2004, 6, 18)),
        (YES_NO, "yes", True),
        (YES_NO, "No", False),
        (UPPERCASE, "pa", "PA"),
        (REFERENCE, "7 - Dana Reyes", 7),
        (REFERENCE, "7", 7),
    ],
)
def test_parses_valid_input(field_type, raw, expected):
    assert Field("x", "X", field_type).parse(raw) == expected


@pytest.mark.parametrize(
    ("field_type", "raw", "message"),
    [
        (INTEGER, "four", "Size must be a whole number."),
        (DECIMAL, "abc", "Size must be a number."),
        (MONEY, "NaN", "Size must be a number."),
        (MONEY, "Infinity", "Size must be a number."),
        (DATE, "06/18/2004", "Size must be a date written as YYYY-MM-DD."),
        (YES_NO, "maybe", "Size must be Yes or No."),
        (REFERENCE, "Dana Reyes", "Size must be a whole number."),
    ],
)
def test_rejects_invalid_input(field_type, raw, message):
    with pytest.raises(AppError) as error:
        Field("x", "Size", field_type).parse(raw)
    assert str(error.value) == message


def test_blank_required_field_is_rejected():
    with pytest.raises(AppError, match="Name is required."):
        Field("x", "Name", required=True).parse("   ")


def test_blank_optional_field_is_none():
    assert Field("x", "Name").parse("   ") is None


def test_text_is_stripped():
    assert Field("x", "Name").parse("  Dana ") == "Dana"


def test_formatter_resolves_reference_labels():
    field = reference("agent_id", "Agent", lambda: [Option(3, "Dana Reyes")])
    render = field.formatter()
    assert render(3) == "3 - Dana Reyes"
    assert render(None) == ""


def test_formatted_money_parses_back():
    field = Field("x", "Price", MONEY)
    value = Decimal("1250000.50")
    assert field.parse(field.formatter()(value)) == value


def test_optional_reference_offers_a_blank_choice():
    field = reference("a", "Agent", lambda: [Option(1, "A")], required=False)
    assert field.choices() == ["", "1 - A"]


def test_selectable_narrows_choices_but_not_labels():
    field = reference(
        "p",
        "Property",
        lambda: [Option(1, "Sold"), Option(2, "Open")],
        selectable=lambda: [Option(2, "Open")],
    )
    assert field.choices() == ["2 - Open"]
    assert field.formatter()(1) == "1 - Sold"


def test_initial_prefers_default_then_first_required_choice():
    assert Field("x", "Pool", YES_NO, required=True, default="No").initial() == "No"
    field = reference("b", "Buyer", lambda: [Option(4, "Omar")])
    assert field.initial() == "4 - Omar"
    assert Field("x", "City").initial() == ""
