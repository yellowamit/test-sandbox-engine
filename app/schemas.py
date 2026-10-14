from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, description="Quantity must be strictly positive")

class CheckoutRequest(BaseModel):
    user_id: int
    items: List[OrderItemRequest] = Field(min_length=1)

class CheckoutResponse(BaseModel):
    order_ref: str
    status: str
    total_amount: Decimal
    remaining_balance: Decimal
