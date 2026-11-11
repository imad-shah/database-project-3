from datetime import date, timedelta
from decimal import Decimal
from random import Random

import psycopg
from psycopg import sql

from models import Agent, Buyer, Listing, Property, Sale, Seller
from repository import TABLES, Repositories, init_db

from .data import FIRST_NAMES, LAST_NAMES, STREET_NAMES, STREET_SUFFIXES, TOWNS
from .images import draw_house

AGENT_COUNT = 12
BUYER_COUNT = 45
SELLER_COUNT = 45
SOLD_HOMES = 80
AVAILABLE_HOMES = 70

AS_OF = date(2005, 4, 12)
SOLD_LISTINGS_START = date(2003, 3, 1)
SOLD_LISTINGS_END = date(2004, 10, 31)
AVAILABLE_LISTINGS_START = date(2004, 9, 1)
AVAILABLE_LISTINGS_END = date(2005, 3, 31)

TOP_PRICE = Decimal(1_250_000)

Terms = dict[str, object]


def _random_date(rng: Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def _contact(rng: Random, index: int) -> dict[str, str]:
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    return {
        "first_name": first,
        "last_name": last,
        "phone": f"610-555-{rng.randint(0, 9999):04d}",
        "email": f"{first}.{last}.{index}@example.com".lower(),
    }


def _agents(rng: Random) -> list[Agent]:
    return [
        Agent(
            **_contact(rng, index),
            license_number=f"RS{100_000 + index}",
            hire_date=_random_date(rng, date(1995, 1, 1), date(2002, 12, 31)),
        )
        for index in range(AGENT_COUNT)
    ]


def _buyers(rng: Random) -> list[Buyer]:
    return [
        Buyer(
            **_contact(rng, index),
            max_budget=Decimal(rng.randrange(300_000, 800_000, 25_000)),
            min_bedrooms=rng.randint(2, 4),
            preferred_city=rng.choice((None, None, rng.choice(TOWNS).city)),
        )
        for index in range(BUYER_COUNT)
    ]


def _sellers(rng: Random) -> list[Seller]:
    return [Seller(**_contact(rng, index)) for index in range(SELLER_COUNT)]


def _home(
    rng: Random,
    number: int,
    listing_date: date,
    sellers: list[Seller],
    agents: list[Agent],
) -> tuple[Property, Terms]:
    town = rng.choice(TOWNS)
    bedrooms = rng.randint(2, 6)
    street = f"{rng.choice(STREET_NAMES)} {rng.choice(STREET_SUFFIXES)}"
    home = Property(
        street=f"{100 + number} {street}",
        city=town.city,
        state="PA",
        zip_code=town.zip_code,
        school_district=town.district,
        bedrooms=bedrooms,
        bathrooms=Decimal(rng.randint(2, 7)) / 2 + 1,
        square_feet=rng.randrange(900, 1100, 50) * bedrooms,
        year_built=rng.randint(1920, 2003),
        has_pool=rng.random() < 0.2,
    )
    terms = {
        "asking_price": Decimal(rng.randrange(town.min_price, town.max_price, 2_500)),
        "listing_date": listing_date,
        "seller_id": rng.choice(sellers).seller_id,
        "listing_agent_id": rng.choice(agents).agent_id,
    }
    return home, terms


def _featured_homes(
    sellers: list[Seller], agents: list[Agent]
) -> dict[str, tuple[Property, Terms]]:
    def home(
        asking_price: Decimal, listing_date: date, **details: object
    ) -> tuple[Property, Terms]:
        terms = {
            "asking_price": asking_price,
            "listing_date": listing_date,
            "seller_id": sellers[0].seller_id,
            "listing_agent_id": agents[0].agent_id,
        }
        return Property(state="PA", **details), terms

    return {
        "estate": home(
            street="900 Saucon Valley Rd",
            city="Bethlehem",
            zip_code="18015",
            school_district="Saucon Valley",
            bedrooms=7,
            bathrooms=Decimal("6.5"),
            square_feet=7200,
            year_built=1998,
            has_pool=True,
            asking_price=TOP_PRICE,
            listing_date=date(2005, 1, 15),
        ),
        "manor": home(
            street="12 Parkland Manor Ct",
            city="Orefield",
            zip_code="18069",
            school_district="Parkland",
            bedrooms=6,
            bathrooms=Decimal("5.5"),
            square_feet=6400,
            year_built=2001,
            has_pool=True,
            asking_price=TOP_PRICE + 50_000,
            listing_date=date(2004, 3, 1),
        ),
        "cottage": home(
            street="44 Lehigh Ave",
            city="Bethlehem",
            zip_code="18015",
            school_district="Bethlehem Area",
            bedrooms=3,
            bathrooms=Decimal("2.0"),
            square_feet=1800,
            year_built=1950,
            has_pool=False,
            asking_price=Decimal(235_000),
            listing_date=date(2005, 2, 1),
        ),
        "family": home(
            street="318 Cedar Crest Blvd",
            city="Allentown",
            zip_code="18104",
            school_district="Parkland",
            bedrooms=4,
            bathrooms=Decimal("2.5"),
            square_feet=2600,
            year_built=1985,
            has_pool=False,
            asking_price=Decimal(329_000),
            listing_date=date(2005, 3, 1),
        ),
    }


def _resale_home() -> Property:
    return Property(
        street="75 Ferry St",
        city="Easton",
        state="PA",
        zip_code="18042",
        school_district="Easton Area",
        bedrooms=3,
        bathrooms=Decimal("1.5"),
        square_feet=1500,
        year_built=1925,
        has_pool=False,
    )


def _sale(
    rng: Random, listing: Listing, buyers: list[Buyer], agents: list[Agent]
) -> Sale:
    has_buyers_agent = rng.random() < 0.6
    other_agent = rng.choice(agents).agent_id
    days_on_market = rng.randint(14, 180)
    return Sale(
        listing_id=listing.listing_id,
        buyer_id=rng.choice(buyers).buyer_id,
        selling_agent_id=(
            listing.listing_agent_id if rng.random() < 0.7 else other_agent
        ),
        buyers_agent_id=other_agent if has_buyers_agent else None,
        sale_price=round(listing.asking_price * Decimal(rng.uniform(0.92, 1.03)), -2),
        sale_date=min(listing.listing_date + timedelta(days=days_on_market), AS_OF),
    )


def reset(con: psycopg.Connection) -> None:
    con.execute("SELECT lo_unlink(oid) FROM pg_largeobject_metadata")
    con.execute(
        sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
            sql.SQL(", ").join(map(sql.Identifier, TABLES))
        )
    )
    init_db(con)


