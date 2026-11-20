"""Order microservice; it checks products and records order events."""

from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import sqlite3

import requests
from flask import Flask, jsonify, request


app = Flask(__name__)
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "/data/orders.sqlite"))
CATALOG_SERVICE_URL = os.getenv(
    "CATALOG_SERVICE_URL", "http://catalog:8001"
).rstrip("/")
NOTIFICATIONS_SERVICE_URL = os.getenv(
    "NOTIFICATIONS_SERVICE_URL", "http://notifications:8003"
).rstrip("/")


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
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price_tnd TEXT NOT NULL,
                total_tnd TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def order_to_dict(row):
    return {
        "id": row["id"],
        "customer_name": row["customer_name"],
        "customer_email": row["customer_email"],
        "product_id": row["product_id"],
        "product_name": row["product_name"],
        "quantity": row["quantity"],
        "unit_price_tnd": row["unit_price_tnd"],
        "total_tnd": row["total_tnd"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


@app.get("/")
def home():
    return jsonify(
        {
            "service": "orders",
            "message": "Service commandes opérationnel.",
            "orders_url": "/orders",
        }
    )


@app.get("/health")
def health():
    with database() as connection:
        connection.execute("SELECT 1")
    return jsonify({"status": "ok", "service": "orders"})


@app.get("/orders")
def list_orders():
    with database() as connection:
        rows = connection.execute(
            "SELECT * FROM orders ORDER BY id DESC"
        ).fetchall()
    return jsonify([order_to_dict(row) for row in rows])


@app.get("/orders/<int:order_id>")
def get_order(order_id):
    with database() as connection:
        row = connection.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "Commande introuvable."}), 404
    return jsonify(order_to_dict(row))


@app.post("/orders")
def create_order():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps doit être un objet JSON."}), 400

    customer_name = str(data.get("customer_name", "")).strip()
    customer_email = str(data.get("customer_email", "")).strip()
    product_id = data.get("product_id")
    quantity = data.get("quantity")

    if not customer_name or "@" not in customer_email:
        return (
            jsonify(
                {
                    "error": (
                        "customer_name et une adresse customer_email valide "
                        "sont obligatoires."
                    )
                }
            ),
            400,
        )
    if type(product_id) is not int or product_id <= 0:
        return jsonify({"error": "product_id doit être un entier positif."}), 400
    if type(quantity) is not int or quantity <= 0:
        return jsonify({"error": "quantity doit être un entier positif."}), 400

    try:
        catalog_response = requests.get(
            f"{CATALOG_SERVICE_URL}/products/{product_id}", timeout=5
        )
    except requests.RequestException:
        return (
            jsonify(
                {
                    "error": "Le service catalogue est momentanément indisponible."
                }
            ),
            503,
        )

    if catalog_response.status_code == 404:
        return jsonify({"error": "Le produit demandé n'existe pas."}), 404
    if catalog_response.status_code != 200:
        return jsonify({"error": "Réponse invalide du service catalogue."}), 502

    try:
        product = catalog_response.json()
    except ValueError:
        return jsonify({"error": "Le catalogue a renvoyé une réponse invalide."}), 502
    if not isinstance(product, dict):
        return jsonify({"error": "Le catalogue a renvoyé une réponse invalide."}), 502
    try:
        unit_price = Decimal(str(product["price_tnd"]))
        total = (unit_price * quantity).quantize(Decimal("0.001"))
    except (KeyError, InvalidOperation, TypeError, ValueError):
        return jsonify({"error": "Le prix reçu du catalogue est invalide."}), 502
    if not unit_price.is_finite() or unit_price <= 0:
        return jsonify({"error": "Le prix reçu du catalogue est invalide."}), 502

    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO orders (
                customer_name, customer_email, product_id, product_name,
                quantity, unit_price_tnd, total_tnd, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'created')
            """,
            (
                customer_name,
                customer_email,
                product_id,
                str(product.get("name", "Produit")),
                quantity,
                format(unit_price, ".3f"),
                format(total, ".3f"),
            ),
        )
        row = connection.execute(
            "SELECT * FROM orders WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    order = order_to_dict(row)
    notification_payload = {
        "event_type": "order_created",
        "order_id": order["id"],
        "customer_email": customer_email,
        "payload": {
            "customer_name": customer_name,
            "product_id": product_id,
            "product_name": order["product_name"],
            "quantity": quantity,
            "total_tnd": order["total_tnd"],
        },
    }
    try:
        notification_response = requests.post(
            f"{NOTIFICATIONS_SERVICE_URL}/notify",
            json=notification_payload,
            timeout=5,
        )
        notification_status = (
            "recorded" if notification_response.status_code == 201 else "unavailable"
        )
    except requests.RequestException:
        notification_status = "unavailable"

    return (
        jsonify(
            {
                "order": order,
                "notification_status": notification_status,
                "message": (
                    "La commande est enregistrée. La notification est simulée."
                    if notification_status == "recorded"
                    else (
                        "La commande est enregistrée, mais le service de "
                        "notifications est indisponible."
                    )
                ),
            }
        ),
        201,
    )


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, debug=False)
