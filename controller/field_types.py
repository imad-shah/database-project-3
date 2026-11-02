from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True, slots=True)
class FieldType:
    parse: Callable[[str], object]
    show: Callable[[Any], str] = str
    choices: tuple[str, ...] = ()


def _integer(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ValueError("must be a whole number.") from None


def _decimal(value: str) -> Decimal:
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ValueError("must be a number.") from None
    if not number.is_finite():
        raise ValueError("must be a number.")
    return number


def _money(value: str) -> Decimal:
    return _decimal(value.replace("$", "").replace(",", ""))


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("must be a date written as YYYY-MM-DD.") from None


def _yes_no(value: str) -> bool:
    answers = {"yes": True, "no": False}
    try:
        return answers[value.lower()]
    except KeyError:
        raise ValueError("must be Yes or No.") from None


def _yes_no_label(value: bool) -> str:
    return "Yes" if value else "No"


def _reference(value: str) -> int:
    return _integer(value.partition(" - ")[0])


TEXT = FieldType(parse=str)
UPPERCASE = FieldType(parse=str.upper)
INTEGER = FieldType(parse=_integer)
DECIMAL = FieldType(parse=_decimal)
MONEY = FieldType(parse=_money, show="${:,.2f}".format)
DATE = FieldType(parse=_date)
YES_NO = FieldType(parse=_yes_no, show=_yes_no_label, choices=("Yes", "No"))
REFERENCE = FieldType(parse=_reference)
