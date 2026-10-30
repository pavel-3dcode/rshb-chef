import pytest

from app import create_app


@pytest.mark.parametrize("path", [
    "/menu",
    "/api/recommendations",
    "/api/cart/validate",
    "/api/menu/add/validate",
])
def test_unavailable_database_returns_503(tmp_path, path):
    app = create_app()
    app.config.update(
        TESTING=True,
        ADMIN_DB_PATH=tmp_path / "missing" / "menu.db",
    )
    client = app.test_client()

    if path == "/menu":
        response = client.get(path)
    else:
        response = client.post(
            path,
            json={
                "stage": "before_order",
                "dish_id": 1,
            },
        )

    assert response.status_code == 503

    if path.startswith("/api/"):
        assert response.is_json
        assert "error" in response.get_json()
