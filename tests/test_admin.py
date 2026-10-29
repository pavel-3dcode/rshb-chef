import re
import shutil
import sqlite3
from pathlib import Path
import pytest
from werkzeug.security import generate_password_hash

from app import create_app


@pytest.fixture
def admin_client(monkeypatch):
    monkeypatch.setenv("RSHB_SECRET_KEY", "test-only-secret")
    monkeypatch.setenv("RSHB_ADMIN_USER", "admin")
    monkeypatch.setenv(
        "RSHB_ADMIN_PASSWORD_HASH",
        generate_password_hash("test-password"),
    )

    app = create_app()
    app.config["TESTING"] = True

    return app.test_client()


def get_csrf_token(client):
    response = client.get("/admin/login")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    return re.search(
        r'name="csrf_token"\s+value="([^"]+)"',
        html,
    ).group(1)


def test_admin_requires_login(admin_client):
    response = admin_client.get("/admin/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/login")


def test_admin_login_success(admin_client):
    token = get_csrf_token(admin_client)

    response = admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")
    assert admin_client.get("/admin/").status_code == 200


def test_admin_rejects_wrong_password(admin_client):
    token = get_csrf_token(admin_client)

    response = admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "wrong-password",
            "csrf_token": token,
        },
    )

    assert response.status_code == 401
    assert admin_client.get("/admin/").status_code == 302


def test_admin_rejects_missing_csrf(admin_client):
    response = admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
        },
    )

    assert response.status_code == 400


def test_admin_rejects_invalid_csrf(admin_client):
    get_csrf_token(admin_client)

    response = admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
            "csrf_token": "invalid-token",
        },
    )

    assert response.status_code == 400

def test_admin_logout(admin_client):
    token = get_csrf_token(admin_client)

    response = admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )

    assert response.status_code == 302

    with admin_client.session_transaction() as session:
        logout_token = session["csrf_token"]

    response = admin_client.post(
        "/admin/logout",
        data={"csrf_token": logout_token},
    )

    assert response.status_code == 302
    assert admin_client.get("/admin/").status_code == 302


def test_admin_logout_requires_csrf(admin_client):
    token = get_csrf_token(admin_client)

    admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )

    response = admin_client.post("/admin/logout")

    assert response.status_code == 400
    assert admin_client.get("/admin/").status_code == 200

def test_availability_requires_login(admin_client):
    response = admin_client.post(
        "/admin/dishes/9/availability",
        data={"available": "0"},
    )

    assert response.status_code == 403


def test_availability_requires_csrf(admin_client):
    token = get_csrf_token(admin_client)

    admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )

    response = admin_client.post(
        "/admin/dishes/9/availability",
        data={"available": "0"},
    )

    assert response.status_code == 400

def test_availability_update_success(admin_client, tmp_path):
    source = Path(__file__).resolve().parent.parent / "instance" / "rshb_chef.db"
    test_db = tmp_path / "test.db"
    shutil.copy2(source, test_db)

    admin_client.application.config["ADMIN_DB_PATH"] = test_db

    token = get_csrf_token(admin_client)

    login_response = admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )

    assert login_response.status_code == 302

    with admin_client.session_transaction() as admin_session:
        token = admin_session["csrf_token"]

    response = admin_client.post(
        "/admin/dishes/9/availability",
        data={
            "csrf_token": token,
            "available": "0",
        },
    )

    assert response.status_code == 302

    connection = sqlite3.connect(test_db)
    try:
        row = connection.execute(
            "SELECT available FROM dishes WHERE id = 9"
        ).fetchone()
        assert row[0] == 0
    finally:
        connection.close()

def test_price_requires_login(admin_client):
    response = admin_client.post(
        "/admin/dishes/9/price",
        data={"price_kopeck": "75000"},
    )

    assert response.status_code == 403


def test_price_requires_csrf(admin_client):
    token = get_csrf_token(admin_client)

    admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )

    response = admin_client.post(
        "/admin/dishes/9/price",
        data={"price_kopeck": "75000"},
    )

    assert response.status_code == 400


def test_price_update_success(admin_client, tmp_path):
    source = Path(__file__).resolve().parent.parent / "instance" / "rshb_chef.db"
    test_db = tmp_path / "test.db"
    shutil.copy2(source, test_db)

    admin_client.application.config["ADMIN_DB_PATH"] = test_db

    token = get_csrf_token(admin_client)

    response = admin_client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )
    assert response.status_code == 302

    with admin_client.session_transaction() as admin_session:
        token = admin_session["csrf_token"]

    response = admin_client.post(
        "/admin/dishes/9/price",
        data={
            "csrf_token": token,
            "price_kopeck": "75000",
        },
    )

    assert response.status_code == 302

    connection = sqlite3.connect(test_db)
    try:
        row = connection.execute(
            "SELECT price_kopeck FROM dishes WHERE id = 9"
        ).fetchone()
        assert row[0] == 75000
    finally:
        connection.close()

def test_restaurant_rules_update_success(admin_client, tmp_path):
    source = Path(__file__).resolve().parent.parent / "instance" / "rshb_chef.db"
    test_db = tmp_path / "test.db"
    shutil.copy2(source, test_db)

    admin_client.application.config["ADMIN_DB_PATH"] = test_db

    token = get_csrf_token(admin_client)

    response = admin_client.post(
        "/admin/login",
        data = {
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )
    assert response.status_code == 302

    with admin_client.session_transaction() as admin_session:
        token = admin_session["csrf_token"]

    response = admin_client.post(
        "/admin/rules",
        data = {
            "csrf_token": token,
            "preference_weight": "4",
            "pairing_weight": "5",
            "category_weight": "2",
            "enabled": "1",
        },
    )

    assert response.status_code == 302

    connection = sqlite3.connect(test_db)
    try:
        row = connection.execute(
            """
            SELECT preference_weight, pairing_weight,
                   category_weight, enabled
            FROM restaurant_rules
            WHERE restaurant_id = 1
            """
        ).fetchone()

        assert row == (4, 5, 2, 1)
    finally:
        connection.close()

def test_rules_require_login(admin_client):
    response = admin_client.post(
        "/admin/rules",
        data = {
            "preference_weight": "2",
            "pairing_weight": "3",
            "category_weight": "1",
            "enabled": "1",
        },
    )

    assert response.status_code == 403


def test_rules_require_csrf(admin_client):
    token = get_csrf_token(admin_client)

    admin_client.post(
        "/admin/login",
        data = {
            "username": "admin",
            "password": "test-password",
            "csrf_token": token,
        },
    )

    response = admin_client.post(
        "/admin/rules",
        data = {
            "preference_weight": "2",
            "pairing_weight": "3",
            "category_weight": "1",
            "enabled": "1",
        },
    )

    assert response.status_code == 400


def test_disabled_recommendations_return_empty(admin_client):
    from app.integration import load_menu
    from app.recommendations import recommend, GuestContext

    menu = load_menu(1)
    menu.enabled = False

    guest = GuestContext(
        restaurant_id = 1,
        stage = "before_order",
    )

    assert recommend(menu, guest) == []
