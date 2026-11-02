from dataclasses import dataclass
from typing import Self

import psycopg

from models import Agent, Buyer, Property, Sale, Seller

from .interfaces import IPropertyRepository, RecordNotFound
from .report_repository import ReportRepository
from .sql_repository import SqlRepository


class AgentRepository(SqlRepository[Agent]):
    model = Agent
    table = "agents"
    key = "agent_id"
    order_by = "last_name, first_name"


class BuyerRepository(SqlRepository[Buyer]):
    model = Buyer
    table = "buyers"
    key = "buyer_id"
    order_by = "last_name, first_name"


class SellerRepository(SqlRepository[Seller]):
    model = Seller
    table = "sellers"
    key = "seller_id"
    order_by = "last_name, first_name"


class SaleRepository(SqlRepository[Sale]):
    model = Sale
    table = "sales"
    key = "sale_id"
    order_by = "sale_date DESC, sale_id DESC"


class PropertyRepository(SqlRepository[Property], IPropertyRepository):
    model = Property
    table = "properties"
    source = "property_listings"
    key = "property_id"
    order_by = "city, street"
    computed = frozenset({"status", "has_photo"})

    def find_available(self) -> list[Property]:
        return self._select("status = 'Available'")

    def get_image(self, property_id: int) -> bytes | None:
        row = self._con.execute(
            "SELECT lo_get(image) FROM properties WHERE property_id = %s",
            (property_id,),
        ).fetchone()
        if row is None:
            raise RecordNotFound
        return row[0] and bytes(row[0])

    def set_image(self, property_id: int, image: bytes | None) -> None:
        self._write_one(
            """
            UPDATE properties
            SET image = CASE WHEN %(image)s::bytea IS NULL THEN NULL
                             ELSE lo_from_bytea(0, %(image)s::bytea) END
            WHERE property_id = %(property_id)s
            RETURNING property_id
            """,
            {"image": image, "property_id": property_id},
        )


@dataclass(frozen=True, slots=True)
class Repositories:
    agents: AgentRepository
    buyers: BuyerRepository
    sellers: SellerRepository
    properties: PropertyRepository
    sales: SaleRepository
    reports: ReportRepository

    @classmethod
    def connect(cls, con: psycopg.Connection) -> Self:
        return cls(
            agents=AgentRepository(con),
            buyers=BuyerRepository(con),
            sellers=SellerRepository(con),
            properties=PropertyRepository(con),
            sales=SaleRepository(con),
            reports=ReportRepository(con),
        )
