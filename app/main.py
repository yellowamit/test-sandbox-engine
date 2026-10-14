import uuid
from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models import User, Product, Order, OrderItem
from app.schemas import CheckoutRequest, CheckoutResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ephemeral Test Sandbox SUT", version="1.0.0")

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(Base.metadata.tables["users"].select().limit(1))
    return {"status": "healthy", "database": "connected"}

@app.post("/orders/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def checkout(payload: CheckoutRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == payload.user_id).with_for_update().first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {payload.user_id} not found.")

        total_cost = Decimal("0.00")
        reserved_items = []

        for item in payload.items:
            product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found.")
            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient inventory for '{product.name}'. Required: {item.quantity}, Available: {product.stock_quantity}."
                )

            item_cost = Decimal(str(product.price)) * item.quantity
            total_cost += item_cost
            reserved_items.append((product, item.quantity, product.price))

        if user.wallet_balance < total_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient wallet funds. Total: {total_cost}, Balance: {user.wallet_balance}."
            )

        user.wallet_balance = Decimal(str(user.wallet_balance)) - total_cost

        for product, qty, _ in reserved_items:
            product.stock_quantity -= qty

        order_ref = str(uuid.uuid4())
        new_order = Order(
            order_ref=order_ref,
            user_id=user.id,
            total_amount=total_cost,
            status="COMPLETED"
        )
        db.add(new_order)
        db.flush()

        for product, qty, unit_price in reserved_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price
            )
            db.add(order_item)

        db.commit()
        db.refresh(user)

        return CheckoutResponse(
            order_ref=order_ref,
            status="COMPLETED",
            total_amount=total_cost,
            remaining_balance=user.wallet_balance
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Transaction failed: {str(exc)}")
