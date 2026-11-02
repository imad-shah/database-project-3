from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from controller import AppError
from models import Agent, Buyer, Seller
from seed.images import draw_house


@pytest.fixture
def people(repositories):
    agent = repositories.agents.save(
        Agent(
            first_name="A",
            last_name="Gent",
            license_number="RS1",
            hire_date=date(2000, 1, 1),
        )
    )
    other = repositories.agents.save(
        Agent(
            first_name="B",
            last_name="Gent",
            license_number="RS2",
            hire_date=date(2000, 1, 1),
        )
    )
    buyer = repositories.buyers.save(Buyer(first_name="B", last_name="Uyer"))
    seller = repositories.sellers.save(Seller(first_name="S", last_name="Eller"))
    return {"agent": agent, "other": other, "buyer": buyer, "seller": seller}


@pytest.fixture
def listing(controllers, people):
    return controllers.properties.save(listing_values(people))


def listing_values(people, **overrides: str) -> dict[str, str]:
    values = {
        "street": "1 Main St",
        "city": "Bethlehem",
        "state": "pa",
        "zip_code": "18015",
        "school_district": "Bethlehem Area",
        "bedrooms": "3",
        "bathrooms": "2.5",
        "square_feet": "1800",
        "year_built": "1950",
        "has_pool": "No",
        "asking_price": "$230,000.00",
        "listing_date": "2004-02-01",
        "seller_id": str(people["seller"].seller_id),
        "listing_agent_id": str(people["agent"].agent_id),
    }
    return values | overrides


def sale_values(listing, people, **overrides: str) -> dict[str, str]:
    values = {
        "property_id": str(listing.property_id),
        "buyer_id": str(people["buyer"].buyer_id),
        "selling_agent_id": str(people["agent"].agent_id),
        "buyers_agent_id": str(people["other"].agent_id),
        "sale_price": "225000",
        "sale_date": "2004-03-01",
    }
    return values | overrides


def large_object_count(con) -> int:
    return con.execute("SELECT count(*) FROM pg_largeobject_metadata").fetchone()[0]


def test_new_listing_is_available_without_a_photo(listing):
    assert listing.status == "Available"
    assert listing.has_photo is False
    assert listing.state == "PA"


def test_duplicate_address_is_explained(controllers, people, listing):
    with pytest.raises(AppError, match="address already exists"):
        controllers.properties.save(listing_values(people))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"state": "Penn"}, "two-letter"),
        ({"zip_code": "1801"}, "ZIP code"),
        ({"bedrooms": "-1"}, "Bedrooms"),
        ({"square_feet": "0"}, "Square feet"),
        ({"year_built": "1200"}, "Year built"),
        ({"asking_price": "0"}, "Asking price"),
    ],
)
def test_listing_rules_are_explained(controllers, people, overrides, message):
    with pytest.raises(AppError, match=message):
        controllers.properties.save(listing_values(people, **overrides))


def test_recording_a_sale_stores_every_detail(controllers, people, listing):
    sale = controllers.sales.save(sale_values(listing, people))
    assert sale.sale_price == Decimal(225000)
    assert sale.sale_date == date(2004, 3, 1)
    assert sale.buyer_id == people["buyer"].buyer_id
    assert sale.selling_agent_id == people["agent"].agent_id
    assert sale.buyers_agent_id == people["other"].agent_id


def test_buyers_agent_is_optional(controllers, people, listing):
    sale = controllers.sales.save(sale_values(listing, people, buyers_agent_id=""))
    assert sale.buyers_agent_id is None


def test_sold_home_leaves_the_available_list(
    controllers, repositories, people, listing
):
    assert controllers.properties.available_options() != []
    controllers.sales.save(sale_values(listing, people))
    assert controllers.properties.available_options() == []
    assert repositories.properties.find(listing.property_id).status == "Sold"


def test_deleting_a_sale_relists_the_home(controllers, people, listing):
    sale = controllers.sales.save(sale_values(listing, people))
    controllers.sales.delete(str(sale.sale_id))
    assert len(controllers.properties.available_options()) == 1


