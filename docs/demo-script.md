# Déroulé de démonstration (environ 6 minutes)

Le script suppose que Docker Desktop est démarré et que le dépôt est ouvert dans VS Code. Les services écoutent sur les ports 8001, 8002 et 8003.

## 0:00 - 0:45 | Présenter le besoin

Présenter la boutique tunisienne de produits artisanaux et le problème du serveur unique : disponibilité limitée, montée en charge difficile, sauvegardes manuelles et absence de supervision. Résumer la recommandation : cloud public pour démarrer, services conteneurisés, base managée et observabilité.

## 0:45 - 1:30 | Montrer le dépôt et l'architecture

Ouvrir le dépôt GitHub public `abderahmenchaari2016-bit/mini-projet-cloud`. Montrer les trois dossiers de service, les trois Dockerfiles, le fichier `docker-compose.yml` et le schéma `docs/architecture-prototype.svg`. Expliquer que le schéma décrit le prototype local, tandis que le rapport contient l'architecture cloud cible proposée.

## 1:30 - 2:15 | Vérifier Docker

Dans le terminal du projet, exécuter `docker --version`, puis `docker run --rm hello-world`. Montrer ensuite `docker compose ps` et expliquer que les trois services sont `healthy` sur 8001, 8002 et 8003.

## 2:15 - 3:00 | Tester le catalogue

Ouvrir `http://localhost:8001/health`, puis `http://localhost:8001/products`. Présenter les produits préchargés et expliquer que le service possède sa base SQLite dans le volume Docker `catalog_data`.

## 3:00 - 4:30 | Montrer une commande et la communication

Utiliser PowerShell pour envoyer une commande :

```powershell
$body = @{customer_name='Demo'; customer_email='demo@example.test'; product_id=1; quantity=2} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8002/orders -ContentType 'application/json' -Body $body
```

Expliquer que le service commandes demande le produit au catalogue, calcule le total, enregistre la commande puis transmet un événement au service notifications. Ouvrir `http://localhost:8003/notifications` pour montrer l'événement enregistré. Préciser qu'aucun vrai e-mail n'est envoyé.

## 4:30 - 5:15 | Montrer persistance et composition

Dans `docker-compose.yml`, montrer le réseau `cloud-network`, les variables d'URL entre services, les contrôles de santé et les volumes nommés. Exécuter `docker compose down`, puis `docker compose up -d` et montrer que les données persistent dans les volumes.

## 5:15 - 6:00 | Conclure avec le rapport et les limites

Présenter le rapport PDF, la comparaison public/privé/hybride et la correspondance SaaS/PaaS/IaaS/FaaS/DBaaS/BMaaS. Terminer par les étapes de production : remplacer SQLite par DBaaS, mettre les notifications en file d'attente, ajouter authentification, HTTPS, sauvegardes restaurées en test et alertes. Indiquer que le workflow GitHub Actions lance le test de bout en bout à chaque push et pull request.

## Commandes utiles

```powershell
docker compose up --build -d
docker compose ps
python scripts/smoke_test.py
docker compose logs --tail 50
```

Pour les captures demandées par le cours, enregistrer l'écran avec l'interface de capture de votre choix : Docker Desktop avec les trois conteneurs, le résultat de `docker run --rm hello-world`, `docker compose ps`, la page `/products`, puis la commande et la notification associée. La capture doit être faite sur le poste où Docker Desktop tourne.
