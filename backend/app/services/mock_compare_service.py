from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.models import (
    BasketOptimisationResult,
    CompareRequest,
    CompareResponse,
    GroceryCategory,
    ItemSelectionResult,
    MatchQuality,
    MixedBasketResult,
    Supermarket,
    SupermarketBasketTotal,
    SupermarketProduct,
    build_intent,
)


def _sample_product(supermarket: Supermarket, name: str, category: GroceryCategory, price: str, brand: str, own_brand: bool) -> SupermarketProduct:
    unit_value = Decimal(price)
    return SupermarketProduct(
        id=uuid4(),
        supermarketName=supermarket.name,
        name=name,
        category=category,
        subcategory="standard",
        price=Decimal(price),
        size="1 unit",
        brand=brand,
        isOwnBrand=own_brand,
        isPremium=False,
        isOrganic=False,
        unitDescription="£/unit",
        unitValue=unit_value,
        tags=[category.value, name.lower()],
    )


def _selection(intent, supermarket: Supermarket, product: SupermarketProduct) -> ItemSelectionResult:
    quantity = intent.quantity
    total = product.price * Decimal(quantity)
    return ItemSelectionResult(
        id=uuid4(),
        intent=intent,
        supermarket=supermarket,
        product=product,
        quantity=quantity,
        unitPrice=product.price,
        unitPriceDescription=f"{product.unitDescription} {product.unitValue}",
        totalPrice=total,
        matchQuality=MatchQuality.exact,
        confidence=Decimal("0.91"),
        reasons=["Exact category match.", "Mock response for live API wiring."],
    )


def build_comparison(request: CompareRequest) -> CompareResponse:
    markets = request.supermarkets
    if len(markets) < 2:
        fallback = Supermarket(id=uuid4(), name="Tesco", description="Tesco Extra")
        markets = markets + [fallback]

    market_a = markets[0]
    market_b = markets[1]

    milk_intent = build_intent("Semi-skimmed milk", 2, GroceryCategory.milk, ["milk", "semi skimmed"])
    bread_intent = build_intent("Wholemeal bread", 1, GroceryCategory.bread, ["bread", "wholemeal"])
    eggs_intent = build_intent("Free-range eggs", 1, GroceryCategory.eggs, ["eggs", "free range"])
    intents = [milk_intent, bread_intent, eggs_intent]

    a_milk = _sample_product(market_a, f"{market_a.name} Semi-Skimmed Milk 2L", GroceryCategory.milk, "1.65", market_a.name, True)
    a_bread = _sample_product(market_a, f"{market_a.name} Wholemeal Bread", GroceryCategory.bread, "1.30", market_a.name, True)
    a_eggs = _sample_product(market_a, f"{market_a.name} Free-Range Eggs 12", GroceryCategory.eggs, "2.75", market_a.name, True)

    b_milk = _sample_product(market_b, f"{market_b.name} Semi-Skimmed Milk 2L", GroceryCategory.milk, "1.55", market_b.name, True)
    b_bread = _sample_product(market_b, f"{market_b.name} Wholemeal Bread", GroceryCategory.bread, "1.42", market_b.name, True)
    b_eggs = _sample_product(market_b, f"{market_b.name} Free-Range Eggs 12", GroceryCategory.eggs, "2.49", market_b.name, False)

    selections_a = [_selection(milk_intent, market_a, a_milk), _selection(bread_intent, market_a, a_bread), _selection(eggs_intent, market_a, a_eggs)]
    selections_b = [_selection(milk_intent, market_b, b_milk), _selection(bread_intent, market_b, b_bread), _selection(eggs_intent, market_b, b_eggs)]

    total_a = sum((item.totalPrice for item in selections_a), Decimal("0.00"))
    total_b = sum((item.totalPrice for item in selections_b), Decimal("0.00"))

    market_total_a = SupermarketBasketTotal(
        id=uuid4(),
        supermarket=market_a,
        selections=selections_a,
        unavailableItems=[],
        total=total_a,
    )
    market_total_b = SupermarketBasketTotal(
        id=uuid4(),
        supermarket=market_b,
        selections=selections_b,
        unavailableItems=[],
        total=total_b,
    )

    supermarket_totals = sorted([market_total_a, market_total_b], key=lambda x: x.total)
    cheapest_single = supermarket_totals[0]

    mixed_selections = [
        _selection(milk_intent, market_b, b_milk),
        _selection(bread_intent, market_a, a_bread),
        _selection(eggs_intent, market_b, b_eggs),
    ]
    mixed_total = sum((item.totalPrice for item in mixed_selections), Decimal("0.00"))
    mixed = MixedBasketResult(selections=mixed_selections, unavailableItems=[], total=mixed_total)

    selected = mixed if request.comparisonMode.value == "cheapestPossible" else MixedBasketResult(
        selections=cheapest_single.selections,
        unavailableItems=cheapest_single.unavailableItems,
        total=cheapest_single.total,
    )

    result = BasketOptimisationResult(
        shoppingList=request.shoppingList,
        intents=intents,
        supermarketTotals=supermarket_totals,
        cheapestSingleStore=cheapest_single,
        mixedBasket=mixed,
        selectedBasket=selected,
        comparisonMode=request.comparisonMode,
        preferences=request.preferences,
    )

    most_expensive_total = supermarket_totals[-1].total
    savings_vs_most_expensive = most_expensive_total - selected.total
    savings_vs_cheapest_single = cheapest_single.total - selected.total

    return CompareResponse(
        result=result,
        savingsVsMostExpensive=savings_vs_most_expensive,
        savingsVsCheapestSingleStore=savings_vs_cheapest_single,
    )
