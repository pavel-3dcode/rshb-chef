import sqlite3
from pathlib import Path

from app.db import get_connection


def migrate_schema(db_path):
    db_path = Path(db_path)
    if not db_path.is_file():
        raise FileNotFoundError(db_path)

    connection = get_connection(db_path)

    try:
        current_schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'dishes'"
        ).fetchone()

        if current_schema is None:
            raise RuntimeError("Table dishes not found")

        if "typeof(price_kopeck) = 'integer'" in current_schema["sql"]:
            raise RuntimeError("Database schema already updated")

        connection.execute("PRAGMA foreign_keys = OFF")

        connection.execute("BEGIN")

        connection.execute("""
            CREATE TABLE dishes_new (
                id INTEGER PRIMARY KEY,
                restaurant_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price_kopeck INTEGER NOT NULL
                    CHECK (typeof(price_kopeck) = 'integer' AND price_kopeck >= 0),
                available INTEGER NOT NULL DEFAULT 1
                    CHECK (available IN (0, 1)),
                is_alcohol INTEGER NOT NULL DEFAULT 0
                    CHECK (is_alcohol IN (0, 1)),
                ingredients_verified INTEGER NOT NULL DEFAULT 0
                    CHECK (ingredients_verified IN (0, 1)),
                allergens_verified INTEGER NOT NULL DEFAULT 0
                    CHECK (allergens_verified IN (0, 1)),
                UNIQUE (restaurant_id, id),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
        """)

        connection.execute("""
            INSERT INTO dishes_new
            SELECT * FROM dishes
        """)

        connection.execute("DROP TABLE dishes")
        connection.execute("ALTER TABLE dishes_new RENAME TO dishes")

        connection.execute("""
            CREATE TABLE restaurant_rules_new (
                restaurant_id INTEGER PRIMARY KEY,
                preference_weight INTEGER NOT NULL DEFAULT 1
                    CHECK (preference_weight BETWEEN 0 AND 5),
                pairing_weight INTEGER NOT NULL DEFAULT 1
                    CHECK (pairing_weight BETWEEN 0 AND 5),
                category_weight INTEGER NOT NULL DEFAULT 1
                    CHECK (category_weight BETWEEN 0 AND 5),
                enabled INTEGER NOT NULL DEFAULT 1
                    CHECK (enabled IN (0, 1)),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
        """)

        connection.execute("""
            INSERT INTO restaurant_rules_new
            SELECT * FROM restaurant_rules
        """)

        connection.execute("DROP TABLE restaurant_rules")
        connection.execute(
            "ALTER TABLE restaurant_rules_new RENAME TO restaurant_rules"
        )

        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Foreign key check failed")

        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity != "ok":
            raise RuntimeError(f"Integrity check failed: {integrity}")

        connection.commit()
        print("Migration completed successfully")

    except Exception:
        connection.rollback()
        raise

    finally:
        try:
            connection.execute("PRAGMA foreign_keys = ON")
        finally:
            connection.close()


if __name__ == "__main__":
    raise SystemExit("Specify the correct path to the database file")
