from pathlib import Path
from collections import defaultdict
from app.db import get_connection
from app.recommendations import Dish, MenuSnapshot

def load_menu(restaurant_id: int, db_path=None) -> MenuSnapshot:
    if db_path is None:
        project_dir = Path(__file__).resolve().parent.parent
        db_path = project_dir / "instance" / "rshb_chef.db"

    connection = get_connection(db_path)

    try:
        restaurant = connection.execute("SELECT id, menu_updated from restaurants where id = ?", (restaurant_id,)).fetchone()

        if restaurant is None:
            raise ValueError("Unknown restaurant id")

        rules = connection.execute("SELECT * FROM restaurant_rules WHERE restaurant_id = ?", (restaurant_id,)).fetchone()

        if rules is None:
            raise ValueError("Restaurant rules not found")

        dish_rows = connection.execute("SELECT * FROM dishes WHERE restaurant_id = ?", (restaurant_id,)).fetchall()

        ingredients_by_dish = defaultdict(set)
        for item in connection.execute(
            """
            SELECT di.dish_id, i.name
            FROM dish_ingredients di
            JOIN ingredients i ON i.id = di.ingredient_id
            JOIN dishes d ON d.id = di.dish_id
            WHERE d.restaurant_id = ?
            """,
            (restaurant_id,),
        ):
            ingredients_by_dish[item["dish_id"]].add(item["name"])

        allergens_by_dish = defaultdict(set)
        for item in connection.execute(
            """
            SELECT da.dish_id, a.name
            FROM dish_allergens da
            JOIN allergens a ON a.id = da.allergen_id
            JOIN dishes d ON d.id = da.dish_id
            WHERE d.restaurant_id = ?
            """,
            (restaurant_id,),
        ):
            allergens_by_dish[item["dish_id"]].add(item["name"])

        tags_by_dish = defaultdict(set)
        for item in connection.execute(
            """
            SELECT dt.dish_id, t.name
            FROM dish_tags dt
            JOIN tags t ON t.id = dt.tag_id
            JOIN dishes d ON d.id = dt.dish_id
            WHERE d.restaurant_id = ?
            """,
            (restaurant_id,),
        ):
            tags_by_dish[item["dish_id"]].add(item["name"])

        dishes = []

        for row in dish_rows:
            dish_id = row["id"]

            dishes.append(
                Dish(
                    id = dish_id,
                    restaurant_id = row["restaurant_id"],
                    name = row["name"],
                    category = row["category"],
                    price_kopeck = row["price_kopeck"],
                    available = bool(row["available"]),
                    is_alcohol = bool(row["is_alcohol"]),
                    ingredients_verified = bool(row["ingredients_verified"]),
                    allergens_verified = bool(row["allergens_verified"]),
                    ingredients = ingredients_by_dish[dish_id],
                    allergens = allergens_by_dish[dish_id],
                    tags = tags_by_dish[dish_id],
                )
            )

        pairing_rows = connection.execute("SELECT main_dish_id, addon_dish_id, score FROM pairings WHERE restaurant_id = ?", (restaurant_id,)).fetchall()

        pairings = {
            (row["main_dish_id"], row["addon_dish_id"]): row["score"]
            for row in pairing_rows
        }

        return MenuSnapshot(
            restaurant_id = restaurant_id,
            version = restaurant["menu_updated"] or "unknown",
            dishes = dishes,
            pairings = pairings,
            preference_weight = rules["preference_weight"],
            pairing_weight = rules["pairing_weight"],
            category_weight = rules["category_weight"],
            enabled = bool(rules["enabled"])
        )

    finally:

        connection.close()
