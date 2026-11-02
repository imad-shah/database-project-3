from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Town:
    city: str
    zip_code: str
    district: str
    min_price: int
    max_price: int


TOWNS = (
    Town("Bethlehem", "18015", "Bethlehem Area", 150_000, 350_000),
    Town("Bethlehem", "18017", "Bethlehem Area", 180_000, 400_000),
    Town("Allentown", "18104", "Parkland", 200_000, 550_000),
    Town("Allentown", "18102", "Allentown City", 90_000, 240_000),
    Town("Orefield", "18069", "Parkland", 280_000, 650_000),
    Town("Schnecksville", "18078", "Parkland", 220_000, 480_000),
    Town("Easton", "18042", "Easton Area", 120_000, 320_000),
    Town("Emmaus", "18049", "East Penn", 180_000, 420_000),
    Town("Nazareth", "18064", "Nazareth Area", 170_000, 380_000),
    Town("Whitehall", "18052", "Whitehall-Coplay", 140_000, 300_000),
)

FIRST_NAMES = (
    "Alex",
    "Blair",
    "Casey",
    "Dana",
    "Elliot",
    "Farah",
    "Gabriel",
    "Hana",
    "Imani",
    "Jordan",
    "Kai",
    "Lena",
    "Mateo",
    "Nadia",
    "Omar",
    "Priya",
    "Quinn",
    "Rosa",
    "Sam",
    "Tara",
    "Uma",
    "Victor",
    "Wren",
    "Yusuf",
    "Zoe",
)

LAST_NAMES = (
    "Adler",
    "Brooks",
    "Chen",
    "Diaz",
    "Eriksen",
    "Fischer",
    "Garcia",
    "Hassan",
    "Ito",
    "Jensen",
    "Kowalski",
    "Lopez",
    "Moyer",
    "Nguyen",
    "Okafor",
    "Patel",
    "Reyes",
    "Schmidt",
    "Thomas",
    "Unger",
    "Vargas",
    "Weiss",
    "Young",
    "Zimmerman",
)

STREET_NAMES = (
    "Linden",
    "Main",
    "Maple",
    "Oak",
    "Cedar",
    "Chestnut",
    "Walnut",
    "Spruce",
    "Hanover",
    "Monocacy",
    "Lehigh",
    "Saucon",
    "Hamilton",
    "Cherokee",
    "Fairview",
    "Highland",
    "Delaware",
    "Church",
    "Mill",
    "Orchard",
)

STREET_SUFFIXES = ("St", "Ave", "Rd", "Ln", "Dr", "Ct", "Way")
