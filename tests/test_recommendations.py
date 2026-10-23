import pytest
from app.recommendations import Dish, GuestContext, MenuSnapshot, filter_candidates, calculate_remaining_budget

@pytest.mark.parametrize("salad_price, expected_count", [
    (28000, 1),
    (35000, 1),
    (40000, 0)
])

def test_budget_filter(salad_price, expected_count):
    pasta = Dish(
    id = 1,
    restaurant_id = 1,
    name = "Паста",
    category = "main",
    price_kopeck = 65000,
    available  = True,
    is_alcohol = False,
    ingredients_verified = True,
    allergens_verified = True,
    ingredients = {"макароны", "сыр"},
    allergens = {"молоко"},
    tags = {"сытное"}
    )

    salad = Dish(
        id = 2,
        restaurant_id = 1,
        name = "Овощной салат",
        category = "salad",
        price_kopeck = salad_price,
        available  = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True,
        ingredients = {"огурец", "помидоры"},
        allergens = set(),
        tags = {"овощное"}
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [pasta, salad],
        pairings = {(1, 2): 3},
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "after_main",
        cart_dish_ids = [1],
        budget_kopeck = 100000
    )

    result = filter_candidates(menu, guest)

    assert len(result) == expected_count

def test_unknown_cart_dish_rejected():
    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = []
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "after_main",
        budget_kopeck = 100000,
        cart_dish_ids = [999]
    )

    with pytest.raises(ValueError):
        calculate_remaining_budget(menu, guest)

def test_unknown_cart_dish_without_budget_rejected():
    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = []
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "after_main",
        budget_kopeck = None,
        cart_dish_ids = [999]
    )

    with pytest.raises(ValueError):
        calculate_remaining_budget(menu, guest)


@pytest.mark.parametrize("is_alcohol, age_confirmed, expected_count", [
    (False, False, 1),
    (False, True, 1),
    (True, False, 0),
    (True, True, 1)
],
)

def test_alcohol_filter(is_alcohol, age_confirmed, expected_count):
    dish = Dish(
        id = 1,
        restaurant_id = 1,
        name = "TEst drink",
        category = "drink",
        price_kopeck = 20000,
        available = True,
        is_alcohol = is_alcohol,
        ingredients_verified = True,
        allergens_verified = True,
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [dish]
    )


    guest = GuestContext(
        restaurant_id = 1,
        stage = "after_main",
        age_confirmed = age_confirmed
    )

    result = filter_candidates(menu, guest)

    assert len(result) == expected_count


@pytest.mark.parametrize("allergens_verified, dish_allergens, expected_count", [
    (True, {"молоко"}, 0),
    (True, set(), 1),
    (False, set(), 0)
],)

def test_allergy_filter(allergens_verified, dish_allergens, expected_count):
    dish = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Test dish",
        category = "main",
        price_kopeck = 30000,
        available = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = allergens_verified,
        allergens = dish_allergens
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [dish]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "before_order",
        allergies = {"молоко"})

    result = filter_candidates(menu, guest)

    assert len(result) == expected_count

def test_no_allergies_selected():
    dish = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Test dish",
        category = "main",
        price_kopeck = 30000,
        available = True,
        is_alcohol = False,
        ingredients_verified = False,
        allergens_verified = False,
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [dish]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "before_order",
        allergies = set()
    )

    result = filter_candidates(menu, guest)

    assert len(result) == 1
@pytest.mark.parametrize("restriction, tags, ingredients_verified, expected_count", [
    ("vegan", {"vegan", "vegetarian"}, True, 1),
    ("vegetarian",{"vegetarian"}, True, 1),
    ("vegan", {"vegetarian"}, True, 0),
    ("vegan", {"vegan"}, False, 0),
    ("vegetarian", set(), True, 0)
])

def test_dietary_restriction_filter(restriction, tags, ingredients_verified, expected_count):
    dish = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Test dish",
        category = "main",
        price_kopeck = 30000,
        available = True,
        is_alcohol = False,
        ingredients_verified = ingredients_verified,
        allergens_verified = True,
        tags = tags
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [dish]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "before_order",
        restrictions = {restriction}
    )

    result = filter_candidates(menu, guest)

    assert len(result) == expected_count


