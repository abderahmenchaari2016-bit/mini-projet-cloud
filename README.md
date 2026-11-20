# Prototype cloud pour une boutique artisanale

Ce dépôt conserve une petite API Flask autonome pour la partie 3 du sujet et ajoute un prototype microservices pour la partie 4. Le prototype utilise trois services REST indépendants : catalogue, commandes et notifications.

## Architecture actuelle

| Service | Port local | Responsabilité | Persistance |
| --- | ---: | --- | --- |
| Catalogue | 8001 | Lister, rechercher, consulter et ajouter des produits | Volume SQLite catalog_data |
| Commandes | 8002 | Créer et consulter les commandes | Volume SQLite orders_data |
| Notifications | 8003 | Enregistrer les événements de notification | Volume SQLite notifications_data |

Les conteneurs communiquent sur le réseau Docker cloud-network. Lorsqu'une commande est créée, le service commandes vérifie le produit auprès du catalogue, enregistre la commande, puis transmet un événement au service notifications. Ce dernier conserve l'événement pour la démonstration ; il n'envoie pas encore de véritable e-mail.

Chaque service possède son propre code, son Dockerfile et sa base SQLite. Les volumes Docker conservent les données quand les conteneurs sont arrêtés.

## Schéma d'architecture

~~~mermaid
flowchart LR
    client[Client REST]

    subgraph docker[Docker Compose - cloud-network]
        catalog[Catalogue API :8001]
        orders[Commandes API :8002]
        notifications[Notifications API :8003]
        catalog_db[(Volume catalog_data)]
        orders_db[(Volume orders_data)]
        notifications_db[(Volume notifications_data)]

        catalog --> catalog_db
        orders --> orders_db
        notifications --> notifications_db
        orders -->|GET product| catalog
        orders -->|POST notification event| notifications
    end

    client -->|REST :8001| catalog
    client -->|REST :8002| orders
    client -->|REST :8003| notifications
~~~

## Démarrer les microservices

Dans un terminal Ubuntu/WSL ouvert à la racine du projet :

    docker compose up --build -d
    docker compose ps

Les services sont accessibles sur http://localhost:8001, http://localhost:8002 et http://localhost:8003.

Pour suivre les journaux :

    docker compose logs -f

Pour arrêter les conteneurs en conservant les bases :

    docker compose down

## Parcours de démonstration

Afficher les produits du catalogue :

    curl http://localhost:8001/products

Créer une commande. L'identifiant produit 1 correspond au savon déjà présent dans le catalogue :

    curl -X POST http://localhost:8002/orders \
      -H 'Content-Type: application/json' \
      -d '{"customer_name":"Client démo","customer_email":"demo@example.com","product_id":1,"quantity":2}'

Consulter les commandes et l'événement créé par la commande :

    curl http://localhost:8002/orders
    curl http://localhost:8003/notifications

Vérifier la disponibilité de chaque service :

    curl http://localhost:8001/health
    curl http://localhost:8002/health
    curl http://localhost:8003/health

## Routes REST

### Catalogue

| Méthode | Route | Usage |
| --- | --- | --- |
| GET | /health | Vérifier le service et sa base |
| GET | /products | Lister les produits |
| GET | /products?q=savon | Rechercher par nom ou catégorie |
| GET | /products/{id} | Consulter un produit |
| POST | /products | Ajouter un produit |

Exemple de corps pour POST /products :

    {
      "name": "Crème naturelle",
      "category": "Soins naturels",
      "description": "Crème artisanale.",
      "price_tnd": "25.000"
    }

### Commandes

| Méthode | Route | Usage |
| --- | --- | --- |
| GET | /health | Vérifier le service et sa base |
| GET | /orders | Lister les commandes |
| GET | /orders/{id} | Consulter une commande |
| POST | /orders | Vérifier le produit, enregistrer la commande et demander une notification |

Exemple de corps pour POST /orders :

    {
      "customer_name": "Client démo",
      "customer_email": "demo@example.com",
      "product_id": 1,
      "quantity": 2
    }

### Notifications

| Méthode | Route | Usage |
| --- | --- | --- |
| GET | /health | Vérifier le service et sa base |
| POST | /notify | Enregistrer un événement de notification |
| GET | /notifications | Lister les événements |
| GET | /notifications?order_id=1 | Filtrer par commande |
| GET | /notifications/{id} | Consulter un événement |

## API Flask autonome de la partie 3

Les fichiers app.py, requirements.txt et Dockerfile à la racine restent disponibles pour la première API du projet :

    docker build -t cosmetics-api .
    docker run --rm -p 8000:8000 cosmetics-api

Puis ouvrir http://localhost:8000/ ou http://localhost:8000/products.

## Limites du prototype

- Les notifications sont enregistrées mais aucun e-mail n'est envoyé.
- L'API ne gère pas encore l'authentification, le paiement ni le stock.
- Les bases SQLite par service conviennent à la démonstration locale ; une base managée pourra être comparée dans le rapport d'architecture.
- Le prototype n'est pas destiné à être exposé directement sur Internet.
