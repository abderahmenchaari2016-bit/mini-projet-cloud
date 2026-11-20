"""Integration smoke test for the three-service Compose deployment."""

import argparse
import json
from pathlib import Path
import urllib.request


BASE = {
    "catalog": "http://127.0.0.1:8001",
    "orders": "http://127.0.0.1:8002",
    "notifications": "http://127.0.0.1:8003",
}


def request_json(url, method="GET", body=None):
    payload = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload else {}
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.status, json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="write the real API responses to a JSON file")
    args = parser.parse_args()
    evidence = {"health": {}, "catalog": [], "order": None, "notifications": []}

    for name, base in BASE.items():
        status, health = request_json(f"{base}/health")
        assert status == 200 and health["status"] == "ok", (name, health)
        evidence["health"][name] = health
        print(f"OK health {name}: {health['status']}")

    _, products = request_json(f"{BASE['catalog']}/products")
    assert products and products[0]["id"] > 0, "catalogue vide"
    evidence["catalog"] = products
    product = products[0]
    print(f"OK catalog: {len(products)} product(s), first_id={product['id']}")

    body = {
        "customer_name": "CI Demo",
        "customer_email": "ci-demo@example.test",
        "product_id": product["id"],
        "quantity": 2,
    }
    status, result = request_json(f"{BASE['orders']}/orders", "POST", body)
    assert status == 201 and result["notification_status"] == "recorded", result
    order = result["order"]
    evidence["order"] = result
    print(
        f"OK order #{order['id']}: {order['quantity']} item(s), "
        f"total={order['total_tnd']} TND"
    )

    _, notifications = request_json(
        f"{BASE['notifications']}/notifications?order_id={order['id']}"
    )
    assert notifications, "aucun événement reçu par le service notifications"
    assert notifications[0]["delivery_status"] == "simulated", notifications[0]
    evidence["notifications"] = notifications
    print(f"OK inter-service communication: notification #{notifications[0]['id']}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"API results saved to {args.output}")


if __name__ == "__main__":
    main()
