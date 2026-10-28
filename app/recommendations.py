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


def score_candidate(
    dish: Dish,
    menu: MenuSnapshot,
    guest: GuestContext,
) -> float:
    pairing_match = 0

    if guest.stage == "after_main":
        for cart_id in guest.cart_dish_ids:
            if (cart_id, dish.id) in menu.pairings:
                pairing_match = 1
                break

    preference_match = int(bool(guest.preferences & dish.tags))

    category_match = int(dish.category in stage_categories[guest.stage])

    score = (
        menu.pairing_weight * pairing_match +
        menu.preference_weight * preference_match +
        menu.category_weight * category_match
    )

    return score

def build_reasons(
    dish: Dish,
    menu: MenuSnapshot,
    guest: GuestContext,
) -> list[str]:
    reasons = []

    if guest.stage == "after_main":
        if any(
            (cart_id, dish.id) in menu.pairings
            for cart_id in guest.cart_dish_ids
        ):
            reasons.append("Сочетается с выбранным блюдом")

    matching_preferences = sorted(guest.preferences & dish.tags)

    if matching_preferences:
        reasons.append(
            "Соответствует предпочтениям: "
            + ", ".join(matching_preferences)
        )

    reasons.append("Подходит для текущего этапа заказа")

    remaining_budget = calculate_remaining_budget(menu, guest)

    if remaining_budget is not None:
        reasons.append("Укладывается в оставшийся бюджет")

    return reasons


def recommend(
    menu: MenuSnapshot,
    guest: GuestContext,
) -> list[Recommendation]:
    if menu.restaurant_id != guest.restaurant_id:
        raise ValueError("Not the right restaurant")

    if not menu.enabled:
        return []

    candidates = filter_candidates(menu, guest)
    recommendations = []

    for dish in candidates:
        recommendations.append(
            Recommendation(
                dish_id = dish.id,
                name = dish.name,
                price_kopeck = dish.price_kopeck,
                score = score_candidate(dish, menu, guest),
                reasons = build_reasons(dish, menu, guest),
            )
        )

        if guest.stage == "before_dessert":
            dessert_ids = {
                dish.id
                for dish in candidates
                if dish.category == "dessert"
            }

            recommendations.sort(
                key=lambda item: (
                    item.dish_id not in dessert_ids,
                    -item.score,
                    item.price_kopeck,
                    item.dish_id,
                )
            )
        else:
            recommendations.sort(
                key=lambda item: (
                    -item.score,
                    item.price_kopeck,
                    item.dish_id,
                )
            )

    return recommendations[:3]
