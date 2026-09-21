from sqlalchemy import Column, Date, DateTime, Float, Integer, String, func

from .database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    note = Column(String(500), nullable=True)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
