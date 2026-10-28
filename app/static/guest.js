
const form = document.getElementById("recommendation-form");
const results = document.getElementById("recommendation-results");
const submitButton = form.querySelector('button[type="submit"]');

const toggleButton = document.getElementById("toggle-recommendations");
const panel = document.getElementById("recommendations");
const toggleLabel = document.getElementById("toggle-label");

const cart = [];
const cartItems = document.getElementById("cart-items");
const cartCount = document.getElementById("cart-count");
const cartTotal = document.getElementById("cart-total");
const cartBudget = document.getElementById("cart-budget");

function getGuestData() {
    const budgetValue = document.getElementById("budget").value;
    const allergy = document.getElementById("allergy").value;
    const restriction = document.getElementById("restriction").value;
    const preference = document.getElementById("preference").value;

    return {
        stage: document.getElementById("stage").value,
        budget_kopeck: budgetValue === "" ? null : Number(budgetValue) * 100,
        cart_dish_ids: cart.map(dish => dish.dish_id),
        allergies: allergy ? [allergy] : [],
        restrictions: restriction ? [restriction] : [],
        preferences: preference ? [preference] : [],
        age_confirmed: false,
        recommendations_enabled: document.getElementById("recommendations-enabled").checked
    };
}

function renderCart() {
    cartItems.replaceChildren();

    if (cart.length === 0) {
        cartItems.textContent = "Вы пока ничего не выбрали.";
    }

    for (const dish of cart) {
        const row = document.createElement("div");
        row.className = "cart-item";

        const name = document.createElement("span");
        name.textContent = `${dish.name} — ${(dish.price_kopeck / 100).toFixed(2)} ₽`;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = "Убрать";

        remove.addEventListener("click", () => {
            const index = cart.findIndex(item => item.dish_id === dish.dish_id);
            if (index !== -1) cart.splice(index, 1);
            renderCart();
            form.requestSubmit();
        });

        row.append(name, remove);
        cartItems.appendChild(row);

    }

    const total = cart.reduce((sum, dish) => sum + dish.price_kopeck, 0);
    cartCount.textContent = String(cart.length);
    cartTotal.textContent = `${(total / 100).toFixed(2)} ₽`;

    const budget = getGuestData().budget_kopeck;
    cartBudget.textContent = budget === null
        ? "Бюджет не ограничен"
        : `Остаток бюджета: ${((budget - total) / 100).toFixed(2)} ₽`;

    updateMenuButtons();
}

toggleButton.addEventListener("click", () => {
    const isOpen = panel.classList.toggle("is-open");

    toggleButton.classList.toggle("is-open", isOpen);
    toggleButton.setAttribute("aria-expanded", String(isOpen));
    panel.setAttribute("aria-hidden", String(!isOpen));
    panel.inert = !isOpen;

    toggleLabel.textContent = isOpen
        ? "Скрыть настройки"
        : "Подобрать блюда";

    if (isOpen) {
        setTimeout(() => {
            panel.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }, 250);
    }
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const budgetValue = document.getElementById("budget").value;
    const allergy = document.getElementById("allergy").value;
    const restriction = document.getElementById("restriction").value;
    const preference = document.getElementById("preference").value;

    const data = getGuestData();

    submitButton.disabled = true;
    results.textContent = "Подбираем блюда...";

    try {
        const response = await fetch("/api/recommendations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const dishes = await response.json();

        if (!response.ok) {
            throw new Error(dishes.error || "Ошибка получения рекомендаций");
        }

        results.replaceChildren();

        if (dishes.length === 0) {
            results.textContent = "Подходящих блюд не найдено. Попробуйте изменить параметры.";
            return;
        }

        const heading = document.createElement("h3");
        heading.textContent = "Вам подойдут";
        results.appendChild(heading);

        dishes.forEach((dish) => {
            const card = document.createElement("article");
            card.className = "dish-card";

            const name = document.createElement("h3");
            name.textContent = dish.name;

            const price = document.createElement("p");
            price.className = "price";
            price.textContent = `${(dish.price_kopeck / 100).toFixed(2)} ₽`;

            const reasons = document.createElement("p");
            reasons.textContent = dish.reasons.join(" · ");


            const addButton = document.createElement("button");
            addButton.type = "button";
            addButton.className = "add-to-cart";
            addButton.textContent = "Добавить в корзину";

            addButton.addEventListener("click", async () => {
                addButton.disabled = true;

                try {
                    const response = await fetch("/api/cart/validate", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            ...getGuestData(),
                            dish_id: dish.dish_id
                        })
                    });

                    const validated = await response.json();

                    if (!response.ok) {
                        throw new Error(validated.error || "Не удалось добавить блюдо");
                    }

                    cart.push({
                        dish_id: validated.dish_id,
                        name: validated.name,
                        price_kopeck: validated.price_kopeck
                    });

                    renderCart();
                    form.requestSubmit();
                } catch (error) {
                    results.textContent = error.message;
                    addButton.disabled = false;
                }
            });

            card.appendChild(addButton);

            card.append(name, price, reasons);
            results.appendChild(card);
        });
    } catch (error) {
        results.textContent = error.message;
    } finally {
        submitButton.disabled = false;
    }
});

function updateMenuButtons() {
    document.querySelectorAll(".menu-add-button").forEach((button) => {
        const dishId = Number(button.dataset.dishId);
        const added = cart.some(dish => dish.dish_id === dishId);

        button.classList.toggle("is-added", added);
        button.textContent = added ? "Добавлено ✓" : "В корзину";
        button.disabled = added;
    });
}

renderCart();


document.querySelectorAll(".menu-add-button").forEach((button) => {
    button.addEventListener("click", async () => {
        const dishId = Number(button.dataset.dishId);

        button.disabled = true;
        button.textContent = "Проверяем...";

        try {
            const response = await fetch("/api/menu/add/validate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    ...getGuestData(),
                    dish_id: dishId
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Не удалось добавить блюдо");
            }

            cart.push({
                dish_id: data.dish_id,
                name: data.name,
                price_kopeck: data.price_kopeck
            });

            if (
                data.category === "main" &&
                document.getElementById("stage").value === "before_order"
            ) {
                document.getElementById("stage").value = "after_main";
            }

            renderCart();
            form.requestSubmit();

        } catch (error) {
            alert(error.message);
        } finally {
            updateMenuButtons();
        }
    });
});

const dessertButton = document.getElementById("go-to-dessert");

dessertButton.addEventListener("click", () => {
    document.getElementById("stage").value = "before_dessert";

    if (!panel.classList.contains("is-open")) {
        toggleButton.click();
    }

    form.requestSubmit();
});
