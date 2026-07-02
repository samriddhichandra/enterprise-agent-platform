"""
SQLAlchemy models for persisting conversations and task history in
PostgreSQL. Kept intentionally small: two tables covers everything this
platform needs to demonstrate persistence without over-engineering it.
"""
import datetime
import uuid

from sqlalchemy import String, Text, DateTime, Integer, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_message: Mapped[str] = mapped_column(Text)
    agent_response: Mapped[str] = mapped_column(Text)
    plan: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string of the planner's subtasks
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String)
    agent_name: Mapped[str] = mapped_column(String)
    input_text: Mapped[str] = mapped_column(Text)
    output_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


# --- Demo "enterprise" tables, purely so the SQL Tool has real data to
# query. In a real deployment the SQL Tool would point at actual company
# tables instead of these seeded demo ones. ---

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    department: Mapped[str] = mapped_column(String)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String)
