import sqlite3
from pathlib import Path

def get_connection(db_path):
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    project_dir = Path(__file__).resolve().parent.parent
    db_path = project_dir / "instance" / "rshb_chef.db"
    schema_path = project_dir / "schema.sql"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = get_connection(db_path)

    try:
        with open(schema_path, encoding="utf-8") as file:
            connection.executescript(file.read())

    finally:
        connection.close()
