from dataclasses import dataclass, field

stage_categories = {
    "before_order": {"main", "soup", "salad"},
    "after_main": {"side", "salad", "drink"},
    "before_dessert": {"dessert", "drink"}
}

@dataclass
class GuestContext:
    restaurant_id: int
    stage: str
    budget_kopeck: int | None = None
    cart_dish_ids: list[int] = field (default_factory=list)
    allergies: set[str] = field(default_factory=set)
    restrictions: set[str] = field(default_factory=set)
    preferences: set[str] = field(default_factory=set)
    age_confirmed: bool = False
    recommendations_enabled: bool = True


@dataclass
class Dish:
    id: int
    restaurant_id: int
    name: str
    category: str
    price_kopeck: int
    available: bool
    is_alcohol: bool
    ingredients_verified: bool
    allergens_verified: bool
    ingredients: set[str] = field(default_factory=set)
    allergens: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MenuSnapshot:
    restaurant_id: int
    version: str
    dishes: list[Dish]
    pairings: dict[tuple[int, int], int] = field(default_factory=dict)
    preference_weight: float = 2
    pairing_weight: float = 3
    category_weight: float  = 1
    enabled: bool = True

@dataclass
class Recommendation:
    dish_id: int
    name: str
    price_kopeck: int
    score: float
    reasons: list[str] = field(default_factory=list)

def filter_candidates(menu: MenuSnapshot, guest: GuestContext) -> list[Dish]:
    candidates = []

    if guest.stage not in stage_categories:
        raise ValueError("Unknown stage")

    if guest.budget_kopeck is not None and guest.budget_kopeck < 0:
        raise ValueError("Negative budget")
    if not guest.recommendations_enabled:
        return candidates

    remaining_budget = calculate_remaining_budget(menu, guest)

    for dish in menu.dishes:
        if dish.restaurant_id != guest.restaurant_id:
            continue
        if dish.category not in stage_categories[guest.stage]:
            continue
        if not dish.available:
            continue
        if dish.is_alcohol and not guest.age_confirmed:
            continue
        if guest.allergies:
            if not dish.allergens_verified:
                continue
            if guest.allergies & dish.allergens:
                continue
        if guest.restrictions:
            if not dish.ingredients_verified:
                continue
            if not guest.restrictions.issubset(dish.tags):
                continue
        if dish.id in guest.cart_dish_ids:
            continue
        if remaining_budget is not None and dish.price_kopeck > remaining_budget:
            continue

        candidates.append(dish)
    return candidates

def calculate_remaining_budget(menu: MenuSnapshot, guest: GuestContext) -> int | None:

    cart_total = 0

    for dish_id in guest.cart_dish_ids:
        for dish in menu.dishes:
            if dish.id ==dish_id and dish.restaurant_id == guest.restaurant_id:
                cart_total += dish.price_kopeck
                break
        else:
            raise ValueError("Cart include unknown dish")

    if guest.budget_kopeck is None:
            return None

    return guest.budget_kopeck - cart_total
