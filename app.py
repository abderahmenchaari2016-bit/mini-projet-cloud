from flask import Flask, jsonify

app = Flask(__name__)

# Example products for the Tunisian natural cosmetics shop.
products = [
    {
        "id": 1,
        "name": "Olive Oil Soap",
        "category": "Soap",
        "price_tnd": 8.5,
    },
    {
        "id": 2,
        "name": "Rosemary Essential Oil",
        "category": "Essential oil",
        "price_tnd": 18.0,
    },
    {
        "id": 3,
        "name": "Prickly Pear Seed Oil",
        "category": "Natural cosmetics",
        "price_tnd": 32.0,
    },
]


@app.get("/")
def home():
    """Return a short welcome message as JSON."""
    return jsonify({"message": "Welcome to the Natural Cosmetics API!"})


@app.get("/products")
def get_products():
    """Return the example product list as JSON."""
    return jsonify(products)


if __name__ == "__main__":
    # Listen on every network interface so Docker can forward port 8000.
    app.run(host="0.0.0.0", port=8000, debug=False)
