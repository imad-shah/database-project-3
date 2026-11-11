from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from statistics import mean

import pytest

from controller import AppError


def report_named(controllers, title):
    return next(r for r in controllers.reports.reports if r.title == title)


def run(controllers, title, **overrides):
    report = report_named(controllers, title)
    values = {param.name: param.initial() for param in report.params}
    return controllers.reports.run(report, values | overrides)


def column(result, name):
    index = result.columns.index(name)
    return [row[index] for row in result.rows]


def money(value):
    return f"{value:,.2f}"


def for_sale(seeded):
    homes = {h.property_id: h for h in seeded.properties.find_all()}
    return [(homes[lst.property_id], lst) for lst in seeded.listings.find_available()]


def test_every_report_has_an_interesting_answer(seeded, controllers):
    for report in controllers.reports.reports:
        assert run(controllers, report.title).rows, report.title


def test_homes_by_city_and_price(seeded, controllers):
    expected = {
        h.street
        for h, lst in for_sale(seeded)
        if h.city == "Bethlehem" and 200_000 <= lst.asking_price <= 250_000
    }
    result = run(controllers, "Homes by city and price")
    assert set(column(result, "Street")) == expected
    assert "44 Lehigh Ave" in expected


def test_city_search_ignores_case(seeded, controllers):
    assert (
        run(controllers, "Homes by city and price", city="bethlehem").rows
        == run(controllers, "Homes by city and price").rows
    )


def test_sold_homes_are_excluded_from_for_sale_searches(seeded, controllers):
    wide = {"min_price": "1", "max_price": "99999999", "city": "Orefield"}
    result = run(controllers, "Homes by city and price", **wide)
    assert "12 Parkland Manor Ct" not in column(result, "Street")


def test_homes_by_district(seeded, controllers):
    expected = {
        h.street
        for h, _ in for_sale(seeded)
        if h.school_district == "Parkland" and h.bedrooms >= 4 and not h.has_pool
    }
    result = run(controllers, "Homes by school district")
    assert set(column(result, "Street")) == expected
    assert set(column(result, "Pool")) == {"No"}


def yearly_sales(seeded, year):
    return [s for s in seeded.sales.find_all() if s.sale_date.year == year]


def test_top_agent(seeded, controllers):
    totals = defaultdict(Decimal)
    for sale in yearly_sales(seeded, 2004):
        totals[sale.selling_agent_id] += sale.sale_price
    best = max(totals.values())
    expected = {
        seeded.agents.find(agent_id).full_name
        for agent_id, total in totals.items()
        if total == best
    }
    result = run(controllers, "Top agent of the year")
    assert set(column(result, "Agent")) == expected
    assert set(column(result, "Total Sales ($)")) == {money(best)}


def test_top_agent_reports_ties(seeded, controllers):
    sales = yearly_sales(seeded, 2004)
    agent_totals = defaultdict(list)
    for sale in sales:
        agent_totals[sale.selling_agent_id].append(sale)
    first, second, *_ = list(agent_totals.values())
    for sale in sales:
        sale.sale_price = Decimal(1)
        seeded.sales.save(sale)
    first[0].sale_price = Decimal(9_000_000 - len(first))
    second[0].sale_price = Decimal(9_000_000 - len(second))
    seeded.sales.save(first[0])
    seeded.sales.save(second[0])
    assert len(run(controllers, "Top agent of the year").rows) == 2


def test_agent_performance_covers_each_agent(seeded, controllers):
    listing_dates = {
        lst.listing_id: lst.listing_date for lst in seeded.listings.find_all()
    }
    grouped = defaultdict(list)
    for sale in yearly_sales(seeded, 2004):
        grouped[sale.selling_agent_id].append(sale)
    result = run(controllers, "Agent performance")
    assert len(result.rows) == seeded.agents.count()
    for name, row in zip(column(result, "Agent"), result.rows):
        agent = next(a for a in seeded.agents.find_all() if a.full_name == name)
        sales = grouped[agent.agent_id]
        price = mean(s.sale_price for s in sales).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        days = mean((s.sale_date - listing_dates[s.listing_id]).days for s in sales)
        assert row[1] == str(len(sales))
        assert row[2] == money(price)
        assert abs(Decimal(row[3]) - Decimal(str(days))) < Decimal("0.06")


def test_agent_without_sales_still_appears(seeded, controllers):
    result = run(controllers, "Agent performance", year="1999")
    assert set(column(result, "Homes Sold")) == {"0"}
    assert set(column(result, "Average Sale Price ($)")) == {""}


def test_most_expensive_homes_includes_ties_and_sold_prices(seeded, controllers):
    result = run(controllers, "Most expensive homes")
    assert set(column(result, "Street")) == {
        "900 Saucon Valley Rd",
        "12 Parkland Manor Ct",
    }
    assert set(column(result, "Status")) == {"Available", "Sold"}


def test_every_most_expensive_home_has_a_picture(seeded, controllers):
    result = run(controllers, "Most expensive homes")
    for property_id in column(result, "Property ID"):
        assert controllers.reports.image(property_id).startswith(b"\x89PNG")


def test_only_some_homes_have_pictures(seeded):
    assert sum(1 for h in seeded.properties.find_all() if h.has_photo) == 3


def test_buyer_matches_respect_preferences(seeded, controllers):
    buyer = seeded.buyers.find_all()[0]
    result = controllers.reports.run(
        report_named(controllers, "Homes matching a buyer"),
        {"buyer_id": str(buyer.buyer_id)},
    )
    expected = {
        h.street
        for h, lst in for_sale(seeded)
        if lst.asking_price <= buyer.max_budget
        and h.bedrooms >= buyer.min_bedrooms
        and (buyer.preferred_city is None or h.city == buyer.preferred_city)
    }
    assert set(column(result, "Street")) == expected


def test_slow_listings_meet_the_threshold(seeded, controllers):
    result = run(controllers, "Slow-moving listings", min_days="120")
    days = [int(value) for value in column(result, "Days on Market")]
    assert days and min(days) >= 120
    assert days == sorted(days, reverse=True)


def test_market_summary_counts_sales(seeded, controllers):
    result = run(controllers, "Market summary by city")
    sold = sum(int(value) for value in column(result, "Homes Sold"))
    assert sold == len(yearly_sales(seeded, 2004))


def test_bad_report_input_is_explained(seeded, controllers):
    with pytest.raises(AppError, match="Year must be a whole number"):
        run(controllers, "Agent performance", year="last year")


def test_impossible_year_is_explained(seeded, controllers):
    with pytest.raises(AppError, match="out of range"):
        run(controllers, "Agent performance", year="0")


def test_report_input_cannot_inject_sql(seeded, controllers):
    attack = "x'; DROP TABLE sales; --"
    assert run(controllers, "Homes by city and price", city=attack).rows == []
    assert seeded.sales.count() > 0


def test_seed_is_repeatable(seeded, con):
    from seed import populate, reset

    def snapshot():
        return [
            (lst.street, lst.asking_price, lst.listing_date, lst.status)
            for lst in seeded.listings.find_all()
        ]

    first = snapshot()
    reset(con)
    populate(seeded)
    assert snapshot() == first


def test_seed_has_a_home_that_sold_and_was_relisted(seeded):
    listings = [
        lst for lst in seeded.listings.find_all() if lst.street == "75 Ferry St"
    ]
    assert sorted(lst.status for lst in listings) == ["Available", "Sold"]
    assert len({lst.seller_id for lst in listings}) == 2
    assert len({lst.property_id for lst in listings}) == 1