def test_multiple_dietary_restrictions():
    dish = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Овощной салат",
        category = "salad",
        price_kopeck = 28000,
        available = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True,
        tags = {"vegetarian"}
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [dish]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "before_order",
        restrictions = {"vegan", "vegetarian"}
    )

    result = filter_candidates(menu, guest)

    assert result == []


def test_no_dietary_restrictions_selected():
    dish = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Тестовое блюдо",
        category = "main",
        price_kopeck = 28000,
        available = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True,
        tags = set()
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [dish]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "before_order",
        restrictions = set()
    )

    result = filter_candidates(menu, guest)

    assert len(result) == 1

@pytest.mark.parametrize("stage, category, expected_count", [
    ("before_order", "main", 1),
    ("before_order", "dessert", 0),
    ("after_main", "side", 1),
    ("after_main", "main", 0),
    ("before_dessert", "dessert", 1),
    ("before_dessert", "salad", 0),
])

def test_stage_category_filter(stage, category, expected_count):
    dish = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Test dish",
        category = category,
        price_kopeck = 30000,
        available = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True,
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [dish]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = stage
    )

    result = filter_candidates(menu, guest)

    assert len(result) == expected_count


@pytest.mark.parametrize("stage", [
    "before_desert",
    "after_lunch",
    ""
])

def test_unknown_stage_rejected(stage):
    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = []
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = stage
    )

    with pytest.raises(ValueError, match = "Unknown stage"):
        filter_candidates(menu, guest)


def test_recommendations_disabled():
    dish = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Test dish",
        category = "main",
        price_kopeck = 30000,
        available = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True,
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [dish]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "before_order",
        recommendations_enabled = False
    )

    result = filter_candidates(menu, guest)

    assert result == []


def test_negative_budget_rejected():
    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = []
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "before_order",
        budget_kopeck = -1
    )

    with pytest.raises(ValueError, match = "Negative budget"):
        filter_candidates(menu, guest)


def test_negative_remaining_budget():
    pasta = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Паста",
        category = "main",
        price_kopeck = 65000,
        available  = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True,
        ingredients = {"макароны", "сыр"},
        allergens = {"молоко"},
        tags = {"сытное"}
    )

    salad = Dish(
        id = 2,
        restaurant_id = 1,
        name = "Овощной салат",
        category = "salad",
        price_kopeck = 28000,
        available  = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True,
        ingredients = {"огурец", "помидоры"},
        allergens = set(),
        tags = {"овощное"}
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [pasta, salad]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "after_main",
        cart_dish_ids = [1],
        budget_kopeck = 50000
    )

    remaining = calculate_remaining_budget(menu, guest)

    result = filter_candidates(menu, guest)

    assert remaining == -15000
    assert result == []


@pytest.mark.parametrize(
    "budget, price, expected_count",
    [
        (65000, 28000, 0),
        (65000, 0, 1),
        (50000, 0, 0),
    ],
)

def test_exhausted_budget(budget, price, expected_count):
    pasta = Dish(
        id = 1,
        restaurant_id = 1,
        name = "Паста",
        category = "main",
        price_kopeck = 65000,
        available  = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True,
        ingredients = {"макароны", "сыр"},
        allergens = {"молоко"},
        tags = {"сытное"}
    )

    addon = Dish(
        id = 2,
        restaurant_id = 1,
        name = "Дополнение",
        category = "side",
        price_kopeck = price,
        available  = True,
        is_alcohol = False,
        ingredients_verified = True,
        allergens_verified = True
    )

    menu = MenuSnapshot(
        restaurant_id = 1,
        version = "1.0",
        dishes = [pasta, addon]
    )

    guest = GuestContext(
        restaurant_id = 1,
        stage = "after_main",
        cart_dish_ids = [1],
        budget_kopeck = budget
    )

    result = filter_candidates(menu, guest)

    assert len(result) == expected_count
