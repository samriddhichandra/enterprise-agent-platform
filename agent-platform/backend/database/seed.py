"""
Seeds the demo Employee and Order tables with sample rows so the SQL Tool
has real data to query. Run once after the tables are created:

    python -m backend.database.seed
"""
import asyncio

from sqlalchemy import select

from backend.database.session import async_session, init_db
from backend.database.models import Employee, Order

EMPLOYEES = [
    ("Asha Rao", "Engineering"),
    ("Vikram Shah", "Engineering"),
    ("Priya Nair", "Sales"),
    ("Karan Mehta", "Sales"),
    ("Divya Iyer", "HR"),
]

ORDERS = [
    ("Acme Corp", 4200.00, "completed"),
    ("Globex Ltd", 1500.50, "pending"),
    ("Initech", 9800.00, "completed"),
    ("Acme Corp", 750.00, "cancelled"),
]


async def seed():
    await init_db()
    async with async_session() as session:
        existing = (await session.execute(select(Employee))).scalars().first()
        if existing:
            print("Demo tables already seeded, skipping.")
            return

        for name, dept in EMPLOYEES:
            session.add(Employee(name=name, department=dept))
        for customer, amount, status in ORDERS:
            session.add(Order(customer_name=customer, amount=amount, status=status))

        await session.commit()
        print(f"Seeded {len(EMPLOYEES)} employees and {len(ORDERS)} orders.")


if __name__ == "__main__":
    asyncio.run(seed())
