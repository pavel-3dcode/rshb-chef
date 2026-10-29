from app.db import get_connection


def set_dish_availability(db_path, restaurant_id, dish_id, available):
    if type(restaurant_id) is not int or restaurant_id <= 0:
        raise ValueError("Invalid restaurant_id")

    if type(dish_id) is not int or dish_id <= 0:
        raise ValueError("Invalid dish_id")

    if type(available) is not bool:
        raise ValueError("Invalid availability")

    connection = get_connection(db_path)

    try:
        with connection:
            cursor = connection.execute(
                """
                UPDATE dishes
                SET available = ?
                WHERE id = ? AND restaurant_id = ?
                """,
                (int(available), dish_id, restaurant_id),
            )

            if cursor.rowcount != 1:
                raise ValueError("Dish not found in restaurant")
    finally:
        connection.close()

def set_dish_price(db_path, restaurant_id, dish_id, price_kopeck):
    if type(restaurant_id) is not int or restaurant_id <= 0:
        raise ValueError("Invalid restaurant_id")

    if type(dish_id) is not int or dish_id <= 0:
        raise ValueError("Invalid dish_id")

    if type(price_kopeck) is not int or price_kopeck <= 0:
        raise ValueError("Invalid price")

    connection = get_connection(db_path)

    try:
        with connection:
            cursor = connection.execute(
                """
                UPDATE dishes
                SET price_kopeck = ?
                WHERE id = ? AND restaurant_id = ?
                """,
                (price_kopeck, dish_id, restaurant_id),
            )

            if cursor.rowcount != 1:
                raise ValueError("Dish not found in restaurant")
    finally:
        connection.close()

def update_restaurant_rules(
    db_path,
    restaurant_id,
    preference_weight,
    pairing_weight,
    category_weight,
    enabled,
):
    if type(restaurant_id) is not int or restaurant_id <= 0:
        raise ValueError("Invalid restaurant_id")

    for weight in (preference_weight, pairing_weight, category_weight):
        if type(weight) is not int or not 0 <= weight <= 5:
            raise ValueError("Weight must be an integer from 0 to 5")

    if type(enabled) is not bool:
        raise ValueError("Invalid enabled value")

    connection = get_connection(db_path)

    try:
        with connection:
            cursor = connection.execute(
                """
                UPDATE restaurant_rules
                SET preference_weight = ?,
                    pairing_weight = ?,
                    category_weight = ?,
                    enabled = ?
                WHERE restaurant_id = ?
                """,
                (
                    preference_weight,
                    pairing_weight,
                    category_weight,
                    int(enabled),
                    restaurant_id,
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError("Restaurant rules not found")
    finally:
        connection.close()
