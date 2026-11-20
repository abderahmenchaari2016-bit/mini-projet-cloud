# Dossier de recommandation Cloud

**Projet :** Cloudifier une PME e-business avec une architecture microservices<br/>
**Contexte :** PME tunisienne de vente en ligne de produits artisanaux<br/>
**Formation :** 3e année E-business - Cloud Computing<br/>
**Version :** 1.0 - 20 novembre 2026<br/>
**Équipe :** noms à compléter

## Synthèse décisionnelle

Le site actuel dépend d'un serveur physique unique, d'une base MySQL locale et de sauvegardes manuelles. Cette organisation concentre les risques de panne et de perte de données, absorbe mal les pics et rend la supervision comme la croissance coûteuses en effort.

La recommandation est une migration progressive vers un **cloud public**, avec une application conteneurisée et des services managés. Le premier palier de production peut utiliser un service de conteneurs managé, une base relationnelle managée, une file de messages pour les événements asynchrones, un stockage objet, la gestion centralisée des secrets et des journaux, des sauvegardes testées et un point d'entrée HTTPS protégé. Cette recommandation privilégie la réduction de l'exploitation courante et l'élasticité, sous réserve de contrôler les coûts et de vérifier les exigences de localisation des données.

Le prototype livré est local : une API catalogue, une API commandes et une API notifications, chacune avec son propre Dockerfile, son API REST et son volume SQLite. Docker Compose relie les services sur un réseau privé. Le parcours de commande exerce la communication catalogue → commandes → notifications. Ce prototype démontre les concepts; il n'est pas un déploiement de production.

## 1. Diagnostic et besoins

### 1.1 État actuel

| Constat | Conséquence métier et technique | Réponse recommandée |
| --- | --- | --- |
| Serveur physique unique | Point de panne unique; reprise longue en cas d'incident | Répartir les composants et prévoir redémarrage, contrôles de santé et stratégie de reprise |
| MySQL local | Couplage au serveur; capacité et maintenance gérées manuellement | Migrer vers DBaaS avec sauvegardes automatiques et restauration vérifiée |
| Sauvegardes manuelles | Risque de sauvegarde absente, obsolète ou inutilisable | Politique planifiée, rétention définie et exercices réguliers de restauration |
| Pics difficiles à absorber | Lenteur ou indisponibilité pendant les campagnes et promotions | Mise à l'échelle des services stateless et mise en file des tâches irrégulières |
| Pas de supervision | Détection tardive des erreurs et de la saturation | Journaux centralisés, métriques, alarmes et tableaux de bord |
| Données clients peu exploitées | Décisions marketing et réassort peu informées | Entrepôt/BI séparé, consentement et minimisation des données |

### 1.2 Besoins

**Fonctionnels :** consulter et rechercher des produits; créer et suivre une commande; valider le produit et calculer le montant; notifier le client; administrer le catalogue; produire des indicateurs de vente et de demande.

**Non fonctionnels :** disponibilité supérieure au serveur unique; élasticité pendant les pointes; sauvegarde et restauration documentées; temps de réponse prévisible; chiffrement en transit et au repos; accès avec privilège minimal; traçabilité et alertes; déploiements reproductibles; coûts mesurables; protection des données et conformité à confirmer pour la juridiction concernée.

Les niveaux de service chiffrés, RPO/RTO, volumes, budget et exigences de résidence des données n'étant pas fournis, ils doivent être fixés pendant le cadrage avant tout engagement contractuel.

## 2. Modèle de déploiement

La terminologie des modèles cloud s'appuie sur la définition NIST : cloud public, privé, communautaire et hybride, ainsi que les modèles de services SaaS, PaaS et IaaS [1].

| Modèle | Atouts pour cette PME | Coûts / limites | Évaluation |
| --- | --- | --- | --- |
| Public | Provisionnement rapide, services managés, élasticité, paiement à l'usage | Gouvernance fournisseur, contrôle des coûts, configuration sécurité à maîtriser | **Recommandé** pour lancer et faire évoluer la boutique sans exploiter un datacenter |
| Privé | Contrôle et personnalisation élevés; environnement dédié | Investissement et exploitation plus lourds; l'élasticité dépend de la capacité achetée | Peu adapté à une PME sans contrainte de contrôle imposant un cloud dédié |
| Hybride | Garde certains systèmes en local et migre progressivement; peut répondre à des exigences de résidence | Connectivité, identité, supervision, sécurité et dépannage plus complexes | Option de transition si une contrainte réelle impose de conserver MySQL ou des données sur site |

**Décision :** choisir le cloud public avec une première région à sélectionner selon latence, disponibilité des services, coût et règles de données. Éviter de choisir une région sur une hypothèse non vérifiée. Maintenir les interfaces applicatives portables (conteneurs, API et automatisation) afin de limiter le couplage.

## 3. Modèles de service et besoins

| Modèle | Où il s'applique | Justification |
| --- | --- | --- |
| SaaS (Software as a Service) | Messagerie, collaboration, CRM, support client ou comptabilité | Remplace des outils génériques à exploiter soi-même; privilégier les services conformes aux besoins de confidentialité et d'export |
| PaaS (Platform as a Service) | Hébergement de l'API et pipeline de déploiement géré | Permet aux développeurs de livrer l'application sans maintenir les OS et serveurs; choix simple au démarrage |
| IaaS (Infrastructure as a Service) | Réseau virtuel, sous-réseaux, pare-feu et éventuellement VM de compatibilité | Offre plus de contrôle quand le PaaS ne suffit pas, avec davantage de tâches d'administration |
| FaaS (Function as a Service) | Traitements événementiels : génération de miniatures, tâches planifiées, traitement ponctuel de commande | Facturation à l'exécution et mise à l'échelle automatique; adapté aux traitements courts, avec limites de durée et de démarrage à vérifier |
| DBaaS (Database as a Service) | Base relationnelle de commandes, clients et catalogue | Le fournisseur gère une part importante des opérations de base, sauvegardes et maintenance; règles de rétention et restauration à configurer et tester [4] |
| BMaaS (Bare Metal as a Service) | Serveur physique dédié pour besoin matériel spécialisé, isolation ou conformité forte | Contrôle matériel accru, mais coût et responsabilité d'exploitation élevés; non retenu sans contrainte justifiant le matériel dédié |

