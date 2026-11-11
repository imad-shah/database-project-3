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
def home(controllers):
    return controllers.properties.save(home_values())


@pytest.fixture
def listing(controllers, people, home):
    return controllers.listings.save(listing_values(home, people))


def home_values(**overrides: str) -> dict[str, str]:
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
    }
    return values | overrides


def listing_values(home, people, **overrides: str) -> dict[str, str]:
    values = {
        "property_id": str(home.property_id),
        "seller_id": str(people["seller"].seller_id),
        "listing_agent_id": str(people["agent"].agent_id),
        "asking_price": "$230,000.00",
        "listing_date": "2004-02-01",
    }
    return values | overrides


def sale_values(listing, people, **overrides: str) -> dict[str, str]:
    values = {
        "listing_id": str(listing.listing_id),
        "buyer_id": str(people["buyer"].buyer_id),
        "selling_agent_id": str(people["agent"].agent_id),
        "buyers_agent_id": str(people["other"].agent_id),
        "sale_price": "225000",
        "sale_date": "2004-03-01",
    }
    return values | overrides


def large_object_count(con) -> int:
    return con.execute("SELECT count(*) FROM pg_largeobject_metadata").fetchone()[0]


def test_new_home_is_not_listed_and_has_no_photo(home):
    assert home.status == "Not Listed"
    assert home.has_photo is False
    assert home.state == "PA"


def test_new_listing_is_available(repositories, home, listing):
    assert listing.status == "Available"
    assert (listing.street, listing.city) == (home.street, home.city)
    assert repositories.properties.find(home.property_id).status == "Available"


def test_listing_label_shows_the_address(controllers, listing):
    assert str(controllers.listings.options()[0]) == (
        f"{listing.listing_id} - 1 Main St, Bethlehem"
    )


def test_duplicate_address_is_explained(controllers, home):
    with pytest.raises(AppError, match="address already exists"):
        controllers.properties.save(home_values())


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"state": "Penn"}, "two-letter"),
        ({"zip_code": "1801"}, "ZIP code"),
        ({"bedrooms": "-1"}, "Bedrooms"),
        ({"square_feet": "0"}, "Square feet"),
        ({"year_built": "1200"}, "Year built"),
    ],
)
def test_property_rules_are_explained(controllers, overrides, message):
    with pytest.raises(AppError, match=message):
        controllers.properties.save(home_values(**overrides))


def test_asking_price_must_be_positive(controllers, people, home):
    with pytest.raises(AppError, match="Asking price"):
        controllers.listings.save(listing_values(home, people, asking_price="0"))


def test_listing_requires_an_existing_property(controllers, people, home):
    values = listing_values(home, people, property_id="999")
    with pytest.raises(AppError, match="linked to other records"):
        controllers.listings.save(values)


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


def test_sold_listing_leaves_the_available_list(
    controllers, repositories, people, listing
):
    assert controllers.listings.available_options() != []
    controllers.sales.save(sale_values(listing, people))
    assert controllers.listings.available_options() == []
    assert repositories.listings.find(listing.listing_id).status == "Sold"
    assert repositories.properties.find(listing.property_id).status == "Sold"


def test_deleting_a_sale_makes_the_listing_available(controllers, people, listing):
    sale = controllers.sales.save(sale_values(listing, people))
    controllers.sales.delete(str(sale.sale_id))
    assert len(controllers.listings.available_options()) == 1


def test_a_listing_sells_at_most_once(controllers, people, listing):
    controllers.sales.save(sale_values(listing, people))
    with pytest.raises(AppError, match="listing has already been sold"):
        controllers.sales.save(sale_values(listing, people))


def test_a_home_has_one_active_listing_at_a_time(controllers, people, home, listing):
    with pytest.raises(AppError, match="already has an active listing"):
        controllers.listings.save(listing_values(home, people))
    assert controllers.properties.unlisted_options() == []


