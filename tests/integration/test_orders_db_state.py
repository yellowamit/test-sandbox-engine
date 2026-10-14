import pytest
from decimal import Decimal
from app.models import User, Product, Order, OrderItem

@pytest.mark.req_id("REQ-INT-01")
def test_successful_checkout_atomic_db_mutation(client, db_session):
    user_before = db_session.query(User).filter(User.id == 1).first()
    product_before = db_session.query(Product).filter(Product.id == 1).first()

    initial_balance = user_before.wallet_balance
    initial_stock = product_before.stock_quantity
    order_qty = 2
    item_price = product_before.price

    payload = {
        "user_id": 1,
        "items": [{"product_id": 1, "quantity": order_qty}]
    }
    response = client.post("/orders/checkout", json=payload)
    assert response.status_code == 201
    data = response.json()

    db_session.expire_all()
    user_after = db_session.query(User).filter(User.id == 1).first()
    product_after = db_session.query(Product).filter(Product.id == 1).first()

    expected_deduction = Decimal(str(item_price)) * order_qty
    assert user_after.wallet_balance == initial_balance - expected_deduction
    assert product_after.stock_quantity == initial_stock - order_qty

    persisted_order = db_session.query(Order).filter(Order.order_ref == data["order_ref"]).first()
    assert persisted_order is not None
    assert persisted_order.total_amount == expected_deduction

    order_item = db_session.query(OrderItem).filter(OrderItem.order_id == persisted_order.id).first()
    assert order_item.quantity == order_qty
    assert order_item.product_id == 1

@pytest.mark.req_id("REQ-INT-02")
def test_rejection_on_zero_inventory_no_db_mutation(client, db_session):
    user_before = db_session.query(User).filter(User.id == 1).first()
    initial_balance = user_before.wallet_balance

    payload = {
        "user_id": 1,
        "items": [{"product_id": 3, "quantity": 1}]  # Product 3 has 0 stock
    }
    response = client.post("/orders/checkout", json=payload)
    assert response.status_code == 400
    assert "Insufficient inventory" in response.json()["detail"]

    db_session.expire_all()
    user_after = db_session.query(User).filter(User.id == 1).first()
    assert user_after.wallet_balance == initial_balance

@pytest.mark.req_id("REQ-INT-03")
def test_rejection_on_insufficient_wallet_balance(client, db_session):
    product_before = db_session.query(Product).filter(Product.id == 1).first()
    initial_stock = product_before.stock_quantity

    payload = {
        "user_id": 2,  # Bob has 0 balance
        "items": [{"product_id": 1, "quantity": 1}]
    }
    response = client.post("/orders/checkout", json=payload)
    assert response.status_code == 400
    assert "Insufficient wallet funds" in response.json()["detail"]

    db_session.expire_all()
    product_after = db_session.query(Product).filter(Product.id == 1).first()
    assert product_after.stock_quantity == initial_stock
