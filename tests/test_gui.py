import tkinter as tk

import pytest

import gui.entity_tab
import gui.properties_tab
import gui.widgets
from gui import RealEstateApp
from gui.entity_tab import EntityTab
from gui.properties_tab import PropertiesTab
from gui.reports_tab import ReportsTab
from seed.images import draw_house


class Dialogs:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.infos: list[str] = []
        self.confirm = True

    def showerror(self, _title: str, message: str) -> None:
        self.errors.append(message)

    def showinfo(self, _title: str, message: str) -> None:
        self.infos.append(message)

    def askyesno(self, _title: str, _message: str) -> bool:
        return self.confirm


@pytest.fixture
def dialogs(monkeypatch):
    fake = Dialogs()
    for module in (gui.widgets, gui.entity_tab, gui.properties_tab):
        monkeypatch.setattr(module, "messagebox", fake)
    return fake


@pytest.fixture
def app(seeded, controllers, dialogs):
    try:
        window = RealEstateApp(controllers)
    except tk.TclError:
        pytest.skip("No display available")
    window.withdraw()
    yield window
    window.destroy()


def tab_named(app, name):
    return next(tab for tab in app.tabs if tab.tab_name == name)


def select_row(app, tab, index=0):
    tab.table._tree.selection_set(str(index))
    app.update()


def test_every_tab_loads(app, dialogs):
    assert [tab.tab_name for tab in app.tabs] == [
        "Properties",
        "Listings",
        "Sales",
        "Agents",
        "Buyers",
        "Sellers",
        "Reports",
    ]
    assert dialogs.errors == []
    for tab in app.tabs:
        if isinstance(tab, EntityTab):
            assert tab.table._rows


def test_property_table_uses_a_compact_summary(app):
    tab = tab_named(app, "Properties")
    displayed = tuple(tab.table._tree.cget("displaycolumns"))
    assert displayed == (
        "Property ID",
        "Status",
        "Street",
        "City",
        "State",
        "ZIP Code",
        "Bedrooms",
        "Bathrooms",
        "Square Feet",
        "Photo",
    )
    assert len(tab.table._tree.cget("columns")) == len(tab.controller.spec.fields)


@pytest.mark.parametrize(
    "name", ["Properties", "Listings", "Sales", "Agents", "Buyers", "Sellers"]
)
def test_saving_an_unchanged_row_round_trips(app, dialogs, controllers, name):
    tab = tab_named(app, name)
    before = tab.table._rows[0]
    select_row(app, tab)
    tab._save()
    assert dialogs.errors == []
    key = before[0]
    assert next(row for row in tab.controller.rows() if row[0] == key) == before


def test_blank_form_does_not_preselect_records(app):
    tab = tab_named(app, "Sales")
    assert tab.form.values()["listing_id"] == ""
    assert tab.form.values()["buyer_id"] == ""


def test_invalid_save_shows_an_error(app, dialogs):
    tab = tab_named(app, "Agents")
    tab._save()
    assert dialogs.errors == ["First Name is required."]


def chooser_values(tab, name):
    return set(next(c for f, c in tab.form._choosers if f.name == name)["values"])


def row_for(tab, record_id):
    return next(r for r in tab.table._rows if r[0] == str(record_id))


def test_sale_form_offers_only_available_listings(app, controllers):
    offered = chooser_values(tab_named(app, "Sales"), "listing_id")
    assert offered == {str(o) for o in controllers.listings.available_options()}


def test_listing_form_offers_only_unlisted_homes(app, controllers):
    offered = chooser_values(tab_named(app, "Listings"), "property_id")
    assert offered == {str(o) for o in controllers.properties.unlisted_options()}


def sell(app, controllers, option, sale_date="2005-04-12"):
    sales = tab_named(app, "Sales")
    sales.form.fill(
        {
            "listing_id": str(option),
            "buyer_id": str(controllers.buyers.options()[0]),
            "selling_agent_id": str(controllers.agents.options()[0]),
            "sale_price": "$240,000",
            "sale_date": sale_date,
        }
    )
    sales._save()


