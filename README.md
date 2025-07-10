# DjangoBot - Système de Recommandation de Films

Un système de recommandation de films moderne et intelligent construit avec Django, intégrant plusieurs bases de données et des algorithmes de recommandation avancés.

## Fonctionnalités

### Fonctionnalités Principales
- **Intégration Base de Données Films**: Alimenté par l'API TMDb avec des informations complètes sur les films
- **Authentification Utilisateur**: Inscription, connexion et gestion complète des profils utilisateurs
- **Avis et Notes sur les Films**: Les utilisateurs peuvent noter et critiquer les films (1-5 étoiles)
- **Liste de Lecture Personnalisée**: Sauvegarder les films à regarder plus tard
- **Recommandations Avancées**: Système de recommandation hybride utilisant le filtrage collaboratif
- **Préférences Utilisateur**: Suivi des préférences basées sur les genres
- **Interactions Films**: Suivi des interactions utilisateur (vues, likes, partages, recherches)

### Fonctionnalités Techniques
- **Architecture Multi-Base de Données**: Django ORM + Neo4j
- **API RESTful**: Django REST Framework pour les endpoints API
- **Tâches d'Arrière-plan**: Celery pour le traitement asynchrone
- **Mise en Cache**: Redis/Base de données pour améliorer les performances
- **Analyses en Temps Réel**: Suivi du comportement utilisateur et analyses
- **Prêt pour la Production**: Configuré pour le déploiement avec des paramètres de sécurité appropriés

## Stack Technologique

### Backend
- **Framework**: Django 5.2+
- **Base de Données**: SQLite (développement) / PostgreSQL (production)
- **Base de Données Graphe**: Neo4j AuraDB pour les recommandations
- **Cache**: Redis / Cache base de données
- **File de Tâches**: Celery avec broker Redis/Base de données
- **API**: Django REST Framework

### Frontend
- **Styling**: Tailwind CSS
- **JavaScript**: Fonctionnalités ES6+ modernes
- **Composants UI**: Intégration Bootstrap

### Services Externes
- **Données Films**: API TMDb (The Movie Database)
- **Email**: Configuration SMTP pour les notifications

## Prérequis

Avant d'exécuter cette application, assurez-vous d'avoir :

- Python 3.8+
- Node.js et npm (pour les dépendances frontend)
- Compte Neo4j AuraDB (optionnel)
- Clé API TMDb
- Serveur Redis (optionnel, utilise la base de données par défaut)

## Installation

### 1. Cloner le Dépôt
```bash
git clone https://github.com/youcisla/movies.git
cd movies
```

### 2. Configuration du Backend
```bash
cd backend

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows:
venv\Scripts\activate
# Sur macOS/Linux:
source venv/bin/activate

# Installer les dépendances Python
pip install -r requirements.txt
```

### 3. Dépendances Frontend
```bash
# Depuis la racine du projet
npm install
```

### 4. Configuration de l'Environnement
Créer un fichier `.env` dans le répertoire `backend` :

```env
# Paramètres Django
SECRET_KEY=votre-clé-secrète-ici
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Configuration API TMDb
TMDB_API_KEY=votre-clé-api-tmdb
TMDB_ACCESS_TOKEN=votre-token-accès-tmdb
TMDB_BASE_URL=https://api.themoviedb.org/3

# URLs des Bases de Données (Optionnel)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=votre-mot-de-passe-neo4j
NEO4J_DATABASE=neo4j

# Configuration Redis (Optionnel)
REDIS_URL=redis://localhost:6379

# Configuration Email (Optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
```

### 5. Configuration de la Base de Données
```bash
cd backend

# Exécuter les migrations
python manage.py makemigrations
python manage.py migrate

# Créer la table de cache (si utilisation du cache base de données)
python manage.py createcachetable

# Créer un superutilisateur
python manage.py createsuperuser

# Charger les données d'exemple (optionnel)
python create_sample_data.py
```

## Exécution de l'Application

### Mode Développement

#### Option 1: Utilisation des Scripts de Configuration
```bash
# Sur Windows
cd backend
setup.bat

# Sur macOS/Linux
cd backend
chmod +x setup.sh
./setup.sh
```

#### Option 2: Démarrage Manuel
```bash
cd backend

# Démarrer le serveur de développement Django
python manage.py runserver

# Dans un autre terminal, démarrer le worker Celery (optionnel)
celery -A movie_recommender worker --loglevel=info
```

### Mode Production
```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Exécuter avec Gunicorn
gunicorn movie_recommender.wsgi:application --bind 0.0.0.0:8000
```

L'application sera disponible à `http://localhost:8000`

## Structure du Projet

