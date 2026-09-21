import os
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import crud, schemas
from .auth import require_api_key
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spend Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/expenses", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    return crud.create_expense(db, expense)


@app.get("/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    return crud.list_expenses(db, category, start_date, end_date, skip, limit)


@app.get("/summary", response_model=schemas.SummaryOut)
def summary(
    month: Optional[str] = Query(None, description="YYYY-MM, defaults to current month"),
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    try:
        return crud.get_summary(db, month)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
