"""Catalogue microservice for the natural cosmetics shop."""

from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request


app = Flask(__name__)
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "/data/catalog.sqlite"))

SEED_PRODUCTS = (
    (
        "Savon artisanal à l'huile d'olive",
        "Savons",
        "Savon naturel fabriqué en Tunisie.",
        "8.500",
    ),
    (
        "Huile essentielle de romarin",
        "Huiles essentielles",
        "Huile essentielle pour les soins et le bien-être.",
        "18.000",
    ),
    (
        "Huile de pépins de figue de barbarie",
        "Soins naturels",
        "Huile végétale artisanale pour le soin de la peau.",
        "32.000",
    ),
)


@contextmanager
def database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                price_tnd TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            connection.executemany(
                """
                INSERT OR IGNORE INTO products (name, category, description, price_tnd)
                VALUES (?, ?, ?, ?)
                """,
                SEED_PRODUCTS,
            )


def product_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "price_tnd": row["price_tnd"],
        "created_at": row["created_at"],
    }


def normalize_price(value):
    try:
        price = Decimal(str(value)).quantize(Decimal("0.001"))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not price.is_finite() or price <= 0:
        return None
    return format(price, ".3f")


@app.get("/")
def home():
    return jsonify(
        {
            "service": "catalog",
            "message": "Service catalogue opérationnel.",
            "products_url": "/products",
        }
    )


@app.get("/health")
def health():
    with database() as connection:
        connection.execute("SELECT 1")
    return jsonify({"status": "ok", "service": "catalog"})


@app.get("/products")
def list_products():
    query = request.args.get("q", "").strip()
    with database() as connection:
        if query:
            pattern = f"%{query}%"
            rows = connection.execute(
                """
                SELECT * FROM products
                WHERE name LIKE ? OR category LIKE ?
                ORDER BY id
                """,
                (pattern, pattern),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM products ORDER BY id"
            ).fetchall()
    return jsonify([product_to_dict(row) for row in rows])


@app.get("/products/<int:product_id>")
def get_product(product_id):
    with database() as connection:
        row = connection.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "Produit introuvable."}), 404
    return jsonify(product_to_dict(row))


@app.post("/products")
def create_product():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps doit être un objet JSON."}), 400

    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    description = str(data.get("description", "")).strip()
    price_tnd = normalize_price(data.get("price_tnd"))
    if not name or not category or price_tnd is None:
        return (
            jsonify(
                {
                    "error": (
                        "Les champs name, category et un price_tnd positif "
                        "sont obligatoires."
                    )
                }
            ),
            400,
        )

    try:
        with database() as connection:
            cursor = connection.execute(
                """
                INSERT INTO products (name, category, description, price_tnd)
                VALUES (?, ?, ?, ?)
                """,
                (name, category, description, price_tnd),
            )
            row = connection.execute(
                "SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Un produit porte déjà ce nom."}), 409

    return jsonify(product_to_dict(row)), 201


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)
