
import pytest

from app import create_app
from app.integration import load_menu


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_valid_recommendations(client):
    response = client.post(
        "/api/recommendations",
        json={"stage": "before_order", "budget_kopeck": 40000},
    )

    assert response.status_code == 200

    results = response.get_json()
    assert isinstance(results, list)
    assert len(results) <= 3
    assert all(item["price_kopeck"] <= 40000 for item in results)


def test_allergy_excludes_conflicting_dishes(client):
    menu = load_menu(1)
    dishes = {dish.id: dish for dish in menu.dishes}

    response = client.post(
        "/api/recommendations",
        json={"stage": "before_order", "allergies": ["Milk"]},
    )

    assert response.status_code == 200

    for item in response.get_json():
        dish = dishes[item["dish_id"]]
        assert dish.allergens_verified
        assert "Milk" not in dish.allergens


def test_opt_out_returns_empty_list(client):
    response = client.post(
        "/api/recommendations",
        json={
            "stage": "before_order",
            "recommendations_enabled": False,
        },
    )

    assert response.status_code == 200
    assert response.get_json() == []


@pytest.mark.parametrize("data", [
    {"stage": "invalid"},
    {"stage": "before_order", "budget_kopeck": True},
    {"stage": "before_order", "allergies": ["unknown"]},
    {"stage": "before_order", "restrictions": ["unknown"]},
    {"stage": "before_order", "cart_dish_ids": [999999]},
    {"stage": "before_order", "age_confirmed": "true"},
    {"stage": "before_order", "recommendations_enabled": 0},
])
def test_invalid_requests_return_400(client, data):
    response = client.post("/api/recommendations", json=data)

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_non_object_json_returns_400(client):
    response = client.post("/api/recommendations", json=[])

    assert response.status_code == 400


def test_recommendation_does_not_repeat_cart(client):
    response = client.post(
        "/api/recommendations",
        json={
            "stage": "before_order",
            "cart_dish_ids": [15],
        },
    )

    assert response.status_code == 200
    assert all(item["dish_id"] != 15 for item in response.get_json())


def test_unknown_age_excludes_alcohol(client):
    menu = load_menu(1)
    dishes = {dish.id: dish for dish in menu.dishes}

    response = client.post(
        "/api/recommendations",
        json={"stage": "before_order"},
    )

    assert response.status_code == 200

    for item in response.get_json():
        assert not dishes[item["dish_id"]].is_alcohol
