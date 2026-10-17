
import sqlite3
from pathlib import Path

import pytest
import runpy

from app.db import get_connection


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"

    project_dir = Path(__file__).resolve().parent.parent
    schema_path = project_dir / "schema.sql"

    connection = get_connection(db_path)

    try:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )

        connection.execute(
            "INSERT INTO restaurants (id, name) VALUES (?, ?)",
            (1, "Test Restaurant")
        )

        yield connection

    finally:
        connection.close()


def test_negative_price_rejected(tmp_path):
    db_path = tmp_path / "test.db"

    project_dir = Path(__file__).resolve().parent.parent
    schema_path = project_dir / "schema.sql"

    connection = get_connection(db_path)

    try:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )

        connection.execute(
            "INSERT INTO restaurants (id, name) VALUES (?, ?)",
            (1, "Test Restaurant")
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO dishes (
                    restaurant_id, name, category, price_kopeck
                )
                VALUES (?, ?, ?, ?)
                """,
                (1, "Invalid Dish", "main", -100)
            )

        count = connection.execute(
            "SELECT COUNT(*) FROM dishes"
        ).fetchone()[0]

        assert count == 0

    finally:
        connection.close()


def test_invalid_availability_rejected(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            """
            INSERT INTO dishes (
                restaurant_id, name, category,
                price_kopeck, available
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, "Invalid Availability", "main", 50000, 2)
        )

    count = db.execute(
        "SELECT COUNT(*) FROM dishes"
    ).fetchone()[0]

    assert count == 0


def test_unknown_restaurant_rejected(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            """
            INSERT INTO dishes (
                restaurant_id, name, category, price_kopeck
            )
            VALUES (?, ?, ?, ?)
            """,
            (999, "Invalid Restaurant", "main", 50000)
        )

    count = db.execute(
        "SELECT COUNT(*) FROM dishes"
    ).fetchone()[0]

    assert count == 0


def test_cross_restaurant_pairing_rejected(db):
    db.execute(
        "INSERT INTO restaurants (id, name) VALUES (?, ?)",
        (2, "Second Restaurant")
    )

    db.executemany(
        """
        INSERT INTO dishes (
            id, restaurant_id, name, category, price_kopeck
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (101, 1, "Main Dish", "main", 50000),
            (102, 2, "Side Dish", "side", 20000)
        ]
    )

    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            """
            INSERT INTO pairings (
                restaurant_id, main_dish_id,
                addon_dish_id, score
            )
            VALUES (?, ?, ?, ?)
            """,
            (1, 101, 102, 5)
        )

    count = db.execute(
        "SELECT COUNT(*) FROM pairings"
    ).fetchone()[0]

    assert count == 0


def test_seed_on_clean_database(tmp_path, monkeypatch):
    project_dir = Path(__file__).resolve().parent.parent
    schema_path = project_dir / "schema.sql"
    seed_path = project_dir / "seed_demo.py"

    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()

    db_path = instance_dir / "rshb_chef.db"

    connection = get_connection(db_path)

    try:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )
    finally:
        connection.close()

    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(seed_path))
    runpy.run_path(str(seed_path))

    connection = get_connection(db_path)

    try:
        dishes_count = connection.execute(
            "SELECT COUNT(*) FROM dishes"
        ).fetchone()[0]

        pairings_count = connection.execute(
            "SELECT COUNT(*) FROM pairings"
        ).fetchone()[0]

        rules_count = connection.execute(
            "SELECT COUNT(*) FROM restaurant_rules"
        ).fetchone()[0]

        assert dishes_count == 27
        assert pairings_count == 12
        assert rules_count == 1

        assert connection.execute(
            "SELECT COUNT(*) FROM dish_ingredients"
        ).fetchone()[0] == 127

        assert connection.execute(
            "SELECT COUNT(*) FROM dish_allergens"
        ).fetchone()[0] == 26

        assert connection.execute(
            "SELECT COUNT(*) FROM dish_tags"
        ).fetchone()[0] == 69

    finally:
        connection.close()

@pytest.mark.parametrize(
    "column",
    [
        "preference_weight",
        "pairing_weight",
        "category_weight",
    ]
)
@pytest.mark.parametrize(
    "weight, should_pass",
    [
        (0, True),
        (3, True),
        (5, True),
        (-1, False),
        (6, False),
    ]
)
def test_weight_range(db, column, weight, should_pass):
    sql = f"""
        INSERT INTO restaurant_rules (
            restaurant_id, {column}
        )
        VALUES (?, ?)
    """

    if should_pass:
        db.execute(sql, (1, weight))
    else:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(sql, (1, weight))
