from dataclasses import dataclass

from repository import queries

from .field_types import DATE, INTEGER, MONEY, YES_NO
from .fields import Field, OptionSource, reference


@dataclass(frozen=True, slots=True)
class Report:
    title: str
    question: str
    query: str
    params: tuple[Field, ...] = ()
    image_column: str | None = None


def _year(default: str = "2004") -> Field:
    return Field("year", "Year", INTEGER, required=True, default=default)


def build_reports(buyers: OptionSource) -> tuple[Report, ...]:
    return (
        Report(
            title="Homes by city and price",
            question="Find addresses of homes for sale in a city within a price range.",
            query=queries.HOMES_BY_CITY_AND_PRICE,
            params=(
                Field("city", "City", required=True, default="Bethlehem"),
                Field(
                    "min_price", "Lowest Price", MONEY, required=True, default="200000"
                ),
                Field(
                    "max_price", "Highest Price", MONEY, required=True, default="250000"
                ),
            ),
        ),
        Report(
            title="Homes by school district",
            question=(
                "Find addresses of homes for sale in a school district "
                "with at least a given number of bedrooms, with or without a pool."
            ),
            query=queries.HOMES_BY_DISTRICT,
            params=(
                Field("district", "School District", required=True, default="Parkland"),
                Field(
                    "min_bedrooms",
                    "Minimum Bedrooms",
                    INTEGER,
                    required=True,
                    default="4",
                ),
                Field("has_pool", "Swimming Pool", YES_NO, required=True, default="No"),
            ),
        ),
        Report(
            title="Top agent of the year",
            question="Find the agent who sold the most property in a year by total dollar value.",
            query=queries.TOP_AGENT_BY_SALES,
            params=(_year(),),
        ),
        Report(
            title="Agent performance",
            question=(
                "For each agent, compute the average selling price of properties "
                "sold in a year and the average time they were on the market."
            ),
            query=queries.AGENT_PERFORMANCE,
            params=(_year(),),
        ),
        Report(
            title="Most expensive homes",
            question="Show a picture of the most expensive house(s) in the database.",
            query=queries.MOST_EXPENSIVE_HOMES,
            image_column="Property ID",
        ),
        Report(
            title="Homes matching a buyer",
            question="Find available homes that fit a buyer's budget, bedrooms and city.",
            query=queries.HOMES_FOR_BUYER,
            params=(reference("buyer_id", "Buyer", buyers),),
        ),
        Report(
            title="Slow-moving listings",
            question="Find available homes that have been on the market for a long time.",
            query=queries.STALE_LISTINGS,
            params=(
                Field(
                    "as_of",
                    "As Of (YYYY-MM-DD)",
                    DATE,
                    required=True,
                    default="2005-04-12",
                ),
                Field("min_days", "Minimum Days", INTEGER, required=True, default="90"),
            ),
        ),
        Report(
            title="Market summary by city",
            question="Summarize each city's sales in a year, including price against asking.",
            query=queries.MARKET_BY_CITY,
            params=(_year(),),
        ),
    )
