_ADDRESS = (
    'l.street AS "Street", l.city AS "City", l.state AS "State", l.zip_code AS "ZIP"'
)
_AGENT_NAME = "a.first_name || ' ' || a.last_name"
_SOLD_IN_YEAR = """
    s.sale_date >= make_date(%(year)s::int, 1, 1)
    AND s.sale_date < make_date(%(year)s::int + 1, 1, 1)
"""

HOMES_BY_CITY_AND_PRICE = f"""
SELECT {_ADDRESS}, l.asking_price AS "Asking Price ($)"
FROM property_listings l
WHERE l.status = 'Available'
  AND lower(l.city) = lower(%(city)s)
  AND l.asking_price BETWEEN %(min_price)s AND %(max_price)s
ORDER BY l.asking_price
"""

HOMES_BY_DISTRICT = f"""
SELECT {_ADDRESS}, l.bedrooms AS "Bedrooms", l.has_pool AS "Pool",
       l.asking_price AS "Asking Price ($)"
FROM property_listings l
WHERE l.status = 'Available'
  AND lower(l.school_district) = lower(%(district)s)
  AND l.bedrooms >= %(min_bedrooms)s
  AND l.has_pool = %(has_pool)s
ORDER BY l.asking_price
"""

TOP_AGENT_BY_SALES = f"""
WITH totals AS (
    SELECT s.selling_agent_id,
           SUM(s.sale_price) AS total,
           COUNT(*) AS homes,
           RANK() OVER (ORDER BY SUM(s.sale_price) DESC) AS position
    FROM sales s
    WHERE {_SOLD_IN_YEAR}
    GROUP BY s.selling_agent_id
)
SELECT {_AGENT_NAME} AS "Agent", t.homes AS "Homes Sold", t.total AS "Total Sales ($)"
FROM totals t
JOIN agents a ON a.agent_id = t.selling_agent_id
WHERE t.position = 1
ORDER BY "Agent"
"""

AGENT_PERFORMANCE = f"""
SELECT {_AGENT_NAME} AS "Agent",
       COUNT(s.sale_id) AS "Homes Sold",
       ROUND(AVG(s.sale_price), 2) AS "Average Sale Price ($)",
       ROUND(AVG(s.sale_date - p.listing_date), 1) AS "Average Days on Market"
FROM agents a
LEFT JOIN sales s ON s.selling_agent_id = a.agent_id AND {_SOLD_IN_YEAR}
LEFT JOIN properties p ON p.property_id = s.property_id
GROUP BY a.agent_id, a.first_name, a.last_name
ORDER BY "Average Sale Price ($)" DESC NULLS LAST, "Agent"
"""

MOST_EXPENSIVE_HOMES = f"""
SELECT l.property_id AS "Property ID", {_ADDRESS}, l.status AS "Status", l.price AS "Price ($)"
FROM property_listings l
WHERE l.price = (SELECT MAX(price) FROM property_listings)
ORDER BY l.property_id
"""

HOMES_FOR_BUYER = f"""
SELECT {_ADDRESS}, l.bedrooms AS "Bedrooms", l.asking_price AS "Asking Price ($)"
FROM buyers b
JOIN property_listings l
  ON l.status = 'Available'
 AND (b.max_budget IS NULL OR l.asking_price <= b.max_budget)
 AND (b.min_bedrooms IS NULL OR l.bedrooms >= b.min_bedrooms)
 AND (b.preferred_city IS NULL OR lower(l.city) = lower(b.preferred_city))
WHERE b.buyer_id = %(buyer_id)s
ORDER BY l.asking_price
"""

STALE_LISTINGS = f"""
SELECT {_ADDRESS}, {_AGENT_NAME} AS "Listing Agent",
       %(as_of)s::date - l.listing_date AS "Days on Market",
       l.asking_price AS "Asking Price ($)"
FROM property_listings l
JOIN agents a ON a.agent_id = l.listing_agent_id
WHERE l.status = 'Available'
  AND %(as_of)s::date - l.listing_date >= %(min_days)s
ORDER BY "Days on Market" DESC
"""

MARKET_BY_CITY = f"""
SELECT p.city AS "City",
       COUNT(*) AS "Homes Sold",
       ROUND(AVG(s.sale_price), 2) AS "Average Sale Price ($)",
       ROUND(100 * SUM(s.sale_price) / SUM(p.asking_price), 1) AS "Sale Price vs Asking (percent)"
FROM sales s
JOIN properties p ON p.property_id = s.property_id
WHERE {_SOLD_IN_YEAR}
GROUP BY p.city
ORDER BY "Homes Sold" DESC, "City"
"""
