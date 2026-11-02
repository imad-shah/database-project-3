from dataclasses import dataclass

from models import Agent, Buyer, Sale, Seller
from repository import Repositories

from .entity_controller import EntityController
from .interfaces import IEntityController, IPropertyController, IReportController
from .property_controller import PropertyController
from .report_controller import ReportController
from .reports import build_reports
from .specs import AGENT_SPEC, BUYER_SPEC, SELLER_SPEC, property_spec, sale_spec


@dataclass(frozen=True, slots=True)
class Controllers:
    agents: IEntityController[Agent]
    buyers: IEntityController[Buyer]
    sellers: IEntityController[Seller]
    properties: IPropertyController
    sales: IEntityController[Sale]
    reports: IReportController


def build_controllers(repositories: Repositories) -> Controllers:
    agents = EntityController(AGENT_SPEC, repositories.agents)
    buyers = EntityController(BUYER_SPEC, repositories.buyers)
    sellers = EntityController(SELLER_SPEC, repositories.sellers)
    properties = PropertyController(
        property_spec(sellers.options, agents.options), repositories.properties
    )
    sales = EntityController(
        sale_spec(
            properties.options,
            properties.available_options,
            buyers.options,
            agents.options,
        ),
        repositories.sales,
    )
    reports = ReportController(
        build_reports(buyers.options), repositories.reports, properties
    )
    return Controllers(agents, buyers, sellers, properties, sales, reports)
