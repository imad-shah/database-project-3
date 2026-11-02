from datetime import date

import pytest

from controller import AppError
from models import Agent, Buyer


def agent_values(**overrides: str) -> dict[str, str]:
    values = {
        "first_name": "Morgan",
        "last_name": "Rivera",
        "phone": "610-555-0199",
        "email": "morgan@example.com",
        "license_number": "RS1",
        "hire_date": "2005-04-12",
    }
    return values | overrides


def test_new_record_gets_an_id(controllers):
    agent = controllers.agents.save(agent_values())
    assert agent.agent_id is not None
    assert agent.hire_date == date(2005, 4, 12)


def test_saving_with_an_id_updates_in_place(controllers, repositories):
    agent = controllers.agents.save(agent_values())
    controllers.agents.save(
        agent_values(agent_id=str(agent.agent_id), last_name="Reed")
    )
    assert repositories.agents.count() == 1
    assert repositories.agents.find(agent.agent_id).last_name == "Reed"


def test_updating_a_missing_record_is_reported(controllers):
    with pytest.raises(AppError, match="no longer exists"):
        controllers.agents.save(agent_values(agent_id="999"))


def test_deleting_removes_the_record(controllers, repositories):
    agent = controllers.agents.save(agent_values())
    controllers.agents.delete(str(agent.agent_id))
    assert repositories.agents.find(agent.agent_id) is None


def test_deleting_a_missing_record_is_reported(controllers):
    with pytest.raises(AppError, match="no longer exists"):
        controllers.agents.delete("999")


def test_deleting_without_a_selection_is_reported(controllers):
    with pytest.raises(AppError, match="Select a record first"):
        controllers.agents.delete("")


def test_duplicate_license_is_explained(controllers):
    controllers.agents.save(agent_values())
    with pytest.raises(AppError, match="license number"):
        controllers.agents.save(agent_values(email="other@example.com"))


def test_connection_survives_a_rejected_write(controllers, repositories):
    controllers.agents.save(agent_values())
    with pytest.raises(AppError):
        controllers.agents.save(agent_values(email="other@example.com"))
    assert repositories.agents.count() == 1


def test_missing_required_value_is_rejected(controllers):
    with pytest.raises(AppError, match="Last Name is required"):
        controllers.agents.save(agent_values(last_name=" "))


def test_money_out_of_column_range_is_explained(controllers):
    values = {"first_name": "A", "last_name": "B", "max_budget": "1e30"}
    with pytest.raises(AppError, match="out of range"):
        controllers.buyers.save(values)


def test_budget_must_be_positive(controllers):
    values = {"first_name": "A", "last_name": "B", "max_budget": "-1"}
    with pytest.raises(AppError, match="Maximum budget"):
        controllers.buyers.save(values)


def test_optional_buyer_preferences_stay_null(controllers):
    buyer = controllers.buyers.save({"first_name": "A", "last_name": "B"})
    assert isinstance(buyer, Buyer)
    assert buyer.max_budget is None
    assert controllers.buyers.rows()[0][5:8] == ("", "", "")


def test_rows_align_with_spec_fields(controllers):
    agent: Agent = controllers.agents.save(agent_values())
    row = controllers.agents.rows()[0]
    assert len(row) == len(controllers.agents.spec.fields)
    assert row[0] == str(agent.agent_id)
    assert row[-1] == "2005-04-12"


def test_options_use_the_full_name(controllers):
    agent = controllers.agents.save(agent_values())
    assert str(controllers.agents.options()[0]) == f"{agent.agent_id} - Morgan Rivera"
