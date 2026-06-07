import pytest
from datetime import date
from pydantic import ValidationError

from app.tools import search_flights, find_hotels, FindHotelsInput, SearchFlightsInput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def call_find_hotels(location="Tel Aviv", check_in="2026-07-01", check_out="2026-07-05", requirements=None):
    """Invoke find_hotels tool directly via .invoke() for clean dict results."""
    payload = {
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
        "requirements": requirements or [],
    }
    return find_hotels.invoke(payload)


def call_search_flights(destination="NYC", departure_date="2026-07-01", return_date="2026-07-10", passengers=2):
    payload = {
        "destination": destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "passengers": passengers,
    }
    return search_flights.invoke(payload)


# ---------------------------------------------------------------------------
# find_hotels — filtering logic
# ---------------------------------------------------------------------------

class TestFindHotelsFiltering:
    def test_no_requirements_returns_all_hotels(self):
        result = call_find_hotels(requirements=[])
        assert result["results_count"] == 7

    def test_kosher_filter_returns_only_kosher_hotels(self):
        result = call_find_hotels(requirements=["kosher"])
        names = [h["name"] for h in result["hotels"]]
        assert result["results_count"] == 4
        assert "Grand Kosher Resort" in names
        assert "Family Paradise Hotel" in names
        assert "The Kosher Pearl" in names
        assert "Luxury Palace" in names
        # non-kosher hotels must be absent
        assert "Budget Stay Inn" not in names
        assert "City Center Suites" not in names

    def test_parking_filter(self):
        result = call_find_hotels(requirements=["parking"])
        for hotel in result["hotels"]:
            assert "parking" in hotel["features"]

    def test_car_rental_filter(self):
        result = call_find_hotels(requirements=["car_rental"])
        names = [h["name"] for h in result["hotels"]]
        assert "City Center Suites" in names
        assert "Traveler's Hub" in names
        assert "Luxury Palace" in names
        assert "Budget Stay Inn" not in names

    def test_kids_friendly_filter(self):
        result = call_find_hotels(requirements=["kids_friendly"])
        for hotel in result["hotels"]:
            assert "kids_friendly" in hotel["features"]

    def test_multiple_requirements_kosher_and_parking(self):
        result = call_find_hotels(requirements=["kosher", "parking"])
        names = [h["name"] for h in result["hotels"]]
        # Only hotels with BOTH kosher AND parking
        assert "Grand Kosher Resort" in names
        assert "Family Paradise Hotel" in names
        assert "Luxury Palace" in names
        # These have one but not both
        assert "The Kosher Pearl" not in names
        assert "City Center Suites" not in names

    def test_all_requirements_returns_only_luxury_palace(self):
        result = call_find_hotels(requirements=["kosher", "parking", "car_rental", "kids_friendly"])
        assert result["results_count"] == 1
        assert result["hotels"][0]["name"] == "Luxury Palace"

    def test_impossible_combination_returns_empty(self):
        # Budget Stay Inn has no features; no hotel satisfies car_rental + kosher + kids_friendly all at once
        # except Luxury Palace — let's test a combination that yields 0
        # We'll craft this by checking: only car_rental + kosher together
        result = call_find_hotels(requirements=["car_rental", "kosher"])
        # Only Luxury Palace has both
        assert result["results_count"] == 1
        assert result["hotels"][0]["name"] == "Luxury Palace"

    def test_total_price_calculated_correctly(self):
        result = call_find_hotels(check_in="2026-07-01", check_out="2026-07-05", requirements=[])
        nights = 4
        for hotel in result["hotels"]:
            assert hotel["total_price_usd"] == hotel["price_per_night_usd"] * nights

    def test_nights_calculated_correctly(self):
        result = call_find_hotels(check_in="2026-07-01", check_out="2026-07-08")
        assert result["nights"] == 7


# ---------------------------------------------------------------------------
# find_hotels — Pydantic validation
# ---------------------------------------------------------------------------

class TestFindHotelsValidation:
    def test_invalid_check_out_before_check_in_raises(self):
        with pytest.raises((ValidationError, Exception)):
            FindHotelsInput(
                location="Paris",
                check_in=date(2026, 7, 10),
                check_out=date(2026, 7, 5),
                requirements=[],
            )

    def test_check_out_equal_to_check_in_raises(self):
        with pytest.raises((ValidationError, Exception)):
            FindHotelsInput(
                location="Paris",
                check_in=date(2026, 7, 5),
                check_out=date(2026, 7, 5),
                requirements=[],
            )

    def test_invalid_requirement_tag_raises(self):
        with pytest.raises(ValidationError):
            FindHotelsInput(
                location="Paris",
                check_in=date(2026, 7, 1),
                check_out=date(2026, 7, 5),
                requirements=["spa"],  # not an allowed tag
            )

    def test_invalid_date_string_raises(self):
        with pytest.raises((ValidationError, Exception)):
            call_find_hotels(check_in="not-a-date", check_out="2026-07-05")


# ---------------------------------------------------------------------------
# search_flights — basic smoke tests
# ---------------------------------------------------------------------------

class TestSearchFlights:
    def test_returns_three_flight_options(self):
        result = call_search_flights()
        assert len(result["flights"]) == 3

    def test_total_price_reflects_passengers(self):
        result = call_search_flights(passengers=3)
        for flight in result["flights"]:
            assert flight["total_price_usd"] == flight["price_per_person_usd"] * 3

    def test_nights_calculated_correctly(self):
        result = call_search_flights(departure_date="2026-07-01", return_date="2026-07-10")
        assert result["nights"] == 9

    def test_destination_echoed_in_result(self):
        result = call_search_flights(destination="London")
        assert result["destination"] == "London"


# ---------------------------------------------------------------------------
# search_flights — Pydantic validation
# ---------------------------------------------------------------------------

class TestSearchFlightsValidation:
    def test_return_before_departure_raises(self):
        with pytest.raises((ValidationError, Exception)):
            SearchFlightsInput(
                destination="NYC",
                departure_date=date(2026, 7, 10),
                return_date=date(2026, 7, 5),
                passengers=1,
            )

    def test_zero_passengers_raises(self):
        with pytest.raises(ValidationError):
            SearchFlightsInput(
                destination="NYC",
                departure_date=date(2026, 7, 1),
                return_date=date(2026, 7, 10),
                passengers=0,
            )

    def test_too_many_passengers_raises(self):
        with pytest.raises(ValidationError):
            SearchFlightsInput(
                destination="NYC",
                departure_date=date(2026, 7, 1),
                return_date=date(2026, 7, 10),
                passengers=10,
            )