```
DjangoBot/
├── backend/
│   ├── movie_recommender/          # Paramètres du projet Django
│   │   ├── settings.py            # Configuration principale
│   │   ├── urls.py                # Routage des URLs
│   │   └── wsgi.py                # Configuration WSGI
│   ├── movies/                    # Application de gestion des films
│   │   ├── models.py              # Modèles Movie, Review, Watchlist
│   │   ├── views.py               # Vues API et vues web
│   │   ├── urls.py                # URLs spécifiques aux films
│   │   └── recommendation_engine.py # Algorithmes de recommandation
│   ├── accounts/                  # Authentification utilisateur
│   ├── analytics/                 # Analyses comportement utilisateur
│   ├── recommendations/           # Système de recommandation
│   ├── dashboard_queries/         # Requêtes pour le tableau de bord
│   ├── templates/                 # Templates HTML
│   ├── static/                    # Fichiers statiques (CSS, JS, images)
│   └── requirements.txt           # Dépendances Python
├── package.json                   # Dépendances frontend
└── README.md                      # Ce fichier
```

## Modèles Principaux

### Modèle Movie
- Intégration TMDb pour les données des films
- Relations avec les genres
- Notes et avis des utilisateurs
- Fonctionnalité de liste de lecture

### Interactions Utilisateur
- Système d'avis avec notes de 1-5 étoiles
- Gestion de liste de lecture
- Suivi des préférences utilisateur
- Journalisation des interactions (vues, likes, partages)

### Moteur de Recommandation
- Filtrage collaboratif
- Filtrage basé sur le contenu
- Approche hybride combinant plusieurs algorithmes
- Intégration Neo4j pour les recommandations basées sur les graphes

## Endpoints API

### Authentification
- `POST /api/auth/login/` - Connexion utilisateur
- `POST /api/auth/register/` - Inscription utilisateur
- `POST /api/auth/logout/` - Déconnexion utilisateur

### Films
- `GET /api/movies/` - Lister les films avec pagination
- `GET /api/movies/{id}/` - Obtenir les détails d'un film
- `POST /api/movies/{id}/review/` - Ajouter/modifier un avis
- `POST /api/movies/{id}/watchlist/` - Ajouter à la liste de lecture

### Recommandations
- `GET /api/recommendations/` - Obtenir des recommandations personnalisées
- `GET /api/recommendations/popular/` - Obtenir les films populaires
- `GET /api/recommendations/similar/{id}/` - Obtenir des films similaires

### Profil Utilisateur
- `GET /api/profile/` - Obtenir le profil utilisateur et les statistiques
- `PUT /api/profile/` - Mettre à jour les préférences utilisateur

## Options de Configuration

### Configuration Base de Données
L'application prend en charge plusieurs backends de base de données :
- **SQLite**: Par défaut pour le développement
- **PostgreSQL**: Recommandé pour la production
- **Neo4j**: Pour les recommandations basées sur les graphes

### Stratégie de Mise en Cache
- **Redis**: Préféré pour la production
- **Base de données**: Option de secours
- **Gestion des sessions**: Backend configurable

### Tâches d'Arrière-plan
- **Celery**: Pour le traitement des recommandations
- **Redis/Base de données**: Configuration du broker
- **Surveillance des tâches**: Suivi des résultats intégré

## Fonctionnalités de Sécurité

- Protection CSRF
- Filtrage XSS
- Configuration d'en-têtes sécurisés
- Authentification et autorisation utilisateur
- Validation et assainissement des entrées
- Paramètres de sécurité de production

## Analyses et Surveillance

- Suivi des interactions utilisateur
- Métriques de popularité des films
- Surveillance de la précision des recommandations
- Journalisation des performances
- Suivi et rapport d'erreurs

## Déploiement

### Variables d'Environnement
Définir les variables d'environnement suivantes pour la production :
- `SECRET_KEY`: Clé secrète Django
- `DEBUG=False`: Désactiver le mode debug
- `ALLOWED_HOSTS`: Vos noms de domaine
- Chaînes de connexion base de données
- Clés API et identifiants

### Fichiers Statiques
L'application utilise WhiteNoise pour servir les fichiers statiques en production.

### Migrations Base de Données
Exécuter les migrations en production :
```bash
python manage.py migrate --no-input
python manage.py collectstatic --no-input
```

## Contribution

1. Forkez le dépôt
2. Créez une branche de fonctionnalité (`git checkout -b feature/fonctionnalité-incroyable`)
3. Effectuez vos modifications
4. Exécutez les tests (`python manage.py test`)
5. Commitez vos modifications (`git commit -m 'Ajouter une fonctionnalité incroyable'`)
6. Poussez vers la branche (`git push origin feature/fonctionnalité-incroyable`)
7. Ouvrez une Pull Request

## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Support

Si vous rencontrez des problèmes ou avez des questions :

1. Consultez la page [Issues](https://github.com/youcisla/movies/issues)
2. Créez un nouveau problème avec des informations détaillées
3. Rejoignez nos discussions communautaires

## Remerciements

- [TMDb](https://www.themoviedb.org/) pour les données de films
- [Django](https://www.djangoproject.com/) framework
- [Neo4j](https://neo4j.com/) pour la base de données graphe
- Tous les contributeurs et utilisateurs de ce projet
