from datetime import date
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Allowed requirement tags
# ---------------------------------------------------------------------------
RequirementTag = Literal["kosher", "parking", "car_rental", "kids_friendly"]

# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class SearchFlightsInput(BaseModel):
    destination: str = Field(..., description="IATA city/airport code or full city name, e.g. 'TLV' or 'New York'")
    departure_date: date = Field(..., description="Departure date in YYYY-MM-DD format")
    return_date: date = Field(..., description="Return date in YYYY-MM-DD format")
    passengers: int = Field(..., ge=1, le=9, description="Number of passengers (1-9)")

    @field_validator("return_date")
    @classmethod
    def return_after_departure(cls, v: date, info) -> date:
        departure = info.data.get("departure_date")
        if departure and v <= departure:
            raise ValueError("return_date must be after departure_date")
        return v


class FindHotelsInput(BaseModel):
    location: str = Field(..., description="City or region to search hotels in")
    check_in: date = Field(..., description="Check-in date in YYYY-MM-DD format")
    check_out: date = Field(..., description="Check-out date in YYYY-MM-DD format")
    requirements: list[RequirementTag] = Field(
        default_factory=list,
        description="List of required hotel features: kosher, parking, car_rental, kids_friendly",
    )

    @field_validator("check_out")
    @classmethod
    def checkout_after_checkin(cls, v: date, info) -> date:
        check_in = info.data.get("check_in")
        if check_in and v <= check_in:
            raise ValueError("check_out must be after check_in")
        return v


# ---------------------------------------------------------------------------
# Mock hotel database
# ---------------------------------------------------------------------------

_MOCK_HOTELS = [
    {
        "id": 1,
        "name": "Grand Kosher Resort",
        "stars": 5,
        "price_per_night_usd": 320,
        "features": {"kosher", "parking", "kids_friendly"},
    },
    {
        "id": 2,
        "name": "City Center Suites",
        "stars": 4,
        "price_per_night_usd": 180,
        "features": {"parking", "car_rental"},
    },
    {
        "id": 3,
        "name": "Family Paradise Hotel",
        "stars": 4,
        "price_per_night_usd": 210,
        "features": {"kids_friendly", "parking", "kosher"},
    },
    {
        "id": 4,
        "name": "Budget Stay Inn",
        "stars": 3,
        "price_per_night_usd": 90,
        "features": set(),
    },
    {
        "id": 5,
        "name": "The Kosher Pearl",
        "stars": 4,
        "price_per_night_usd": 260,
        "features": {"kosher"},
    },
    {
        "id": 6,
        "name": "Traveler's Hub",
        "stars": 3,
        "price_per_night_usd": 130,
        "features": {"parking", "car_rental", "kids_friendly"},
    },
    {
        "id": 7,
        "name": "Luxury Palace",
        "stars": 5,
        "price_per_night_usd": 500,
        "features": {"parking", "car_rental", "kids_friendly", "kosher"},
    },
]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool(args_schema=SearchFlightsInput)
def search_flights(
    destination: str,
    departure_date: date,
    return_date: date,
    passengers: int,
) -> dict:
    """Search for available flights to a destination and return mock flight options."""
    nights = (return_date - departure_date).days
    base_price = 350

    return {
        "destination": destination,
        "departure_date": str(departure_date),
        "return_date": str(return_date),
        "passengers": passengers,
        "nights": nights,
        "flights": [
            {
                "flight_id": "AA1042",
                "airline": "American Airlines",
                "departure_time": f"{departure_date}T08:30:00",
                "arrival_time": f"{departure_date}T14:45:00",
                "price_per_person_usd": base_price,
                "total_price_usd": base_price * passengers,
                "stops": 0,
            },
            {
                "flight_id": "LY315",
                "airline": "El Al",
                "departure_time": f"{departure_date}T11:00:00",
                "arrival_time": f"{departure_date}T18:20:00",
                "price_per_person_usd": base_price - 40,
                "total_price_usd": (base_price - 40) * passengers,
                "stops": 1,
            },
            {
                "flight_id": "UA789",
                "airline": "United Airlines",
                "departure_time": f"{departure_date}T22:15:00",
                "arrival_time": f"{return_date}T06:30:00",
                "price_per_person_usd": base_price + 60,
                "total_price_usd": (base_price + 60) * passengers,
                "stops": 0,
            },
        ],
    }


@tool(args_schema=FindHotelsInput)
def find_hotels(
    location: str,
    check_in: date,
    check_out: date,
    requirements: list[RequirementTag],
) -> dict:
    """Find hotels in a location that satisfy all specified requirements."""
    required = set(requirements)
    nights = (check_out - check_in).days

    matched = [
        hotel
        for hotel in _MOCK_HOTELS
        if required.issubset(hotel["features"])
    ]

    results = [
        {
            "id": h["id"],
            "name": h["name"],
            "stars": h["stars"],
            "price_per_night_usd": h["price_per_night_usd"],
            "total_price_usd": h["price_per_night_usd"] * nights,
            "features": sorted(h["features"]),
        }
        for h in matched
    ]

    return {
        "location": location,
        "check_in": str(check_in),
        "check_out": str(check_out),
        "nights": nights,
        "requirements": list(required),
        "results_count": len(results),
        "hotels": results,
    }