def test_a_listing_cannot_change_property(controllers, people, listing):
    other = controllers.properties.save(home_values(street="2 Main St"))
    moved = listing_values(other, people, listing_id=str(listing.listing_id))
    with pytest.raises(AppError, match="can't be moved to a different property"):
        controllers.listings.save(moved)


def relist(controllers, home, people, listing_date):
    return controllers.listings.save(
        listing_values(home, people, listing_date=listing_date)
    )


def test_relisting_before_the_prior_sale_is_rejected(
    controllers, people, home, listing
):
    controllers.sales.save(sale_values(listing, people, sale_date="2004-03-01"))
    with pytest.raises(AppError, match="can't be relisted before its previous sale"):
        relist(controllers, home, people, "2004-02-29")


@pytest.mark.parametrize("listing_date", ["2004-03-01", "2004-03-02"])
def test_relisting_on_or_after_the_prior_sale_is_allowed(
    controllers, people, home, listing, listing_date
):
    controllers.sales.save(sale_values(listing, people, sale_date="2004-03-01"))
    assert relist(controllers, home, people, listing_date).status == "Available"


def test_moving_a_relisting_before_the_prior_sale_is_rejected(
    controllers, people, home, listing
):
    controllers.sales.save(sale_values(listing, people, sale_date="2004-03-01"))
    relisting = relist(controllers, home, people, "2004-06-01")
    values = listing_values(
        home, people, listing_id=str(relisting.listing_id), listing_date="2004-02-15"
    )
    with pytest.raises(AppError, match="can't be relisted before its previous sale"):
        controllers.listings.save(values)


def test_an_earlier_listing_stays_editable_after_a_resale(
    controllers, repositories, people, home, listing
):
    controllers.sales.save(sale_values(listing, people, sale_date="2004-03-01"))
    relisting = relist(controllers, home, people, "2004-06-01")
    controllers.sales.save(
        sale_values(relisting, people, sale_date="2004-08-01", sale_price="250000")
    )
    values = listing_values(
        home, people, listing_id=str(listing.listing_id), asking_price="231000"
    )
    controllers.listings.save(values)
    assert repositories.listings.find(listing.listing_id).asking_price == 231000


def test_a_sold_home_can_be_relisted_and_sold_again(
    controllers, repositories, people, home, listing
):
    controllers.sales.save(sale_values(listing, people))
    assert [o.id for o in controllers.properties.unlisted_options()] == [
        home.property_id
    ]
    new_owner = repositories.sellers.save(Seller(first_name="N", last_name="Ew"))
    relisting = controllers.listings.save(
        listing_values(
            home,
            people,
            seller_id=str(new_owner.seller_id),
            asking_price="260000",
            listing_date="2005-01-10",
        )
    )
    assert relisting.listing_id != listing.listing_id
    assert relisting.seller_id == new_owner.seller_id
    assert repositories.properties.find(home.property_id).status == "Available"
    assert [o.id for o in controllers.listings.available_options()] == [
        relisting.listing_id
    ]
    resale = controllers.sales.save(
        sale_values(relisting, people, sale_price="255000", sale_date="2005-03-01")
    )
    assert resale.listing_id == relisting.listing_id
    assert repositories.properties.find(home.property_id).status == "Sold"
    statuses = {
        lst.listing_id: lst.status
        for lst in repositories.listings.find_all()
        if lst.property_id == home.property_id
    }
    assert statuses == {listing.listing_id: "Sold", relisting.listing_id: "Sold"}


def test_a_sale_cannot_be_removed_after_the_home_is_relisted(
    controllers, repositories, people, home, listing
):
    sale = controllers.sales.save(sale_values(listing, people))
    controllers.listings.save(listing_values(home, people, listing_date="2005-01-10"))
    with pytest.raises(AppError, match="listed again since this sale"):
        controllers.sales.delete(str(sale.sale_id))
    assert repositories.sales.find(sale.sale_id) is not None


def test_sale_cannot_precede_listing(controllers, people, listing):
    early = str(listing.listing_date - timedelta(days=1))
    with pytest.raises(AppError, match="before the listing date"):
        controllers.sales.save(sale_values(listing, people, sale_date=early))