def test_a_home_cannot_be_sold_twice(controllers, people, listing):
    controllers.sales.save(sale_values(listing, people))
    with pytest.raises(AppError, match="already been sold"):
        controllers.sales.save(sale_values(listing, people))


def test_sale_cannot_precede_listing(controllers, people, listing):
    early = str(listing.listing_date - timedelta(days=1))
    with pytest.raises(AppError, match="before the listing date"):
        controllers.sales.save(sale_values(listing, people, sale_date=early))


def test_sale_on_listing_day_is_allowed(controllers, people, listing):
    same_day = str(listing.listing_date)
    assert controllers.sales.save(sale_values(listing, people, sale_date=same_day))


def test_listing_date_cannot_move_past_its_sale(controllers, people, listing):
    controllers.sales.save(sale_values(listing, people))
    values = listing_values(
        people, property_id=str(listing.property_id), listing_date="2004-04-01"
    )
    with pytest.raises(AppError, match="before the listing date"):
        controllers.properties.save(values)


def test_sale_price_must_be_positive(controllers, people, listing):
    with pytest.raises(AppError, match="Sale price"):
        controllers.sales.save(sale_values(listing, people, sale_price="0"))


def test_sale_requires_an_existing_buyer(controllers, people, listing):
    with pytest.raises(AppError, match="linked to other records"):
        controllers.sales.save(sale_values(listing, people, buyer_id="999"))


def test_agent_with_a_listing_cannot_be_deleted(controllers, people, listing):
    with pytest.raises(AppError, match="linked to other records"):
        controllers.agents.delete(str(people["agent"].agent_id))


def test_sold_property_cannot_be_deleted(controllers, people, listing):
    controllers.sales.save(sale_values(listing, people))
    with pytest.raises(AppError, match="linked to other records"):
        controllers.properties.delete(str(listing.property_id))


def test_photo_round_trip(controllers, repositories, listing, tmp_path):
    photo = draw_house((200, 200, 200), 1)
    path = tmp_path / "house.png"
    path.write_bytes(photo)
    property_id = str(listing.property_id)
    controllers.properties.attach_image(property_id, str(path))
    assert controllers.properties.image(property_id) == photo
    assert repositories.properties.find(listing.property_id).has_photo is True


def test_home_without_a_photo_has_no_image(controllers, listing):
    assert controllers.properties.image(str(listing.property_id)) is None


def test_non_image_file_is_rejected(controllers, listing, tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("not a picture")
    with pytest.raises(AppError, match="readable image"):
        controllers.properties.attach_image(str(listing.property_id), str(path))


def test_missing_file_is_rejected(controllers, listing):
    with pytest.raises(AppError, match="readable image"):
        controllers.properties.attach_image(
            str(listing.property_id), str(Path("/no/such/file.png"))
        )


def test_replacing_a_photo_frees_the_old_blob(con, repositories, listing):
    baseline = large_object_count(con)
    photo = draw_house((1, 2, 3), 1)
    repositories.properties.set_image(listing.property_id, photo)
    repositories.properties.set_image(listing.property_id, photo)
    assert large_object_count(con) == baseline + 1


def test_removing_a_photo_frees_the_blob(con, controllers, repositories, listing):
    baseline = large_object_count(con)
    repositories.properties.set_image(listing.property_id, draw_house((1, 2, 3), 1))
    controllers.properties.remove_image(str(listing.property_id))
    assert large_object_count(con) == baseline
    assert controllers.properties.image(str(listing.property_id)) is None


def test_deleting_a_home_frees_its_blob(con, controllers, repositories, listing):
    baseline = large_object_count(con)
    repositories.properties.set_image(listing.property_id, draw_house((1, 2, 3), 1))
    controllers.properties.delete(str(listing.property_id))
    assert large_object_count(con) == baseline


def test_editing_a_listing_keeps_its_photo(controllers, repositories, people, listing):
    photo = draw_house((1, 2, 3), 1)
    repositories.properties.set_image(listing.property_id, photo)
    values = listing_values(people, property_id=str(listing.property_id), bedrooms="4")
    controllers.properties.save(values)
    assert controllers.properties.image(str(listing.property_id)) == photo
