"""Notification microservice; it stores simulated notification events."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request


app = Flask(__name__)
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "/data/notifications.sqlite"))


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
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                delivery_status TEXT NOT NULL DEFAULT 'simulated',
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def notification_to_dict(row):
    return {
        "id": row["id"],
        "order_id": row["order_id"],
        "event_type": row["event_type"],
        "customer_email": row["customer_email"],
        "delivery_status": row["delivery_status"],
        "payload": json.loads(row["payload_json"]),
        "created_at": row["created_at"],
    }


@app.get("/")
def home():
    return jsonify(
        {
            "service": "notifications",
            "message": "Service notifications opérationnel.",
            "notifications_url": "/notifications",
        }
    )


@app.get("/health")
def health():
    with database() as connection:
        connection.execute("SELECT 1")
    return jsonify({"status": "ok", "service": "notifications"})


@app.post("/notify")
def create_notification():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps doit être un objet JSON."}), 400

    order_id = data.get("order_id")
    event_type = str(data.get("event_type", "")).strip()
    customer_email = str(data.get("customer_email", "")).strip()
    payload = data.get("payload", {})
    if type(order_id) is not int or order_id <= 0:
        return jsonify({"error": "order_id doit être un entier positif."}), 400
    if not event_type or "@" not in customer_email or not isinstance(payload, dict):
        return (
            jsonify(
                {
                    "error": (
                        "event_type, une adresse customer_email valide et un "
                        "payload objet sont obligatoires."
                    )
                }
            ),
            400,
        )

    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO notifications (
                order_id, event_type, customer_email, delivery_status, payload_json
            )
            VALUES (?, ?, ?, 'simulated', ?)
            """,
            (
                order_id,
                event_type,
                customer_email,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        row = connection.execute(
            "SELECT * FROM notifications WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    return (
        jsonify(
            {
                "notification": notification_to_dict(row),
                "message": (
                    "Événement enregistré. Aucun e-mail réel n'est envoyé "
                    "par ce prototype."
                ),
            }
        ),
        201,
    )


@app.get("/notifications")
def list_notifications():
    order_id = request.args.get("order_id", type=int)
    with database() as connection:
        if order_id is None:
            rows = connection.execute(
                "SELECT * FROM notifications ORDER BY id DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM notifications
                WHERE order_id = ?
                ORDER BY id DESC
                """,
                (order_id,),
            ).fetchall()
    return jsonify([notification_to_dict(row) for row in rows])


@app.get("/notifications/<int:notification_id>")
def get_notification(notification_id):
    with database() as connection:
        row = connection.execute(
            "SELECT * FROM notifications WHERE id = ?", (notification_id,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "Notification introuvable."}), 404
    return jsonify(notification_to_dict(row))


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003, debug=False)
