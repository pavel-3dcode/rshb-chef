from app.recommendations import GuestContext

ALLOWED_ALLERGIES = {
    "Milk", "Eggs", "Cereals containing gluten",
    "Fish", "Sesame", "Mustard", "Soybeans",
    "Tree nuts", "Peanuts", "Celery",
    "Sulphur dioxide and sulphites",
    "Crustaceans", "Molluscs", "Lupin"
}

ALLOWED_RESTRICTIONS = {"vegan", "vegetarian"}

ALLOWED_PREFERENCES = {
    "creamy", "fresh", "hearty", "light",
    "refreshing", "savory", "sweet"
}

def validate_guest_json(data):
    if not isinstance(data, dict):
        raise ValueError("JSON must be an object")

    allowed_stages = ("before_order", "after_main", "before_dessert")
    stage = data.get("stage")

    if type(stage) is not str or stage not in allowed_stages:
        raise ValueError("Invalid stage")

    budget = data.get("budget_kopeck")

    if budget is not None:
        if type(budget) is not int or budget < 0:
            raise ValueError("Invalid budget_kopeck")

    cart = data.get("cart_dish_ids", [])

    if not isinstance(cart, list):
        raise ValueError("Invalid cart_dish_ids")

    if any(type(dish_id) is not int or dish_id <= 0 for dish_id in cart):
        raise ValueError("Invalid cart_dish_ids")

    if len(cart) != len(set(cart)):
        raise ValueError("Duplicate cart_dish_ids")

    def validate_strings(field):
        values = data.get(field, [])

        if not isinstance(values, list):
            raise ValueError(f"Invalid {field}")

        if any(type(value) is not str or not value.strip() for value in values):
            raise ValueError(f"Invalid {field}")

        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate {field}")

        return values

    allergies = validate_strings("allergies")
    restrictions = validate_strings("restrictions")
    preferences = validate_strings("preferences")

    age_confirmed = data.get("age_confirmed", False)
    recommendations_enabled = data.get("recommendations_enabled", True)

    if type(age_confirmed) is not bool:
        raise ValueError("Invalid age_confirmed")

    if type(recommendations_enabled) is not bool:
        raise ValueError("Invalid recommendations_enabled")

    return {
        "stage": stage,
        "budget_kopeck": budget,
        "cart_dish_ids": cart,
        "allergies": allergies,
        "restrictions": restrictions,
        "preferences": preferences,
        "age_confirmed": age_confirmed,
        "recommendations_enabled": recommendations_enabled
    }

def build_guest_context(data, menu, restaurant_id=1):
    values = validate_guest_json(data)

    for field, allowed in (
        ("allergies", ALLOWED_ALLERGIES),
        ("restrictions", ALLOWED_RESTRICTIONS),
        ("preferences", ALLOWED_PREFERENCES),
    ):
        if not set(values[field]).issubset(allowed):
            raise ValueError(f"Unknown {field}")

    if type(restaurant_id) is not int or restaurant_id <= 0:
        raise ValueError("Invalid restaurant_id")

    menu_restaurant_id = getattr(menu, "restaurant_id", None)

    if menu_restaurant_id is not None and menu_restaurant_id != restaurant_id:
        raise ValueError("Restaurant mismatch")

    valid_dish_ids = {
        dish.id
        for dish in menu.dishes
        if dish.restaurant_id == restaurant_id
    }

    for dish_id in values["cart_dish_ids"]:
        if dish_id not in valid_dish_ids:
            raise ValueError("Unknown cart dish")

    return GuestContext(
        restaurant_id = restaurant_id,
        stage = values["stage"],
        budget_kopeck = values["budget_kopeck"],
        cart_dish_ids = values["cart_dish_ids"],
        allergies = set(values["allergies"]),
        restrictions = set(values["restrictions"]),
        preferences = set(values["preferences"]),
        age_confirmed = values["age_confirmed"],
        recommendations_enabled = values["recommendations_enabled"],
    )
