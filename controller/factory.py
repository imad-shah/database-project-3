from dataclasses import dataclass

from models import Agent, Buyer, Sale, Seller
from repository import Repositories

from .entity_controller import EntityController
from .interfaces import (
    IEntityController,
    IListingController,
    IPropertyController,
    IReportController,
)
from .listing_controller import ListingController
from .property_controller import PropertyController
from .report_controller import ReportController
from .reports import build_reports
from .specs import (
    AGENT_SPEC,
    BUYER_SPEC,
    PROPERTY_SPEC,
    SELLER_SPEC,
    listing_spec,
    sale_spec,
)


@dataclass(frozen=True, slots=True)
class Controllers:
    agents: IEntityController[Agent]
    buyers: IEntityController[Buyer]
    sellers: IEntityController[Seller]
    properties: IPropertyController
    listings: IListingController
    sales: IEntityController[Sale]
    reports: IReportController


def build_controllers(repositories: Repositories) -> Controllers:
    agents = EntityController(AGENT_SPEC, repositories.agents)
    buyers = EntityController(BUYER_SPEC, repositories.buyers)
    sellers = EntityController(SELLER_SPEC, repositories.sellers)
    properties = PropertyController(PROPERTY_SPEC, repositories.properties)
    listings = ListingController(
        listing_spec(
            properties.options,
            properties.unlisted_options,
            sellers.options,
            agents.options,
        ),
        repositories.listings,
    )
    sales = EntityController(
        sale_spec(
            listings.options,
            listings.available_options,
            buyers.options,
            agents.options,
        ),
        repositories.sales,
    )
    reports = ReportController(
        build_reports(buyers.options), repositories.reports, properties
    )
    return Controllers(agents, buyers, sellers, properties, listings, sales, reports)
