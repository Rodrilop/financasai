from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

from database import get_connection, init_db
from analyzer import compute_analysis, get_settings, get_all_income
from market import get_market_data, get_allocation
from ai_engine import generate_recommendations, chat_with_ai
from auth import get_password_hash, verify_password, create_access_token, get_current_user

app = FastAPI(title="FinançasAI API")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions globally and log them."""
    logger.error(f"Global Error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Erro interno no servidor."})

@app.on_event("startup")
def startup():
    init_db()

# ── Models ──────────────────────────────────────────────────────────────────

class SettingsIn(BaseModel):
    salary: float = Field(0, ge=0)
    reference_month: str = Field("", max_length=7)
    emergency_reserve_goal: float = Field(0, ge=0)
    investment_pct: float = Field(20, ge=0, le=100)
    investor_profile: str = Field("moderado", max_length=20)
    budget_essential_pct: float = Field(50, ge=0, le=100)
    budget_important_pct: float = Field(30, ge=0, le=100)
    budget_optional_pct: float = Field(20, ge=0, le=100)

class IncomeIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)

class ExpenseIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    priority: str = Field(..., min_length=1, max_length=20)
    date: str = Field(..., max_length=10)
    notes: Optional[str] = Field("", max_length=500)

class BulkDeleteIn(BaseModel):
    ids: List[int]

class ChatIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    month: Optional[str] = None

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

# ── Auth ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register(user: UserRegister):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email=?", (user.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    hashed = get_password_hash(user.password)
    conn.execute("INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
                       (user.name, user.email, hashed))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/api/auth/login")
def login(user: UserLogin):
    conn = get_connection()
    db_user = conn.execute("SELECT * FROM users WHERE email=?", (user.email,)).fetchone()
    conn.close()
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "name": db_user["name"]}

# ── Settings ─────────────────────────────────────────────────────────────────

@app.get("/api/settings")
def read_settings(user: str = Depends(get_current_user)):
    """Return user settings and configuration parameters."""
    return get_settings()

@app.put("/api/settings")
def update_settings(data: SettingsIn, user: str = Depends(get_current_user)):
    """Update user settings in the database."""
    logger.info(f"Updating settings for user: {user}")
    conn = get_connection()
    conn.execute("""UPDATE settings SET salary=?,reference_month=?,emergency_reserve_goal=?,
                    investment_pct=?,investor_profile=?,budget_essential_pct=?,
                    budget_important_pct=?,budget_optional_pct=? WHERE id=1""",
                 (data.salary, data.reference_month, data.emergency_reserve_goal,
                  data.investment_pct, data.investor_profile, data.budget_essential_pct,
                  data.budget_important_pct, data.budget_optional_pct))
    conn.commit(); conn.close()
    return {"ok": True}

# ── Income ────────────────────────────────────────────────────────────────────

@app.get("/api/income")
def read_income(user: str = Depends(get_current_user)):
    return get_all_income()

@app.post("/api/income", status_code=201)
def add_income(data: IncomeIn, user: str = Depends(get_current_user)):
    """Add a new income record."""
    logger.info(f"Adding income for user: {user}, amount: {data.amount}")
    conn = get_connection()
    cur = conn.execute("INSERT INTO income (name,amount) VALUES (?,?)", (data.name, data.amount))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.delete("/api/income/{income_id}")
def delete_income(income_id: int, user: str = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM income WHERE id=?", (income_id,))
    conn.commit(); conn.close()
    return {"ok": True}

# ── Expenses ──────────────────────────────────────────────────────────────────

@app.get("/api/expenses")
def read_expenses(user: str = Depends(get_current_user), month: Optional[str] = None,
                  category: Optional[str] = None, priority: Optional[str] = None,
                  q: Optional[str] = None):
    """Read expenses with optional filtering by month, category, priority or search query."""
    conn = get_connection()
    sql = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if month:
        sql += " AND date LIKE ?"; params.append(f"{month}%")
    if category:
        sql += " AND category=?"; params.append(category)
    if priority:
        sql += " AND priority=?"; params.append(priority)
    if q:
        sql += " AND description LIKE ?"; params.append(f"%{q}%")
    sql += " ORDER BY date DESC"
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/expenses", status_code=201)
def add_expense(data: ExpenseIn, user: str = Depends(get_current_user)):
    """Add a new expense record."""
    logger.info(f"Adding expense for user: {user}, amount: {data.amount}, category: {data.category}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO expenses (description,amount,category,priority,date,notes) VALUES (?,?,?,?,?,?)",
        (data.description, data.amount, data.category, data.priority, data.date, data.notes)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.put("/api/expenses/{expense_id}")
def update_expense(expense_id: int, data: ExpenseIn, user: str = Depends(get_current_user)):
    conn = get_connection()
    conn.execute(
        "UPDATE expenses SET description=?,amount=?,category=?,priority=?,date=?,notes=? WHERE id=?",
        (data.description, data.amount, data.category, data.priority, data.date, data.notes, expense_id)
    )
    conn.commit(); conn.close()
    return {"id": expense_id, **data.dict()}

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, user: str = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit(); conn.close()
    return {"ok": True}

@app.post("/api/expenses/bulk-delete")
def bulk_delete(data: BulkDeleteIn, user: str = Depends(get_current_user)):
    conn = get_connection()
    conn.execute(f"DELETE FROM expenses WHERE id IN ({','.join('?'*len(data.ids))})", tuple(data.ids))
    conn.commit(); conn.close()
    return {"deleted": len(data.ids)}

# ── Analysis ──────────────────────────────────────────────────────────────────

@app.get("/api/analysis")
def analysis(user: str = Depends(get_current_user), month: Optional[str] = None):
    return compute_analysis(month)

@app.get("/api/analysis/recommendations")
def recommendations(request: Request, month: Optional[str] = None, user: str = Depends(get_current_user)):
    data = compute_analysis(month)
    text = generate_recommendations(data)
    return {"text": text}

@app.post("/api/chat")
def chat(request: Request, data: ChatIn, user: str = Depends(get_current_user)):
    analysis_data = compute_analysis(data.month)
    answer = chat_with_ai(data.question, analysis_data)
    return {"answer": answer}

# ── Market & Investments ──────────────────────────────────────────────────────

@app.get("/api/market")
def market(user: str = Depends(get_current_user)):
    return get_market_data()

@app.get("/api/investments")
def investments(user: str = Depends(get_current_user), month: Optional[str] = None):
    data = compute_analysis(month)
    profile = data.get("investor_profile", "moderado")
    amount = data.get("investment_suggested", 0)
    alloc = get_allocation(profile, amount)
    return {**alloc, "investment_suggested": amount,
            "emergency_goal": data.get("emergency_goal", 0),
            "balance": data.get("balance", 0)}

@app.get("/health")
def health():
    return {"status": "ok"}
