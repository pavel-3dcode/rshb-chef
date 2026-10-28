from pathlib import Path

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

        dishes = []

        for row in dish_rows:
            dish_id = row["id"]

            ingredients = {
                item["name"]
                for item in connection.execute("SELECT i.name FROM  ingredients i JOIN dish_ingredients di ON di.ingredient_id = i.id WHERE di.dish_id = ?", (dish_id,))
            }

            allergens = {
                item["name"]
                for item in connection.execute("SELECT a.name FROM allergens a JOIN dish_allergens da ON da.allergen_id = a.id WHERE da.dish_id = ?", (dish_id,))
            }

            tags = {
                item["name"]
                for item in connection.execute("SELECT t.name FROM tags t JOIN dish_tags dt ON dt.tag_id = t.id WHERE dt.dish_id = ?", (dish_id,))
            }

            dishes.append(
                Dish(
                    id = dish_id,
                    restaurant_id = row["restaurant_id"],
                    name = row["name"],
                    category = row["category"],
                    price_kopeck = row["price_kopeck"],
                    available = row["available"],
                    is_alcohol = row["is_alcohol"],
                    ingredients_verified = bool(row["ingredients_verified"]),
                    allergens_verified = bool(row["allergens_verified"]),
                    ingredients = ingredients,
                    allergens = allergens,
                    tags = tags,
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
