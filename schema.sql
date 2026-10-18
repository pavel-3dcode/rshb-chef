CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    menu_updated TEXT
);

CREATE TABLE dishes (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price_kopeck INTEGER NOT NULL CHECK (typeof(price_kopeck) = 'integer' AND price_kopeck >= 0),
    available INTEGER NOT NULL DEFAULT 1 CHECK (available IN (0, 1)),
    is_alcohol INTEGER NOT NULL DEFAULT 0 CHECK (is_alcohol IN (0, 1)),
    ingredients_verified INTEGER NOT NULL DEFAULT 0 CHECK (ingredients_verified IN (0, 1)),
    allergens_verified INTEGER NOT NULL DEFAULT 0 CHECK (allergens_verified IN (0, 1)),

    UNIQUE (restaurant_id, id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE dish_ingredients (
    dish_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    PRIMARY KEY (dish_id, ingredient_id),
    FOREIGN KEY (dish_id) REFERENCES dishes(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE allergens (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE dish_allergens (
    dish_id INTEGER NOT NULL,
    allergen_id INTEGER NOT NULL,
    PRIMARY KEY (dish_id, allergen_id),
    FOREIGN KEY (dish_id) REFERENCES dishes(id),
    FOREIGN KEY (allergen_id) REFERENCES allergens(id)
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE dish_tags (
    dish_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,

    PRIMARY KEY (dish_id, tag_id),

    FOREIGN KEY (dish_id) REFERENCES dishes(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

CREATE TABLE pairings (
    restaurant_id INTEGER NOT NULL,
    main_dish_id INTEGER NOT NULL,
    addon_dish_id INTEGER NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),

    PRIMARY KEY (main_dish_id, addon_dish_id),

    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),

    FOREIGN KEY (restaurant_id, main_dish_id) REFERENCES dishes(restaurant_id, id),

    FOREIGN KEY (restaurant_id, addon_dish_id) REFERENCES dishes(restaurant_id, id),

    CHECK (main_dish_id != addon_dish_id)
);

CREATE TABLE restaurant_rules (
    restaurant_id INTEGER PRIMARY KEY,
    preference_weight INTEGER NOT NULL DEFAULT 1
        CHECK (preference_weight BETWEEN 0 AND 5),
    pairing_weight INTEGER NOT NULL DEFAULT 1
        CHECK (pairing_weight BETWEEN 0 AND 5),
    category_weight INTEGER NOT NULL DEFAULT 1
        CHECK (category_weight BETWEEN 0 AND 5),
    enabled INTEGER NOT NULL DEFAULT 1
        CHECK (enabled IN (0, 1)),

    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);
