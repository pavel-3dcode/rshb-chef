from types import SimpleNamespace
import pytest

from app.validation import validate_guest_json
from app.validation import build_guest_context

def test_valid_full_json():
    data = {
        "stage": "after_main",
        "budget_kopeck": 100000,
        "cart_dish_ids": [1, 2],
        "allergies": ["milk"],
        "restrictions": ["vegan"],
        "preferences": ["spicy"],
        "age_confirmed": False,
        "recommendations_enabled": True
    }

    assert validate_guest_json(data) == data


@pytest.mark.parametrize("data", [
    None,
    [],
    {"stage": "unknown"},
    {"stage": True},
    {"stage": "before_order", "budget_kopeck": -1},
    {"stage": "before_order", "budget_kopeck": True},
    {"stage": "before_order", "budget_kopeck": 12.5},
    {"stage": "before_order", "cart_dish_ids": [1, 1]},
    {"stage": "before_order", "cart_dish_ids": [True]},
    {"stage": "before_order", "allergies": "milk"},
    {"stage": "before_order", "restrictions": [123]},
    {"stage": "before_order", "preferences": ["spicy", "spicy"]},
    {"stage": "before_order", "age_confirmed": "true"},
    {"stage": "before_order", "recommendations_enabled": 0}
])
def test_invalid_json(data):
    with pytest.raises(ValueError):
        validate_guest_json(data)


def test_defaults():
    result = validate_guest_json({"stage": "before_order"})

    assert result["budget_kopeck"] is None
    assert result["cart_dish_ids"] == []
    assert result["allergies"] == []
    assert result["restrictions"] == []
    assert result["preferences"] == []
    assert result["age_confirmed"] is False
    assert result["recommendations_enabled"] is True

@pytest.fixture
def sample_menu():
    return SimpleNamespace(
        restaurant_id=1,
        dishes=[
            SimpleNamespace(id=1, restaurant_id=1),
            SimpleNamespace(id=2, restaurant_id=1),
            SimpleNamespace(id=3, restaurant_id=2),
        ],
    )


def test_full_guest_context(sample_menu):
    data = {
        "stage": "after_main",
        "budget_kopeck": 100000,
        "cart_dish_ids": [1, 2],
        "allergies": ["Milk"],
        "restrictions": ["vegan"],
        "preferences": ["fresh"],
        "age_confirmed": False,
        "recommendations_enabled": True,
    }

    guest = build_guest_context(data, sample_menu)

    assert guest.restaurant_id == 1
    assert guest.stage == "after_main"
    assert guest.cart_dish_ids == [1, 2]
    assert guest.allergies == {"Milk"}
    assert guest.restrictions == {"vegan"}
    assert guest.preferences == {"fresh"}
    assert guest.age_confirmed is False


@pytest.mark.parametrize("changes", [
    {"allergies": ["Unknown"]},
    {"allergies": ["milk"]},
    {"restrictions": ["unknown"]},
    {"preferences": ["spicy"]},
    {"cart_dish_ids": [999]},
    {"cart_dish_ids": [3]},
])
def test_guest_context_invalid_values(sample_menu, changes):
    data = {"stage": "before_order", **changes}

    with pytest.raises(ValueError):
        build_guest_context(data, sample_menu)


def test_guest_context_wrong_restaurant(sample_menu):
    with pytest.raises(ValueError):
        build_guest_context(
            {"stage": "before_order"},
            sample_menu, restaurant_id=2,
        )
