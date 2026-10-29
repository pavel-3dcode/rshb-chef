import shutil
import sqlite3
from pathlib import Path

import pytest

from app.admin_data import set_dish_availability, set_dish_price, update_restaurant_rules


@pytest.fixture
def test_db(tmp_path):
    source = Path(__file__).resolve().parent.parent / "instance" / "rshb_chef.db"
    destination = tmp_path / "test.db"

    shutil.copy2(source, destination)

    return destination


def get_availability(db_path, dish_id):
    connection = sqlite3.connect(db_path)

    try:
        row = connection.execute(
            "SELECT available FROM dishes WHERE id = ?",
            (dish_id,),
        ).fetchone()

        return row[0]
    finally:
        connection.close()


def test_disable_dish(test_db):
    set_dish_availability(test_db, 1, 9, False)

    assert get_availability(test_db, 9) == 0


def test_enable_dish(test_db):
    set_dish_availability(test_db, 1, 9, False)
    set_dish_availability(test_db, 1, 9, True)

    assert get_availability(test_db, 9) == 1


def test_unknown_dish_rejected(test_db):
    with pytest.raises(ValueError, match="Dish not found"):
        set_dish_availability(test_db, 1, 99999, False)


def test_wrong_restaurant_rejected(test_db):
    original = get_availability(test_db, 9)

    with pytest.raises(ValueError, match="Dish not found"):
        set_dish_availability(test_db, 999, 9, False)

    assert get_availability(test_db, 9) == original


@pytest.mark.parametrize("invalid", ["false", 0, 1, None])
def test_invalid_availability_rejected(test_db, invalid):
    with pytest.raises(ValueError, match="Invalid availability"):
        set_dish_availability(test_db, 1, 9, invalid)

def get_price(db_path, dish_id):
    connection = sqlite3.connect(db_path)

    try:
        row = connection.execute(
            "SELECT price_kopeck FROM dishes WHERE id = ?",
            (dish_id,),
        ).fetchone()

        return row[0]
    finally:
        connection.close()


def test_update_dish_price(test_db):
    set_dish_price(test_db, 1, 9, 75000)

    assert get_price(test_db, 9) == 75000


def test_unknown_dish_price_rejected(test_db):
    with pytest.raises(ValueError, match="Dish not found"):
        set_dish_price(test_db, 1, 99999, 75000)


def test_other_restaurant_price_rejected(test_db):
    original = get_price(test_db, 9)

    with pytest.raises(ValueError, match="Dish not found"):
        set_dish_price(test_db, 999, 9, 75000)

    assert get_price(test_db, 9) == original


@pytest.mark.parametrize("invalid", [-100, 0, "75000", 75.5, True, None])
def test_invalid_price_rejected(test_db, invalid):
    with pytest.raises(ValueError, match="Invalid price"):
        set_dish_price(test_db, 1, 9, invalid)

def get_restaurant_rules(db_path, restaurant_id=1):
    connection = sqlite3.connect(db_path)

    try:
        row = connection.execute(
            """
            SELECT preference_weight, pairing_weight,
                   category_weight, enabled
            FROM restaurant_rules
            WHERE restaurant_id = ?
            """,
            (restaurant_id,),
        ).fetchone()

        return tuple(row) if row else None
    finally:
        connection.close()


def test_update_restaurant_rules(test_db):
    update_restaurant_rules(test_db, 1, 4, 5, 2, False)

    assert get_restaurant_rules(test_db) == (4, 5, 2, 0)


def test_restaurant_rules_allow_zero_weights(test_db):
    update_restaurant_rules(test_db, 1, 0, 0, 0, True)

    assert get_restaurant_rules(test_db) == (0, 0, 0, 1)


@pytest.mark.parametrize("invalid", [-1, 6, 2.5, "3", True, None])
def test_invalid_restaurant_weight_rejected(test_db, invalid):
    before = get_restaurant_rules(test_db)

    with pytest.raises(ValueError, match="Weight must be"):
        update_restaurant_rules(test_db, 1, 2, invalid, 1, True)

    assert get_restaurant_rules(test_db) == before


def test_invalid_restaurant_enabled_rejected(test_db):
    with pytest.raises(ValueError, match="Invalid enabled"):
        update_restaurant_rules(test_db, 1, 2, 3, 1, 1)


def test_unknown_restaurant_rules_rejected(test_db):
    with pytest.raises(ValueError, match="Restaurant rules not found"):
        update_restaurant_rules(test_db, 999, 2, 3, 1, True)