Ces catégories sont utilisées comme grille de choix : NIST définit formellement SaaS, PaaS et IaaS; FaaS, DBaaS et BMaaS sont ici des catégories de services utilisées dans l'analyse du cours. La recommandation reste pragmatique : PaaS/conteneurs managés pour l'API, DBaaS pour les données transactionnelles, FaaS seulement pour les tâches événementielles appropriées.

## 4. Architecture Cloud cible proposée

```text
Clients web/mobile
       |
DNS + HTTPS / protection applicative
       |
Répartiteur de charge
       |
Conteneurs managés : catalogue | commandes | notifications
       |                         |
DBaaS relationnel          File de messages
       |                         |
Sauvegardes chiffrées       Travailleur notifications -> fournisseur e-mail

Tous composants : IAM à privilège minimal, secrets gérés, journaux/métriques/alertes,
stockage objet pour médias, règles de rétention et procédure de reprise.
```

Le choix de conteneurs managés comme Amazon ECS/Fargate est un exemple de réalisation, pas un fournisseur imposé : ECS permet d'exécuter et de faire évoluer des applications conteneurisées, et Fargate supprime la gestion des serveurs sous-jacents [3]. Une file de messages comme Amazon SQS peut découpler producteurs et consommateurs de microservices [5]. Les sauvegardes DBaaS doivent avoir une rétention adaptée et faire l'objet de restaurations d'essai [4]. Les contrôles de sécurité, fiabilité, opérations, performance, coûts et durabilité doivent être revus tout au long du cycle de vie [2].

Le stockage des médias et les analyses clients sont séparés du chemin de commande : cela évite qu'une tâche de reporting ou d'image ralentisse le paiement. Les notifications asynchrones sont recommandées en cible afin de ne pas faire dépendre la réponse de commande de la disponibilité de l'e-mail. Le prototype actuel utilise un appel REST direct pour rester lisible.

## 5. Prototype livré et preuves

| Service | API principale | Données | Conteneur |
| --- | --- | --- | --- |
| Catalogue | `GET /products`, `GET /products/{id}`, `POST /products` | SQLite dans `catalog_data` | Dockerfile dédié, port local 8001 |
| Commandes | `POST /orders`, `GET /orders` | SQLite dans `orders_data` | Dockerfile dédié, port local 8002 |
| Notifications | `POST /notify`, `GET /notifications` | SQLite dans `notifications_data` | Dockerfile dédié, port local 8003 |

Le fichier `docker-compose.yml` crée le réseau `cloud-network`, relie commandes au catalogue et aux notifications, configure les URL internes, les volumes nommés et les contrôles de santé. Les services s'exécutent en utilisateur non privilégié dans leurs images. Le total de commande est calculé avec le type Decimal.

Le contrôle de bout en bout vérifie la santé des trois APIs, lit le catalogue, crée une commande et confirme la réception d'un événement de notification. Il est disponible dans `scripts/smoke_test.py`; le workflow GitHub Actions est configuré pour le lancer à chaque push sur `main` et pour les pull requests. Les captures d'écran exigées par le cours doivent être prises sur l'ordinateur où Docker Desktop est ouvert; des sorties texte de vérification ne sont pas présentées comme des captures d'écran.

## 6. Sécurité, exploitation et feuille de route

1. **Avant la production :** remplacer les données de démonstration, ajouter authentification/autorisation, validation stricte, limitation de débit et gestion du consentement; stocker les secrets hors du dépôt; imposer HTTPS; définir les rôles et accès par service.
2. **Données :** migrer les fichiers SQLite de démonstration vers PostgreSQL managé, chiffrer les sauvegardes, définir la rétention, vérifier une restauration et documenter RPO/RTO. Appliquer les règles de conservation et de suppression des données personnelles.
3. **Fiabilité :** mettre les notifications dans une file avec reprises et file d'échec; rendre les commandes idempotentes; tester les pannes de dépendances; surveiller erreurs, latence, saturation et coûts.
4. **Mise en service progressive :** environnement de test, migration pilote, comparaison des résultats, bascule avec retour arrière, puis arrêt de l'ancien serveur après validation métier.
5. **Coûts :** établir un budget par environnement, alertes budgétaires et revue périodique; limiter les ressources non utilisées et choisir la redondance selon les objectifs de disponibilité.

Les notifications du prototype sont **simulées** et ne déclenchent aucun e-mail réel. Le prototype ne gère pas encore l'authentification, le paiement, le stock ou une base DBaaS. Aucune mise en production ni déploiement AWS n'a été effectué.

## Références

1. NIST, *The NIST Definition of Cloud Computing*, SP 800-145, https://csrc.nist.gov/pubs/sp/800/145/final
2. AWS, *AWS Well-Architected Framework*, https://docs.aws.amazon.com/wellarchitected/latest/framework/framework.html
3. AWS, *What is Amazon Elastic Container Service?*, https://docs.aws.amazon.com/AmazonECS/latest/developerguide/
4. AWS, *Backing up and restoring your Amazon RDS DB instance*, https://docs.aws.amazon.com/AmazonRDS/latest/gettingstartedguide/managing-backup-restore.html
5. AWS, *Amazon Simple Queue Service API Reference*, https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/
