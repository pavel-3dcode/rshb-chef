import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()

def test_cart_addition_success(client):
    recommendations = client.post(
        "/api/recommendations",
        json={"stage": "before_order", "budget_kopeck": 40000},
    )

    assert recommendations.status_code == 200
    items = recommendations.get_json()
    assert items

    response = client.post(
        "/api/cart/validate",
        json = {"stage": "before_order", "budget_kopeck": 40000, "dish_id": items[0]["dish_id"]},
    )

    assert response.status_code == 200
    assert response.get_json()["validated"] is True
    assert response.get_json()["price_kopeck"] == items[0]["price_kopeck"]


@pytest.mark.parametrize("dish_id", [None, True, -1, 0, "15", 1.5])
def test_invalid_dish_id(client, dish_id):
    response = client.post(
        "/api/cart/validate",
        json = {"stage": "before_order", "dish_id": dish_id}
    )

    assert response.status_code == 400

def test_already_in_cart(client):
    response = client.post(
        "/api/cart/validate",
        json = {"stage": "before_order", "dish_id": 15, "cart_dish_ids": [15]},
    )

    assert response.status_code == 409


def test_invalid_allergy(client):
    response = client.post(
        "/api/cart/validate",
        json = {
        "stage": "before_order",
        "dish_id": 15,
        "allergies": ["unknown"]
        },
    )

    assert response.status_code == 400

def test_opt_out_disallows_recommendation(client):
    response = client.post(
        "/api/cart/validate",
        json={
            "stage": "before_order",
            "dish_id": 15,
            "recommendations_enabled": False,
        },
    )

    assert response.status_code == 409
