from collections.abc import Iterator
from contextlib import contextmanager

import psycopg

from repository import RecordNotFound

LINKED_RECORDS = (
    "This record is linked to other records. Remove or reassign those first."
)

CONSTRAINT_MESSAGES = {
    "agents_email_unique": "Another agent already uses that email.",
    "agents_license_unique": "Another agent already has that license number.",
    "buyers_budget_positive": "Maximum budget must be greater than zero.",
    "buyers_bedrooms_valid": "Minimum bedrooms can't be negative.",
    "properties_address_unique": "A property with that address already exists.",
    "properties_state_format": "State must be a two-letter code, such as PA.",
    "properties_zip_format": "ZIP code must look like 18015 or 18015-1234.",
    "properties_bedrooms_valid": "Bedrooms can't be negative.",
    "properties_bathrooms_valid": "Bathrooms can't be negative.",
    "properties_square_feet_positive": "Square feet must be greater than zero.",
    "properties_year_built_valid": "Year built must be between 1600 and 2100.",
    "listings_price_positive": "Asking price must be greater than zero.",
    "listings_after_prior_sale": (
        "A home can't be relisted before its previous sale date."
    ),
    "listings_property_fixed": "A listing can't be moved to a different property.",
    "listings_one_active": (
        "That property already has an active listing. Sell or remove it first."
    ),
    "sales_listing_unique": "That listing has already been sold.",
    "sales_relisted_property": (
        "That home has been listed again since this sale, so the sale can't be "
        "removed or moved to another listing."
    ),
    "sales_price_positive": "Sale price must be greater than zero.",
    "sale_after_listing": "The sale date can't be before the listing date.",
}


class AppError(Exception):
    """An error whose message is safe to show the user."""


def _integrity_message(error: psycopg.IntegrityError) -> str:
    if isinstance(error, psycopg.errors.ForeignKeyViolation):
        return LINKED_RECORDS
    constraint = error.diag.constraint_name
    return CONSTRAINT_MESSAGES.get(
        constraint, f"That change breaks a rule: {constraint}."
    )


@contextmanager
def friendly_errors() -> Iterator[None]:
    try:
        yield
    except RecordNotFound:
        raise AppError("That record no longer exists.") from None
    except psycopg.IntegrityError as e:
        raise AppError(_integrity_message(e)) from None
    except psycopg.DataError:
        raise AppError("One of those values is out of range.") from None
    except psycopg.OperationalError:
        raise AppError("Lost the connection to the database.") from None
