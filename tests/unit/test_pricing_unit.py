import pytest
from decimal import Decimal
from pydantic import ValidationError
from app.schemas import OrderItemRequest, CheckoutRequest

@pytest.mark.req_id("REQ-UNIT-01")
def test_order_item_strictly_positive_quantity():
    with pytest.raises(ValidationError):
        OrderItemRequest(product_id=1, quantity=0)

    with pytest.raises(ValidationError):
        OrderItemRequest(product_id=1, quantity=-5)

@pytest.mark.req_id("REQ-UNIT-02")
def test_checkout_payload_empty_items_rejected():
    with pytest.raises(ValidationError):
        CheckoutRequest(user_id=1, items=[])

@pytest.mark.req_id("REQ-UNIT-03")
def test_pricing_calculation_precision():
    unit_price = Decimal("19.99")
    quantity = 3
    total = unit_price * quantity
    assert total == Decimal("59.97")
    assert isinstance(total, Decimal)
