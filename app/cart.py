
def validate_menu_dish(menu, guest, dish_id):
    dish = next(
        (
            item for item in menu.dishes
            if item.id == dish_id
            and item.restaurant_id == guest.restaurant_id
        ),
        None
    )

    if dish is None:
        raise ValueError("Dish not found")

    if not dish.available:
        raise ValueError("Dish unavailable")

    if dish.id in guest.cart_dish_ids:
        raise ValueError("Dish already in cart")

    if dish.is_alcohol and not guest.age_confirmed:
        raise ValueError("Age confirmation required")

    if guest.allergies:
        if not dish.allergens_verified:
            raise ValueError("Allergen information not verified")

        if guest.allergies & dish.allergens:
            raise ValueError("Dish conflicts with allergies")

    if guest.restrictions:
        if not dish.ingredients_verified:
            raise ValueError("Ingredients not verified")

        if not guest.restrictions.issubset(dish.tags):
            raise ValueError("Dish conflicts with dietary restrictions")

    if guest.budget_kopeck is not None:
        cart_total = sum(
            item.price_kopeck
            for item in menu.dishes
            if item.id in guest.cart_dish_ids
            and item.restaurant_id == guest.restaurant_id
        )

        remaining = guest.budget_kopeck - cart_total

        if dish.price_kopeck > remaining:
            raise ValueError("Dish exceeds remaining budget")

    return dish
