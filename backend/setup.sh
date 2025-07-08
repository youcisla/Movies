#!/bin/bash

# Script de démarrage rapide pour le système de recommandation de films

echo "🎬 Configuration du système de recommandation de films Django"
echo "============================================================"

# Vérification de Python
if ! command -v python &> /dev/null; then
    echo "❌ Python n'est pas installé. Veuillez installer Python 3.8+"
    exit 1
fi

echo "✅ Python détecté"

# Installation des dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements_simple.txt

# Configuration de l'environnement
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "⚠️  Veuillez configurer vos clés API dans le fichier .env"
fi

# Migration de la base de données
echo "🗄️  Configuration de la base de données..."
python manage.py makemigrations
python manage.py migrate

# Création du superutilisateur
echo "👤 Création du superutilisateur..."
echo "Veuillez entrer les informations pour le compte administrateur :"
python manage.py createsuperuser

# Collecte des fichiers statiques
echo "📂 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo ""
echo "🎉 Installation terminée !"
echo ""
echo "🚀 Pour démarrer le serveur :"
echo "   python manage.py runserver"
echo ""
echo "📊 Pour récupérer des films depuis TMDb :"
echo "   python manage.py fetch_movies"
echo ""
echo "🔗 Accès à l'application :"
echo "   - Site web : http://127.0.0.1:8000"
echo "   - Administration : http://127.0.0.1:8000/admin"
echo ""
echo "📋 N'oubliez pas de :"
echo "   1. Configurer votre clé API TMDb dans .env"
echo "   2. Configurer MongoDB si nécessaire"
echo "   3. Lancer 'python manage.py fetch_movies' pour récupérer des films"
echo ""
