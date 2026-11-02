from collections.abc import Callable
from dataclasses import dataclass
from operator import attrgetter

from models import Agent, Buyer, Property, Sale, Seller

from .field_types import DATE, DECIMAL, INTEGER, MONEY, UPPERCASE, YES_NO
from .fields import Field, OptionSource, reference


@dataclass(frozen=True, slots=True)
class EntitySpec[T]:
    title: str
    plural: str
    model: type[T]
    fields: tuple[Field, ...]
    label: Callable[[T], str] = str
    delete_warning: str = ""

    @property
    def key(self) -> Field:
        return self.fields[0]


def _key(name: str, title: str) -> Field:
    return Field(name, f"{title} ID", INTEGER, editable=False)


_full_name = attrgetter("full_name")

_PERSON_FIELDS = (
    Field("first_name", "First Name", required=True),
    Field("last_name", "Last Name", required=True),
    Field("phone", "Phone"),
    Field("email", "Email"),
)

AGENT_SPEC = EntitySpec(
    title="Agent",
    plural="Agents",
    model=Agent,
    label=_full_name,
    fields=(
        _key("agent_id", "Agent"),
        *_PERSON_FIELDS,
        Field("license_number", "License Number", required=True),
        Field("hire_date", "Hire Date (YYYY-MM-DD)", DATE, required=True),
    ),
)

BUYER_SPEC = EntitySpec(
    title="Buyer",
    plural="Buyers",
    model=Buyer,
    label=_full_name,
    fields=(
        _key("buyer_id", "Buyer"),
        *_PERSON_FIELDS,
        Field("max_budget", "Maximum Budget", MONEY),
        Field("min_bedrooms", "Minimum Bedrooms", INTEGER),
        Field("preferred_city", "Preferred City"),
    ),
)

SELLER_SPEC = EntitySpec(
    title="Seller",
    plural="Sellers",
    model=Seller,
    label=_full_name,
    fields=(_key("seller_id", "Seller"), *_PERSON_FIELDS),
)


def property_spec(sellers: OptionSource, agents: OptionSource) -> EntitySpec[Property]:
    return EntitySpec(
        title="Property",
        plural="Properties",
        model=Property,
        label=attrgetter("address"),
        fields=(
            _key("property_id", "Property"),
            Field("status", "Status", in_form=False),
            Field("street", "Street", required=True),
            Field("city", "City", required=True),
            Field("state", "State", UPPERCASE, required=True, default="PA"),
            Field("zip_code", "ZIP Code", required=True),
            Field("school_district", "School District", required=True),
            Field("bedrooms", "Bedrooms", INTEGER, required=True),
            Field("bathrooms", "Bathrooms", DECIMAL, required=True),
            Field("square_feet", "Square Feet", INTEGER, required=True),
            Field("year_built", "Year Built", INTEGER),
            Field("has_pool", "Swimming Pool", YES_NO, required=True, default="No"),
            Field("asking_price", "Asking Price", MONEY, required=True),
            Field("listing_date", "Listing Date (YYYY-MM-DD)", DATE, required=True),
            reference("seller_id", "Seller", sellers),
            reference("listing_agent_id", "Listing Agent", agents),
            Field("has_photo", "Photo", YES_NO, in_form=False),
        ),
    )


def sale_spec(
    properties: OptionSource,
    available_properties: OptionSource,
    buyers: OptionSource,
    agents: OptionSource,
) -> EntitySpec[Sale]:
    return EntitySpec(
        title="Sale",
        plural="Sales",
        model=Sale,
        delete_warning="\n\nThe property will be listed as available again.",
        fields=(
            _key("sale_id", "Sale"),
            reference(
                "property_id", "Property", properties, selectable=available_properties
            ),
            reference("buyer_id", "Buyer", buyers),
            reference("selling_agent_id", "Selling Agent", agents),
            reference("buyers_agent_id", "Buyer's Agent", agents, required=False),
            Field("sale_price", "Sale Price", MONEY, required=True),
            Field("sale_date", "Sale Date (YYYY-MM-DD)", DATE, required=True),
        ),
    )
