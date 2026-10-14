import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from faker import Faker
from app.database import SessionLocal, Base, engine
from app.models import User, Product, Order, OrderItem

fake = Faker()
Faker.seed(42)

def seed_test_database():
    print("[SEED] Seeding deterministic test dataset...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        users = [
            User(id=1, username="alice_funded", email="alice@test.com", wallet_balance=Decimal("5000.00")),
            User(id=2, username="bob_broke", email="bob@test.com", wallet_balance=Decimal("0.00")),
            User(id=3, username="carol_exact", email="carol@test.com", wallet_balance=Decimal("99.99")),
            User(id=4, username="dave_concurrency", email="dave@test.com", wallet_balance=Decimal("1000.00")),
        ]

        products = [
            Product(id=1, sku="SKU-LAPTOP-01", name="Developer Workstation", price=Decimal("1500.00"), stock_quantity=10),
            Product(id=2, sku="SKU-MOUSE-02", name="Ergonomic Mouse", price=Decimal("99.99"), stock_quantity=1),
            Product(id=3, sku="SKU-KEYBRD-03", name="Mechanical Keyboard", price=Decimal("150.00"), stock_quantity=0),
            Product(id=4, sku="SKU-CABLE-04", name="USB-C Monitor Cable", price=Decimal("25.00"), stock_quantity=100),
        ]

        db.add_all(users)
        db.add_all(products)
        db.commit()
        print(f"  [SUCCESS] Seeded {len(users)} users and {len(products)} products with deterministic states.")
    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_database()
