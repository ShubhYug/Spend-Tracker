from calendar import monthrange
from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas

INSIGHT_THRESHOLD_PCT = 20.0


def create_expense(db: Session, expense_in: schemas.ExpenseCreate) -> models.Expense:
    expense = models.Expense(**expense_in.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(
    db: Session,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Expense]:
    query = db.query(models.Expense)
    if category:
        query = query.filter(models.Expense.category == category)
    if start_date:
        query = query.filter(models.Expense.date >= start_date)
    if end_date:
        query = query.filter(models.Expense.date <= end_date)
    return (
        query.order_by(models.Expense.date.desc(), models.Expense.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return start, end


def _previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _parse_month(month: Optional[str]) -> tuple[int, int]:
    if not month:
        today = date.today()
        return today.year, today.month
    try:
        year_str, month_str = month.split("-")
        year, mon = int(year_str), int(month_str)
        if not (1 <= mon <= 12) or len(year_str) != 4:
            raise ValueError
    except ValueError as exc:
        raise ValueError("month must be in YYYY-MM format") from exc
    return year, mon


def _totals_by_category(db: Session, start: date, end: date) -> dict[str, float]:
    rows = (
        db.query(models.Expense.category, func.sum(models.Expense.amount))
        .filter(models.Expense.date >= start, models.Expense.date <= end)
        .group_by(models.Expense.category)
        .all()
    )
    return {category: float(total) for category, total in rows}


def _pct_change(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None
    return (current - previous) / previous * 100


def get_summary(db: Session, month: Optional[str]) -> dict:
    year, mon = _parse_month(month)

    cur_start, cur_end = _month_bounds(year, mon)
    prev_year, prev_mon = _previous_month(year, mon)
    prev_start, prev_end = _month_bounds(prev_year, prev_mon)

    cur_totals = _totals_by_category(db, cur_start, cur_end)
    prev_totals = _totals_by_category(db, prev_start, prev_end)

    total_spend = sum(cur_totals.values())
    previous_month_total = sum(prev_totals.values())

    by_category = [
        {"category": category, "total": total}
        for category, total in sorted(cur_totals.items())
    ]

    by_category_change = []
    insights = []
    for category in sorted(set(cur_totals) | set(prev_totals)):
        current = cur_totals.get(category, 0.0)
        previous = prev_totals.get(category, 0.0)
        change_pct = _pct_change(current, previous)
        by_category_change.append(
            {
                "category": category,
                "current": current,
                "previous": previous,
                "change_pct": change_pct,
            }
        )
        if change_pct is not None and change_pct > INSIGHT_THRESHOLD_PCT:
            insights.append(
                f"Spend in '{category}' increased {change_pct:.1f}% vs previous month "
                f"({previous:.2f} -> {current:.2f})"
            )

    return {
        "month": f"{year:04d}-{mon:02d}",
        "total_spend": total_spend,
        "by_category": by_category,
        "previous_month_total": previous_month_total,
        "total_change_pct": _pct_change(total_spend, previous_month_total),
        "by_category_change": by_category_change,
        "insights": insights,
    }
