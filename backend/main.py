from pathlib import Path
import sqlite3
import hashlib
import hmac
import secrets
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from agent import reply
from models import ChatRequest, ChatReply

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"
PRODUCTS_PATH = ROOT / "data" / "products"

app = FastAPI(title="Campus Customs API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
app.mount("/images", StaticFiles(directory=PRODUCTS_PATH), name="images")

def query(sql: str, params=()):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params).fetchall()]

class AuthRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(AuthRequest):
    first_name: str
    last_name: str
    confirm_password: str

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, expected = stored.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
        return hmac.compare_digest(actual, expected)
    except ValueError:
        return False

@app.post("/api/auth/register")
def register(request: RegisterRequest):
    if not request.first_name.strip() or not request.last_name.strip():
        raise HTTPException(status_code=400, detail="First and last name are required")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    email = str(request.email).lower()
    if query("SELECT id FROM users WHERE email = ?", (email,)):
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    name = f"{request.first_name.strip()} {request.last_name.strip()}"
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)", (name, email, hash_password(request.password), request.first_name.strip(), request.last_name.strip()))
        user_id = cursor.lastrowid
    return {"id": user_id, "name": name, "email": email}

@app.post("/api/auth/login")
def login(request: AuthRequest):
    email = str(request.email).lower()
    rows = query("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,))
    if not rows or not verify_password(request.password, rows[0]["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {key: rows[0][key] for key in ("id", "name", "email")}

def product(row):
    row["image_url"] = f"/images/{Path(row.pop('image_file_path')).name}"
    row["sizes"] = query("SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY size", (row["product_id"],))
    return row

@app.get("/api/products")
def products():
    return [product(row) for row in query("SELECT * FROM catalogue ORDER BY name")]

@app.post("/api/chat", response_model=ChatReply)
async def chat(request: ChatRequest):
    return await reply(request.message)

@app.get("/api/products/{product_id}")
def one_product(product_id: str):
    rows = query("SELECT * FROM catalogue WHERE product_id = ?", (product_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Product not found")
    return product(rows[0])
