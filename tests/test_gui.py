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
        "Asking Price",
        "Photo",
    )
    assert len(tab.table._tree.cget("columns")) == len(tab.controller.spec.fields)


@pytest.mark.parametrize("name", ["Properties", "Sales", "Agents", "Buyers", "Sellers"])
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
    assert tab.form.values()["property_id"] == ""
    assert tab.form.values()["buyer_id"] == ""


def test_invalid_save_shows_an_error(app, dialogs):
    tab = tab_named(app, "Agents")
    tab._save()
    assert dialogs.errors == ["First Name is required."]


def test_sale_form_offers_only_available_homes(app, controllers):
    tab = tab_named(app, "Sales")
    chooser = next(c for f, c in tab.form._choosers if f.name == "property_id")
    offered = set(chooser.cget("values"))
    available = {str(o) for o in controllers.properties.available_options()}
    assert offered == available


def test_recording_a_sale_updates_other_tabs(app, dialogs, controllers):
    sales = tab_named(app, "Sales")
    properties = tab_named(app, "Properties")
    option = controllers.properties.available_options()[0]
    sales.form.fill(
        {
            "property_id": str(option),
            "buyer_id": str(controllers.buyers.options()[0]),
            "selling_agent_id": str(controllers.agents.options()[0]),
            "sale_price": "$240,000",
            "sale_date": "2005-04-12",
        }
    )
    sales._save()
    assert dialogs.errors == []
    assert dialogs.infos == ["Sale saved."]
    assert str(option) not in sales.form._choosers[0][1].cget("values")
    row = next(r for r in properties.table._rows if r[0] == str(option.id))
    assert "Sold" in row


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
