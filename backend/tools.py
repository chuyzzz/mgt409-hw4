from pathlib import Path
import sqlite3
from models import ProductLookup, StockBySize

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"

def normalize_word(word: str) -> str:
    word = word.strip().lower().replace("grey", "gray")
    return "hoodie" if word == "hoodies" else word

def search_products(search: str, limit: int = 6) -> list[dict]:
    """Search the Campus Customs catalogue for products relevant to a shopper's request."""
    words = [normalize_word(word) for word in search.split() if len(word.strip()) > 2][:8]
    if not words:
        return []
    clauses = " AND ".join("lower(name || ' ' || garment_type || ' ' || description || ' ' || colors || ' ' || search_tags) LIKE ?" for _ in words)
    params = [f"%{word}%" for word in words]
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(f"SELECT product_id, name, price, description, colors, image_file_path FROM catalogue WHERE {clauses} ORDER BY name LIMIT ?", (*params, limit)).fetchall()
    return [{**dict(row), "image_url": f"/images/{Path(row['image_file_path']).name}"} for row in rows]

def catalogue_snapshot(limit: int = 12) -> list[dict]:
    """Return a small catalogue sample when a shopper asks what the shop carries."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT product_id, name, price, description, image_file_path FROM catalogue ORDER BY name LIMIT ?", (limit,)).fetchall()
    return [{**dict(row), "image_url": f"/images/{Path(row['image_file_path']).name}"} for row in rows]

def lookup_product(query: str) -> list[ProductLookup]:
    """Look up authoritative product descriptions and prices in the database."""
    words = [normalize_word(word) for word in query.split() if len(word.strip()) > 2][:8]
    if not words:
        return []
    clauses = " AND ".join("lower(product_id || ' ' || name || ' ' || description || ' ' || colors || ' ' || search_tags) LIKE ?" for _ in words)
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(f"SELECT product_id, name, description, price, colors, image_file_path FROM catalogue WHERE {clauses} ORDER BY name LIMIT 6", tuple(f"%{word}%" for word in words)).fetchall()
    return [ProductLookup(**{**dict(row), "image_url": f"/images/{Path(row['image_file_path']).name}"}) for row in rows]

def lookup_stock(product_id: str, size: str = "") -> list[StockBySize]:
    """Look up authoritative inventory quantities, optionally for one requested size."""
    sql = "SELECT size, quantity FROM inventory WHERE product_id = ?"
    params: tuple[str, ...] = (product_id,)
    if size.strip():
        sql += " AND lower(size) = lower(?)"
        params += (size.strip(),)
    sql += " ORDER BY size"
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(sql, params).fetchall()
    return [StockBySize(size=row[0], quantity=row[1]) for row in rows]