def test_recording_a_sale_updates_other_tabs(app, dialogs, controllers, seeded):
    option = controllers.listings.available_options()[0]
    property_id = seeded.listings.find(option.id).property_id
    sell(app, controllers, option)
    assert dialogs.errors == []
    assert dialogs.infos == ["Sale saved."]
    assert str(option) not in chooser_values(tab_named(app, "Sales"), "listing_id")
    assert row_for(tab_named(app, "Listings"), option.id)[1] == "Sold"
    assert row_for(tab_named(app, "Properties"), property_id)[1] == "Sold"


def test_a_home_can_be_added_listed_sold_and_relisted(app, dialogs, controllers):
    properties = tab_named(app, "Properties")
    listings = tab_named(app, "Listings")
    properties.form.fill(
        {
            "street": "5 New St",
            "city": "Easton",
            "state": "PA",
            "zip_code": "18042",
            "school_district": "Easton Area",
            "bedrooms": "3",
            "bathrooms": "2",
            "square_feet": "1600",
            "has_pool": "No",
        }
    )
    properties._save()
    home = next(
        o for o in controllers.properties.options() if o.label.startswith("5 New St")
    )
    assert row_for(properties, home.id)[1] == "Not Listed"

    def list_home(listing_date):
        listings.form.fill(
            {
                "property_id": str(home),
                "seller_id": str(controllers.sellers.options()[0]),
                "listing_agent_id": str(controllers.agents.options()[0]),
                "asking_price": "$200,000",
                "listing_date": listing_date,
            }
        )
        listings._save()
        return next(
            o for o in controllers.listings.available_options() if o.label == home.label
        )

    first = list_home("2005-01-03")
    assert row_for(properties, home.id)[1] == "Available"
    assert str(home) not in chooser_values(listings, "property_id")
    sell(app, controllers, first, sale_date="2005-02-01")
    assert row_for(properties, home.id)[1] == "Sold"
    assert str(home) in chooser_values(listings, "property_id")

    second = list_home("2005-03-01")
    assert second.id != first.id
    assert row_for(listings, first.id)[1] == "Sold"
    assert row_for(listings, second.id)[1] == "Available"
    assert row_for(properties, home.id)[1] == "Available"
    assert dialogs.errors == []


def test_delete_needs_confirmation(app, dialogs, seeded):
    tab = tab_named(app, "Sales")
    select_row(app, tab)
    dialogs.confirm = False
    before = seeded.sales.count()
    tab._delete()
    assert seeded.sales.count() == before


def test_selecting_a_home_shows_its_photo(app, seeded):
    tab = tab_named(app, "Properties")
    assert isinstance(tab, PropertiesTab)
    index = next(i for i, r in enumerate(tab.table._rows) if r[-1] == "Yes")
    select_row(app, tab, index)
    assert tab._preview._photo is not None
    tab.clear()
    assert tab._preview._photo is None


def test_attaching_a_photo_keeps_it_on_screen(app, dialogs, tmp_path, monkeypatch):
    tab = tab_named(app, "Properties")
    index = next(i for i, r in enumerate(tab.table._rows) if r[-1] == "No")
    select_row(app, tab, index)
    path = tmp_path / "house.png"
    path.write_bytes(draw_house((1, 2, 3), 1))
    monkeypatch.setattr(
        gui.properties_tab.filedialog, "askopenfilename", lambda **_: str(path)
    )
    tab._attach()
    assert dialogs.errors == []
    assert tab._preview._photo is not None


def test_every_report_runs_from_the_tab(app, dialogs):
    tab = tab_named(app, "Reports")
    assert isinstance(tab, ReportsTab)
    for title in tab._reports:
        tab._chosen.set(title)
        tab._choose()
        tab._run()
        app.update()
        assert tab._table._rows, title
    assert dialogs.errors == []


def test_picture_report_shows_a_photo(app):
    tab = tab_named(app, "Reports")
    tab._chosen.set("Most expensive homes")
    tab._choose()
    tab._run()
    app.update()
    assert tab._preview._photo is not None