def populate(repositories: Repositories, seed: int = 4710) -> None:
    rng = Random(seed)
    agents = [repositories.agents.save(a) for a in _agents(rng)]
    buyers = [repositories.buyers.save(b) for b in _buyers(rng)]
    sellers = [repositories.sellers.save(s) for s in _sellers(rng)]

    def add_home(home: Property, **terms: object) -> Listing:
        property_id = repositories.properties.save(home).property_id
        return list_home(property_id, **terms)

    def list_home(property_id: int, **terms: object) -> Listing:
        return repositories.listings.save(Listing(property_id=property_id, **terms))

    def add_homes(
        count: int, start: date, end: date, first_number: int
    ) -> list[Listing]:
        listings = []
        for number in range(count):
            listing_date = _random_date(rng, start, end)
            home, terms = _home(
                rng, first_number + number, listing_date, sellers, agents
            )
            listings.append(add_home(home, **terms))
        return listings

    sold = add_homes(SOLD_HOMES, SOLD_LISTINGS_START, SOLD_LISTINGS_END, 0)
    add_homes(
        AVAILABLE_HOMES, AVAILABLE_LISTINGS_START, AVAILABLE_LISTINGS_END, SOLD_HOMES
    )
    for listing in sold:
        repositories.sales.save(_sale(rng, listing, buyers, agents))

    featured = {
        name: add_home(home, **terms)
        for name, (home, terms) in _featured_homes(sellers, agents).items()
    }
    repositories.sales.save(
        Sale(
            listing_id=featured["manor"].listing_id,
            buyer_id=buyers[0].buyer_id,
            selling_agent_id=agents[1].agent_id,
            buyers_agent_id=agents[2].agent_id,
            sale_price=TOP_PRICE,
            sale_date=date(2004, 6, 18),
        )
    )
    photos = {
        "estate": ((226, 214, 196), 3),
        "manor": ((196, 208, 216), 2),
        "cottage": ((222, 196, 176), 1),
    }
    for name, (wall, wings) in photos.items():
        repositories.properties.set_image(
            featured[name].property_id, draw_house(wall, wings)
        )

    first_sale = add_home(
        _resale_home(),
        asking_price=Decimal(145_000),
        listing_date=date(2003, 1, 10),
        seller_id=sellers[1].seller_id,
        listing_agent_id=agents[3].agent_id,
    )
    repositories.sales.save(
        Sale(
            listing_id=first_sale.listing_id,
            buyer_id=buyers[2].buyer_id,
            selling_agent_id=agents[3].agent_id,
            buyers_agent_id=agents[4].agent_id,
            sale_price=Decimal(142_000),
            sale_date=date(2003, 3, 20),
        )
    )
    list_home(
        first_sale.property_id,
        asking_price=Decimal(172_500),
        listing_date=date(2005, 3, 15),
        seller_id=sellers[2].seller_id,
        listing_agent_id=agents[5].agent_id,
    )
