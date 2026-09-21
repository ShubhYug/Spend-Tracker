from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Expense amount, must be positive")
    category: str = Field(..., min_length=1, max_length=64)
    note: Optional[str] = Field(None, max_length=500)
    date: date_type

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("category must not be blank")
        return v

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: date_type) -> date_type:
        if v > date_type.today():
            raise ValueError("date cannot be in the future")
        return v


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    category: str
    note: Optional[str]
    date: date_type
    created_at: datetime


class CategoryTotal(BaseModel):
    category: str
    total: float


class CategoryChange(BaseModel):
    category: str
    current: float
    previous: float
    change_pct: Optional[float]


class SummaryOut(BaseModel):
    month: str
    total_spend: float
    by_category: list[CategoryTotal]
    previous_month_total: float
    total_change_pct: Optional[float]
    by_category_change: list[CategoryChange]
    insights: list[str]
