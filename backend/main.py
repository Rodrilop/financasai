from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import logging
import csv
import io

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

from database import get_connection, init_db, ensure_user_settings
from analyzer import compute_analysis, get_settings, get_income_for_month
from market import get_market_data, get_allocation, get_user_portfolio_data
from ai_engine import generate_recommendations, chat_with_ai, generate_proactive_alert
from apscheduler.schedulers.background import BackgroundScheduler
from auth import get_password_hash, verify_password, create_access_token, get_current_user

app = FastAPI(title="FinançasAI API")

_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_allowed_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]
app.add_middleware(CORSMiddleware, allow_origins=_allowed_origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions globally and log them."""
    logger.error(f"Global Error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Erro interno no servidor."})

def run_proactive_agent():
    """Background task to generate autonomous alerts for all users."""
    conn = get_connection()
    try:
        users = conn.execute("SELECT DISTINCT user_id FROM settings").fetchall()
        for row in users:
            uid = row["user_id"]
            analysis = compute_analysis(uid)
            alert = generate_proactive_alert(uid, analysis)
            if alert:
                conn.execute("INSERT INTO notifications (user_id, title, message) VALUES (?,?,?)", (uid, alert["title"], alert["message"]))
        conn.commit()
    except Exception as e:
        logger.error(f"Proactive Error: {e}")
    finally:
        conn.close()

@app.on_event("startup")
def startup():
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_proactive_agent, 'interval', hours=24)
    scheduler.start()

# ── Models ──────────────────────────────────────────────────────────────────

class SettingsIn(BaseModel):
    reference_month: str = Field("", max_length=7)
    emergency_reserve_goal: float = Field(0, ge=0)
    investment_pct: float = Field(20, ge=0, le=100)
    investor_profile: str = Field("moderado", max_length=20)
    budget_essential_pct: float = Field(50, ge=0, le=100)
    budget_important_pct: float = Field(30, ge=0, le=100)
    budget_optional_pct: float = Field(20, ge=0, le=100)

class AccountIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field("Conta Corrente", max_length=30)

class IncomeIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    account: Optional[str] = "Geral"

class ExpenseIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    category: str
    priority: str
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: Optional[str] = ""
    account: Optional[str] = "Geral"

class PortfolioItemIn(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    average_price: float = Field(..., gt=0)

class BulkDeleteIn(BaseModel):
    ids: List[int]

class ChatIn(BaseModel):
    question: str = Field(..., min_length=1)
    month: Optional[str] = None
    image_base64: Optional[str] = None
    audio_base64: Optional[str] = None

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

class ProfileIn(BaseModel):
    phone: Optional[str] = Field(None, max_length=20)

# ── Auth ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register(user: UserRegister):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email=?", (user.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    hashed = get_password_hash(user.password)
    cur = conn.execute(
        "INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
        (user.name, user.email, hashed)
    )
    conn.commit()
    new_user_id = cur.lastrowid
    conn.close()
    # Create isolated settings row for the new user
    ensure_user_settings(new_user_id)
    return {"ok": True}

@app.post("/api/auth/login")
def login(user: UserLogin):
    conn = get_connection()
    db_user = conn.execute("SELECT * FROM users WHERE email=?", (user.email,)).fetchone()
    conn.close()
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    # Ensure settings exist (safety net for pre-existing users)
    ensure_user_settings(db_user["id"])
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "name": db_user["name"], "phone": db_user["phone"], "is_pro": bool(db_user["is_pro"])}

@app.get("/api/profile")
def get_profile(user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile info."""
    conn = get_connection()
    row = conn.execute("SELECT id, name, email, phone, is_pro FROM users WHERE id=?", (user["id"],)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"id": row["id"], "name": row["name"], "email": row["email"], "phone": row["phone"], "is_pro": bool(row["is_pro"])}

@app.post("/api/auth/upgrade")
def upgrade_user(user: dict = Depends(get_current_user)):
    """Simulate upgrading to Pro."""
    conn = get_connection()
    conn.execute("UPDATE users SET is_pro=1 WHERE id=?", (user["id"],))
    conn.commit()
    conn.close()
    return {"ok": True, "message": "Parabéns! Você agora é um usuário PRO."}

@app.put("/api/profile")
def update_profile(data: ProfileIn, user: dict = Depends(get_current_user)):
    """Update the authenticated user's phone number for WhatsApp integration."""
    uid = user["id"]
    # Normalize: keep only digits
    clean_phone = ''.join(filter(str.isdigit, data.phone or ''))
    if clean_phone and len(clean_phone) < 10:
        raise HTTPException(status_code=400, detail="Número de telefone inválido. Use o formato com DDD (ex: 11999998888).")
    conn = get_connection()
    conn.execute("UPDATE users SET phone=? WHERE id=?", (clean_phone or None, uid))
    conn.commit()
    conn.close()
    logger.info(f"Updated phone for user_id={uid}: {clean_phone}")
    return {"ok": True, "phone": clean_phone or None}

# ── Accounts ──────────────────────────────────────────────────────────────────

@app.get("/api/accounts")
def read_accounts(user: dict = Depends(get_current_user)):
    uid = user["id"]
    conn = get_connection()
    rows = conn.execute("SELECT * FROM accounts WHERE user_id=? ORDER BY name ASC", (uid,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/accounts")
def add_account(data: AccountIn, user: dict = Depends(get_current_user)):
    uid = user["id"]
    conn = get_connection()
    cur = conn.execute("INSERT INTO accounts (user_id, name, type) VALUES (?, ?, ?)", (uid, data.name, data.type))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM accounts WHERE id=? AND user_id=?", (account_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}

# ── Settings ─────────────────────────────────────────────────────────────────

@app.get("/api/settings")
def read_settings(user: dict = Depends(get_current_user)):
    """Return the authenticated user's settings."""
    return get_settings(user["id"])

@app.put("/api/settings")
def update_settings(data: SettingsIn, user: dict = Depends(get_current_user)):
    """Update the authenticated user's settings."""
    uid = user["id"]
    logger.info(f"Updating settings for user_id: {uid}")
    conn = get_connection()
    exists = conn.execute("SELECT id FROM settings WHERE user_id=?", (uid,)).fetchone()
    if exists:
        conn.execute("""UPDATE settings SET reference_month=?,emergency_reserve_goal=?,
                        investment_pct=?,investor_profile=?,budget_essential_pct=?,
                        budget_important_pct=?,budget_optional_pct=? WHERE user_id=?""",
                     (data.reference_month, data.emergency_reserve_goal,
                      data.investment_pct, data.investor_profile, data.budget_essential_pct,
                      data.budget_important_pct, data.budget_optional_pct, uid))
    else:
        conn.execute("""INSERT INTO settings
                        (user_id,reference_month,emergency_reserve_goal,
                         investment_pct,investor_profile,budget_essential_pct,
                         budget_important_pct,budget_optional_pct)
                        VALUES (?,?,?,?,?,?,?,?)""",
                     (uid, data.reference_month, data.emergency_reserve_goal,
                      data.investment_pct, data.investor_profile, data.budget_essential_pct,
                      data.budget_important_pct, data.budget_optional_pct))
    conn.commit()
    conn.close()
    return {"ok": True}

# ── Income ────────────────────────────────────────────────────────────────────

@app.get("/api/income")
def read_income(user: dict = Depends(get_current_user), month: Optional[str] = None):
    conn = get_connection()
    sql = "SELECT * FROM income WHERE user_id=?"
    params = [user["id"]]
    if month:
        sql += " AND date LIKE ?"
        params.append(f"{month}%")
    sql += " ORDER BY date DESC"
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/income", status_code=201)
def add_income(data: IncomeIn, user: dict = Depends(get_current_user)):
    """Add a new income record for the authenticated user."""
    uid = user["id"]
    logger.info(f"Adding income for user_id: {uid}, amount: {data.amount}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO income (user_id, account, name, amount, date) VALUES (?, ?, ?, ?, ?)",
        (uid, data.account or 'Geral', data.name, data.amount, data.date)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.delete("/api/income/{income_id}")
def delete_income(income_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM income WHERE id=? AND user_id=?", (income_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.put("/api/income/{income_id}")
def update_income(income_id: int, data: IncomeIn, user: dict = Depends(get_current_user)):
    """Edit an existing income record."""
    conn = get_connection()
    conn.execute(
        "UPDATE income SET account=?, name=?, amount=?, date=? WHERE id=? AND user_id=?",
        (data.account or 'Geral', data.name, data.amount, data.date, income_id, user["id"])
    )
    conn.commit()
    conn.close()
    return {"id": income_id, **data.dict()}

# ── Expenses ──────────────────────────────────────────────────────────────────

@app.get("/api/expenses")
def read_expenses(user: dict = Depends(get_current_user), month: Optional[str] = None,
                  category: Optional[str] = None, priority: Optional[str] = None,
                  q: Optional[str] = None):
    """Read the authenticated user's expenses with optional filters."""
    uid = user["id"]
    conn = get_connection()
    sql = "SELECT * FROM expenses WHERE user_id=?"
    params: list = [uid]
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
def add_expense(data: ExpenseIn, user: dict = Depends(get_current_user)):
    """Add a new expense record for the authenticated user."""
    uid = user["id"]
    logger.info(f"Adding expense for user_id: {uid}, amount: {data.amount}, category: {data.category}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO expenses (user_id, account, description, amount, category, priority, date, notes) VALUES (?,?,?,?,?,?,?,?)",
        (uid, data.account or 'Geral', data.description, data.amount, data.category, data.priority, data.date, data.notes)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.put("/api/expenses/{expense_id}")
def update_expense(expense_id: int, data: ExpenseIn, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute(
        "UPDATE expenses SET account=?, description=?,amount=?,category=?,priority=?,date=?,notes=? WHERE id=? AND user_id=?",
        (data.account or 'Geral', data.description, data.amount, data.category, data.priority, data.date, data.notes,
         expense_id, user["id"])
    )
    conn.commit()
    conn.close()
    return {"id": expense_id, **data.dict()}

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/api/expenses/import")
async def import_expenses(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Import expenses from a CSV file."""
    uid = user["id"]
    content = await file.read()
    decoded = content.decode("utf-8-sig") # handles UTF-8 BOM
    f = io.StringIO(decoded)
    # Improved CSV detection
    try:
        sample = decoded[:2048]
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=',;\t|')
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
    except Exception:
        # Fallback to comma then semicolon if sniffer fails
        f.seek(0)
        reader = csv.DictReader(f, delimiter=',')
        if not reader.fieldnames or len(reader.fieldnames) < 2:
            f.seek(0)
            reader = csv.DictReader(f, delimiter=';')

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Formato CSV inválido ou cabeçalhos não encontrados.")

    # Mapping logic (Case-insensitive)
    cols = {name.lower().strip(): name for name in reader.fieldnames}
    date_col = next((cols[k] for k in ['data', 'date', 'vencimento', 'dia'] if k in cols), None)
    desc_col = next((cols[k] for k in ['descrição', 'descricao', 'description', 'histórico', 'historico', 'item', 'detalhe'] if k in cols), None)
    val_col  = next((cols[k] for k in ['valor', 'amount', 'total', 'preço', 'preco', 'pago'] if k in cols), None)
    cat_col  = next((cols[k] for k in ['categoria', 'category', 'tipo'] if k in cols), None)

    if not all([date_col, desc_col, val_col]):
        raise HTTPException(status_code=400, detail=f"Colunas obrigatórias (Data, Descrição, Valor) não encontradas. Detectado: {list(reader.fieldnames)}")

    expenses_to_add = []
    for row in reader:
        try:
            # Clean amount: remove currency symbols and handle European/Brazilian number format
            raw_val = str(row[val_col]).replace('R$', '').replace('$', '').strip()
            # If it has both . and , (e.g. 1.234,56), remove the . and replace , with .
            if '.' in raw_val and ',' in raw_val:
                raw_val = raw_val.replace('.', '').replace(',', '.')
            elif ',' in raw_val:
                raw_val = raw_val.replace(',', '.')
                
            amount = abs(float(raw_val))
            
            # Normalize date
            raw_date = row[date_col].strip()
            d_obj = None
            
            # Try various formats
            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%m/%d/%Y", "%Y/%m/%d"]:
                try:
                    d_obj = datetime.strptime(raw_date, fmt)
                    break
                except: continue
            
            if not d_obj:
                try: d_obj = datetime.fromisoformat(raw_date)
                except: pass
            
            if not d_obj:
                logger.warning(f"Could not parse date: {raw_date}")
                continue
            
            clean_date = d_obj.strftime("%Y-%m-%d")
            
            expenses_to_add.append((
                uid,
                row[desc_col].strip(),
                amount,
                row.get(cat_col, 'Outros').strip() if cat_col else 'Outros',
                'Essencial', 
                clean_date,
                'Importado via CSV'
            ))
        except Exception as e:
            logger.warning(f"Error parsing CSV row: {e} | Row: {row}")
            continue

    if not expenses_to_add:
        raise HTTPException(status_code=400, detail="Nenhuma despesa válida encontrada no arquivo.")

    conn = get_connection()
    try:
        sql = "INSERT INTO expenses (user_id, description, amount, category, priority, date, notes) VALUES (?,?,?,?,?,?,?)"
        if hasattr(conn, 'executemany'):
            conn.executemany(sql, expenses_to_add)
        else:
            # Fallback for standard sqlite3 connection (though it has executemany too)
            for exp in expenses_to_add:
                conn.execute(sql, exp)
        
        conn.commit()
    finally:
        conn.close()
    
    return {"ok": True, "count": len(expenses_to_add)}

@app.post("/api/expenses/bulk-delete")
def bulk_delete(data: BulkDeleteIn, user: dict = Depends(get_current_user)):
    uid = user["id"]
    conn = get_connection()
    conn.execute(
        f"DELETE FROM expenses WHERE user_id=? AND id IN ({','.join('?'*len(data.ids))})",
        tuple([uid] + data.ids)
    )
    conn.commit()
    conn.close()
    return {"deleted": len(data.ids)}

# ── Analysis ──────────────────────────────────────────────────────────────────

@app.get("/api/analysis")
def analysis(user: dict = Depends(get_current_user), month: Optional[str] = None):
    return compute_analysis(user["id"], month)

@app.get("/api/analysis/recommendations")
def recommendations(request: Request, month: Optional[str] = None, user: dict = Depends(get_current_user)):
    data = compute_analysis(user["id"], month)
    text = generate_recommendations(data)
    return {"text": text}

@app.post("/api/chat")
def chat(request: Request, data: ChatIn, user: dict = Depends(get_current_user)):
    analysis_data = compute_analysis(user["id"], data.month)
    answer = chat_with_ai(data.question, analysis_data, user["id"], data.image_base64, data.audio_base64)
    return {"answer": answer}

# ── Market & Investments ──────────────────────────────────────────────────────

@app.get("/api/market")
def market(user: dict = Depends(get_current_user)):
    return get_market_data()

@app.get("/api/investments")
def investments(user: dict = Depends(get_current_user), month: Optional[str] = None):
    data = compute_analysis(user["id"], month)
    profile = data.get("investor_profile", "moderado")
    amount = data.get("investment_suggested", 0)
    alloc = get_allocation(profile, amount)
    return {**alloc, "investment_suggested": amount,
            "emergency_goal": data.get("emergency_goal", 0),
            "balance": data.get("balance", 0)}

@app.get("/api/portfolio")
def get_portfolio(user: dict = Depends(get_current_user)):
    return get_user_portfolio_data(user["id"])

@app.post("/api/portfolio")
def add_portfolio_item(item: PortfolioItemIn, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        # Check if already exists to update or insert
        row = conn.execute("SELECT id, quantity, average_price FROM portfolio WHERE user_id=? AND ticker=?", (user["id"], item.ticker.upper())).fetchone()
        if row:
            # Calculate new average price
            new_qty = row["quantity"] + item.quantity
            new_avg = ((row["quantity"] * row["average_price"]) + (item.quantity * item.average_price)) / new_qty
            conn.execute("UPDATE portfolio SET quantity=?, average_price=? WHERE id=?", (new_qty, new_avg, row["id"]))
        else:
            conn.execute("INSERT INTO portfolio (user_id, ticker, quantity, average_price) VALUES (?,?,?,?)",
                         (user["id"], item.ticker.upper(), item.quantity, item.average_price))
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()

@app.delete("/api/portfolio/{item_id}")
def delete_portfolio_item(item_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM portfolio WHERE id=? AND user_id=?", (item_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

# ── Notifications & Proactive Agent ───────────────────────────────────────────

@app.get("/api/notifications")
def get_notifications(user: dict = Depends(get_current_user)):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50", (user["id"],)).fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "message": r["message"], "is_read": bool(r["is_read"]), "created_at": r["created_at"]} for r in rows]

@app.put("/api/notifications/{notif_id}/read")
def read_notification(notif_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?", (notif_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/agent/trigger")
def trigger_agent(user: dict = Depends(get_current_user)):
    """Manual trigger to generate proactive alert for current user (for testing)."""
    analysis = compute_analysis(user["id"])
    alert = generate_proactive_alert(user["id"], analysis)
    if alert:
        conn = get_connection()
        conn.execute("INSERT INTO notifications (user_id, title, message) VALUES (?,?,?)", (user["id"], alert["title"], alert["message"]))
        conn.commit()
        conn.close()
        return {"status": "success", "alert": alert}
    return {"status": "success", "message": "Nenhuma dica necessária no momento."}

# ── WhatsApp Webhook (Meta / WhatsApp Cloud API) ─────────────────────────────

@app.get("/api/webhook/whatsapp")
async def whatsapp_verify(request: Request):
    """Webhook verification for Meta WhatsApp Cloud API."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "financasai_token")
    
    if mode == "subscribe" and token == verify_token:
        from fastapi.responses import Response
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

async def process_whatsapp_ai(remote_jid: str, body_text: str, ai_user_id: int):
    """Background task to process AI and send WhatsApp response."""
    try:
        # AI Processing
        analysis_data = compute_analysis(ai_user_id)
        answer = chat_with_ai(body_text, analysis_data, ai_user_id)

        # Send response via Meta Graph API
        token = os.getenv("WHATSAPP_CLOUD_TOKEN")
        phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        
        if token and phone_id:
            import requests
            url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": remote_jid,
                "type": "text",
                "text": {"body": answer}
            }
            resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Meta API Error: {resp.text}")
            else:
                logger.info(f"Response sent to {remote_jid}")
    except Exception as e:
        logger.error(f"Background WhatsApp Task Error: {e}", exc_info=True)

@app.post("/api/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handling incoming messages from Meta WhatsApp Cloud API.
    """
    try:
        body = await request.json()
        
        entry = body.get("entry", [])
        if not entry: return {"status": "ignored"}
        
        changes = entry[0].get("changes", [])
        if not changes: return {"status": "ignored"}
        
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return {"status": "ok"}
            
        msg = messages[0]
        remote_jid = msg.get("from")
        body_text = ""
        
        if msg.get("type") == "text":
            body_text = msg.get("text", {}).get("body", "")
        elif msg.get("type") == "audio":
            body_text = "[Mensagem de voz recebida]"
            
        if not body_text:
            return {"status": "ignored"}

        logger.info(f"WhatsApp Message from {remote_jid}: {body_text}")

        # Resolve user by Phone Number
        clean_jid = ''.join(filter(str.isdigit, remote_jid))
        conn = get_connection()
        wa_user = conn.execute("SELECT id FROM users WHERE phone=?", (clean_jid,)).fetchone()
        if not wa_user and len(clean_jid) > 11:
            suffix = clean_jid[-11:]
            wa_user = conn.execute("SELECT id FROM users WHERE phone LIKE ?", (f"%{suffix}",)).fetchone()

        if not wa_user:
            logger.warning(f"WhatsApp: no user found for phone={clean_jid}")
            conn.close()
            # Important: always return 200 to Meta even if user not found to avoid retries
            return {"status": "ok"}

        ai_user_id = wa_user["id"]
        conn.close()

        # Immediate feedback (to confirm webhook works)
        try:
            token = os.getenv("WHATSAPP_CLOUD_TOKEN")
            phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            if token and phone_id:
                import requests
                url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                payload = {
                    "messaging_product": "whatsapp", "to": remote_jid, "type": "text",
                    "text": {"body": "Recebi sua mensagem! Estou analisando suas financas, so um momento... ⏳"}
                }
                requests.post(url, json=payload, headers=headers)
        except Exception as e:
            logger.error(f"Immediate Feedback Error: {e}")

        # Dispatch AI processing to background tasks
        background_tasks.add_task(process_whatsapp_ai, remote_jid, body_text, ai_user_id)

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"WhatsApp Webhook Error: {e}", exc_info=True)
        return {"status": "ok"} # Always return 200 to Meta

@app.get("/health")
def health():
    return {"status": "ok"}
