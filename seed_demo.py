from pathlib import Path

from app.db import get_connection


def seed_demo(db_path=None):
    if db_path is None:
        project_dir = Path(__file__).resolve().parent
        db_path = project_dir / "instance" / "rshb_chef.db"

    connection = get_connection(db_path)

    try:

        connection.execute("INSERT OR IGNORE INTO restaurants (id, name) VALUES (?, ?)", (1, "Test Restaurant"))


        dishes = [
            (1, 1, "Chicken Soup", "soup", 35000, 1, 0),
            (2, 1, "Caesar Salad", "salad", 45000, 1, 0),
            (3, 1, "Pork Neck Steak", "main", 130000, 1, 0),
            (4, 1, "Mashed Potatoes", "side", 25000, 1, 0),
            (5, 1, "Chicken Shashlik", "main", 65000, 1, 0),
            (6, 1, "Baked Salmon", "main", 95000, 1, 0),
            (7, 1, "Spinach Pasta in Cream Sauce", "main", 52000, 1, 0),
            (8, 1, "Pasta Carbonara", "main", 62000, 1, 0),
            (9, 1, "Beef Burger", "main", 69000, 1, 0),
            (10, 1, "Cream Soup", "soup", 30000, 1, 0),
            (11, 1, "Fried Rice with Red Onion", "side", 18000, 1, 0),
            (12, 1, "Roasted Vegetables", "side", 29000, 1, 0),
            (13, 1, "French Fries", "side", 23000, 0, 0),
            (14, 1, "Greek Salad", "salad", 39000, 1, 0),
            (15, 1, "Vegetable Salad", "salad", 28000, 1, 0),
            (16, 1, "Homemade Olivier Salad", "salad", 32000, 1, 0),
            (17, 1, "Apple Pie", "dessert", 39000, 1, 0),
            (18, 1, "Tiramisu", "dessert", 42000, 0, 0),
            (19, 1, "Chocolate-Covered Fruit", "dessert", 31000, 1, 0),
            (20, 1, "Ice Cream", "dessert", 25000, 1, 0),
            (21, 1, "Black Tea", "drink", 15000, 1, 0),
            (22, 1, "Fruit Tea", "drink", 18000, 1, 0),
            (23, 1, "Green Tea", "drink", 15000, 1, 0),
            (24, 1, "Lemonade", "drink", 22000, 1, 0),
            (25, 1, "Red Wine", "drink", 49000, 1, 1),
            (26, 1, "White Wine", "drink", 49000, 1, 1),
            (27, 1, "Craft Beer", "drink", 35000, 1, 1),
        ]

        connection.executemany(
            """
            INSERT INTO dishes (
                id, restaurant_id, name, category,
                price_kopeck, available, is_alcohol
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                category = excluded.category,
                price_kopeck = excluded.price_kopeck,
                is_alcohol = excluded.is_alcohol
            """,
            dishes
        )


        recipes = {
            1: ["Chicken", "Potato", "Carrot", "Onion", "Water", "Dill", "Salt"],
            2: ["Chicken", "Romaine Lettuce", "Bread Croutons",
                "Parmesan", "Anchovies", "Eggs", "Mustard", "Garlic", "Olive Oil"],
            3: ["Pork Neck", "Garlic", "Onion", "Sunflower Oil",
                "Salt", "Black Pepper"],
            4: ["Potato", "Milk", "Butter", "Salt"],
            5: ["Chicken", "Onion", "Lemon", "Sunflower Oil", "Paprika", "Salt"],
            6: ["Salmon", "Lemon", "Olive Oil", "Dill", "Salt"],
            7: ["Wheat Pasta", "Spinach", "Cream", "Parmesan",
                "Garlic", "Butter"],
            8: ["Wheat Pasta", "Bacon", "Eggs", "Parmesan",
                "Garlic", "Black Pepper"],
            9: ["Beef", "Sesame Bun", "Cheese", "Tomato",
                "Romaine Lettuce", "Cucumber", "Mustard"],
            10: ["Mushroom", "Cream", "Butter", "Onion",
                "Garlic", "Vegetable Broth"],
            11: ["Rice", "Red Onion", "Sunflower Oil", "Garlic", "Salt"],
            12: ["Zucchini", "Eggplant", "Bell Pepper",
                "Carrot", "Olive Oil"],
            13: ["Potato", "Sunflower Oil", "Salt"],
            14: ["Tomato", "Cucumber", "Red Onion", "Olives",
                "Feta", "Olive Oil", "Oregano"],
            15: ["Tomato", "Cucumber", "Romaine Lettuce",
                "Dill", "Sunflower Oil"],
            16: ["Potato", "Carrot", "Eggs", "Green Peas",
                "Pickled Cucumber", "Cooked Sausage", "Mayonnaise"],
            17: ["Apple", "Wheat Flour", "Eggs", "Butter",
                "Sugar", "Cinnamon"],
            18: ["Mascarpone", "Cream", "Savoiardi Biscuits",
                "Coffee", "Sugar", "Cocoa Powder"],
            19: ["Strawberry", "Banana", "Dark Chocolate"],
            20: ["Milk", "Cream", "Sugar", "Vanilla"],
            21: ["Black Tea", "Water"],
            22: ["Black Tea", "Mixed Berries", "Apple",
                "Lemon", "Sugar", "Water"],
            23: ["Green Tea", "Water"],
            24: ["Lemon", "Water", "Sugar", "Mint"],
            25: [],
            26: [],
            27: [],
        }

        recipe_allergens = {
            1: [],
            2: ["Milk", "Eggs", "Fish", "Mustard",
                "Cereals containing gluten"],
            3: [],
            4: ["Milk"],
            5: [],
            6: ["Fish"],
            7: ["Milk", "Cereals containing gluten"],
            8: ["Milk", "Eggs", "Cereals containing gluten"],
            9: ["Milk", "Sesame", "Mustard",
                "Cereals containing gluten"],
            10: ["Milk"],
            11: [],
            12: [],
            13: [],
            14: ["Milk"],
            15: [],
            16: ["Eggs"],
            17: ["Milk", "Eggs", "Cereals containing gluten"],
            18: ["Milk", "Eggs", "Cereals containing gluten"],
            19: [],
            20: ["Milk"],
            21: [],
            22: [],
            23: [],
            24: [],
            25: [],
            26: [],
            27: [],
        }


        unverified_dishes = {16, 19, 25, 26, 27}


        allergen_names = [
            "Milk",
            "Eggs",
            "Cereals containing gluten",
            "Fish",
            "Sesame",
            "Mustard",
            "Soybeans",
            "Tree nuts",
            "Peanuts",
            "Celery",
            "Sulphur dioxide and sulphites",
            "Crustaceans",
            "Molluscs",
            "Lupin",
        ]


        ingredient_names = sorted({
            ingredient
            for recipe in recipes.values()
            for ingredient in recipe
        })

        connection.executemany(
            "INSERT OR IGNORE INTO ingredients (name) VALUES (?)",
            [(name,) for name in ingredient_names]
        )

        connection.executemany(
            "INSERT OR IGNORE INTO allergens (name) VALUES (?)",
            [(name,) for name in allergen_names]
        )


        ingredient_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM ingredients")
        }

        allergen_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM allergens")
        }


        ingredient_links = [
            (dish_id, ingredient_ids[name])
            for dish_id, names in recipes.items()
            for name in names
        ]

        connection.executemany(
            """
            INSERT OR IGNORE INTO dish_ingredients (dish_id, ingredient_id)
            VALUES (?, ?)
            """,
            ingredient_links
        )

        allergen_links = [
            (dish_id, allergen_ids[name])
            for dish_id, names in recipe_allergens.items()
            for name in names
        ]

        connection.executemany(
            """
            INSERT OR IGNORE INTO dish_allergens (dish_id, allergen_id)
            VALUES (?, ?)
            """,
            allergen_links
        )


        verification_rows = [
            (
                0 if dish_id in unverified_dishes else 1,
                0 if dish_id in unverified_dishes else 1,
                dish_id
            )
            for dish_id in recipes
        ]

        connection.executemany(
            """
            UPDATE dishes
            SET ingredients_verified = ?,
                allergens_verified = ?
            WHERE id = ?
            """,
            verification_rows
        )


        dish_tags = {
            1: ["savory", "light"],
            2: ["savory", "fresh", "hearty"],
            3: ["savory", "hearty"],
            4: ["savory", "creamy", "vegetarian"],
            5: ["savory", "hearty"],
            6: ["savory", "light"],
            7: ["savory", "creamy", "vegetarian"],
            8: ["savory", "creamy", "hearty"],
            9: ["savory", "hearty"],
            10: ["savory", "creamy", "vegetarian"],
            11: ["savory", "light", "vegan", "vegetarian"],
            12: ["savory", "light", "vegan", "vegetarian"],
            13: ["savory", "vegan", "vegetarian"],
            14: ["savory", "fresh", "light", "vegetarian"],
            15: ["fresh", "light", "vegan", "vegetarian"],
            16: ["savory", "hearty"],
            17: ["sweet", "vegetarian"],
            18: ["sweet", "creamy"],
            19: ["sweet", "fresh"],
            20: ["sweet", "creamy", "vegetarian"],
            21: ["light", "vegan", "vegetarian"],
            22: ["fresh", "sweet", "vegan", "vegetarian"],
            23: ["light", "vegan", "vegetarian"],
            24: ["fresh", "refreshing", "vegan", "vegetarian"],
            25: [],
            26: [],
            27: [],
        }

        tag_names = sorted({
            tag
            for tags in dish_tags.values()
            for tag in tags
        })

        connection.executemany(
            "INSERT OR IGNORE INTO tags (name) VALUES (?)",
            [(name,) for name in tag_names]
        )

        tag_ids = {
            row["name"]: row["id"]
            for row in connection.execute(
                "SELECT id, name FROM tags"
            )
        }

        tag_links = [
            (dish_id, tag_ids[tag])
            for dish_id, tags in dish_tags.items()
            for tag in tags
        ]

        connection.executemany(
            """
            INSERT OR IGNORE INTO dish_tags (dish_id, tag_id)
            VALUES (?, ?)
            """,
            tag_links
        )

        pairings = [
            (1, 3, 4, 5),
            (1, 3, 12, 4),
            (1, 3, 15, 3),
            (1, 5, 11, 5),
            (1, 5, 14, 4),
            (1, 6, 12, 5),
            (1, 6, 11, 4),
            (1, 7, 15, 4),
            (1, 8, 14, 4),
            (1, 9, 13, 5),
            (1, 9, 15, 3),
            (1, 9, 24, 4),
        ]

        connection.executemany(
            """
            INSERT INTO pairings (
                restaurant_id, main_dish_id,
                addon_dish_id, score
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(main_dish_id, addon_dish_id)
            DO UPDATE SET score = excluded.score
            """,
            pairings
        )


        connection.execute(
            """
            INSERT OR IGNORE INTO restaurant_rules (
                restaurant_id,
                preference_weight,
                pairing_weight,
                category_weight,
                enabled
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, 2, 3, 1, 1)
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    seed_demo()