def test_sale_on_listing_day_is_allowed(controllers, people, listing):
    same_day = str(listing.listing_date)
    assert controllers.sales.save(sale_values(listing, people, sale_date=same_day))


def test_listing_date_cannot_move_past_its_sale(controllers, people, home, listing):
    controllers.sales.save(sale_values(listing, people))
    values = listing_values(
        home, people, listing_id=str(listing.listing_id), listing_date="2004-04-01"
    )
    with pytest.raises(AppError, match="before the listing date"):
        controllers.listings.save(values)


def test_sale_price_must_be_positive(controllers, people, listing):
    with pytest.raises(AppError, match="Sale price"):
        controllers.sales.save(sale_values(listing, people, sale_price="0"))


def test_sale_requires_an_existing_buyer(controllers, people, listing):
    with pytest.raises(AppError, match="linked to other records"):
        controllers.sales.save(sale_values(listing, people, buyer_id="999"))


def test_agent_with_a_listing_cannot_be_deleted(controllers, people, listing):
    with pytest.raises(AppError, match="linked to other records"):
        controllers.agents.delete(str(people["agent"].agent_id))


def test_listed_property_cannot_be_deleted(controllers, listing):
    with pytest.raises(AppError, match="linked to other records"):
        controllers.properties.delete(str(listing.property_id))


def test_sold_listing_cannot_be_deleted(controllers, people, listing):
    controllers.sales.save(sale_values(listing, people))
    with pytest.raises(AppError, match="linked to other records"):
        controllers.listings.delete(str(listing.listing_id))


def test_unsold_listing_can_be_withdrawn(controllers, repositories, home, listing):
    controllers.listings.delete(str(listing.listing_id))
    assert repositories.properties.find(home.property_id).status == "Not Listed"


def test_photo_round_trip(controllers, repositories, home, tmp_path):
    photo = draw_house((200, 200, 200), 1)
    path = tmp_path / "house.png"
    path.write_bytes(photo)
    property_id = str(home.property_id)
    controllers.properties.attach_image(property_id, str(path))
    assert controllers.properties.image(property_id) == photo
    assert repositories.properties.find(home.property_id).has_photo is True


def test_home_without_a_photo_has_no_image(controllers, home):
    assert controllers.properties.image(str(home.property_id)) is None


def test_non_image_file_is_rejected(controllers, home, tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("not a picture")
    with pytest.raises(AppError, match="readable image"):
        controllers.properties.attach_image(str(home.property_id), str(path))


def test_missing_file_is_rejected(controllers, home):
    with pytest.raises(AppError, match="readable image"):
        controllers.properties.attach_image(
            str(home.property_id), str(Path("/no/such/file.png"))
        )


def test_replacing_a_photo_frees_the_old_blob(con, repositories, home):
    baseline = large_object_count(con)
    photo = draw_house((1, 2, 3), 1)
    repositories.properties.set_image(home.property_id, photo)
    repositories.properties.set_image(home.property_id, photo)
    assert large_object_count(con) == baseline + 1


def test_removing_a_photo_frees_the_blob(con, controllers, repositories, home):
    baseline = large_object_count(con)
    repositories.properties.set_image(home.property_id, draw_house((1, 2, 3), 1))
    controllers.properties.remove_image(str(home.property_id))
    assert large_object_count(con) == baseline
    assert controllers.properties.image(str(home.property_id)) is None


def test_deleting_a_home_frees_its_blob(con, controllers, repositories, home):
    baseline = large_object_count(con)
    repositories.properties.set_image(home.property_id, draw_house((1, 2, 3), 1))
    controllers.properties.delete(str(home.property_id))
    assert large_object_count(con) == baseline


def test_editing_a_home_keeps_its_photo(controllers, repositories, home):
    photo = draw_house((1, 2, 3), 1)
    repositories.properties.set_image(home.property_id, photo)
    controllers.properties.save(
        home_values(property_id=str(home.property_id), bedrooms="4")
    )
    assert controllers.properties.image(str(home.property_id)) == photo
