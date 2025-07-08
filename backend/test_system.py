#!/usr/bin/env python
"""
Script de test pour vérifier le bon fonctionnement du système de recommandation simple
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommender.settings_simple')

try:
    django.setup()
    print("✅ Django configuré avec succès")
except Exception as e:
    print(f"❌ Erreur de configuration Django: {e}")
    sys.exit(1)

# Importation des modèles
try:
    from movies.models_simple import Movie, Genre, Review
    from django.contrib.auth.models import User
    print("✅ Modèles importés avec succès")
except Exception as e:
    print(f"❌ Erreur d'importation des modèles: {e}")
    sys.exit(1)

def test_database_connection():
    """Test de la connexion à la base de données"""
    print("\n🔍 Test de la connexion à la base de données...")
    try:
        # Test de création d'un genre
        genre, created = Genre.objects.get_or_create(
            name="Test Genre",
            defaults={'tmdb_id': 999999}
        )
        print(f"✅ Genre créé/récupéré: {genre.name}")
        
        # Test de création d'un film
        movie, created = Movie.objects.get_or_create(
            title="Film de Test",
            defaults={
                'tmdb_id': 999999,
                'overview': "Ceci est un film de test",
                'vote_average': 8.5,
                'popularity': 100.0
            }
        )
        movie.genres.add(genre)
        print(f"✅ Film créé/récupéré: {movie.title}")
        
        # Nettoyage
        movie.delete()
        genre.delete()
        print("✅ Nettoyage effectué")
        
        return True
    except Exception as e:
        print(f"❌ Erreur de base de données: {e}")
        return False

def test_recommendation_engine():
    """Test du moteur de recommandation"""
    print("\n🤖 Test du moteur de recommandation...")
    try:
        from movies.recommendation import recommend_movies, get_popular_movies
        
        # Test des films populaires
        popular_movies = get_popular_movies(5)
        print(f"✅ Films populaires récupérés: {len(popular_movies)} films")
        
        # Test des recommandations (sans utilisateur)
        recommendations = recommend_movies(1, 5)  # ID utilisateur inexistant
        print(f"✅ Recommandations générées: {len(recommendations)} films")
        
        return True
    except Exception as e:
        print(f"❌ Erreur du moteur de recommandation: {e}")
        return False

def test_tmdb_command():
    """Test de la commande TMDb"""
    print("\n📡 Test de la commande TMDb...")
    try:
        from movies.management.commands.fetch_movies import fetch_movies
        print("✅ Commande TMDb importée avec succès")
        print("⚠️  Note: Pour tester complètement, configurez TMDB_API_KEY dans .env")
        return True
    except Exception as e:
        print(f"❌ Erreur de la commande TMDb: {e}")
        return False

def test_views():
    """Test des vues"""
    print("\n🌐 Test des vues...")
    try:
        from movies.views_simple import movie_list, movie_detail, movie_recommendations
        print("✅ Vues importées avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur des vues: {e}")
        return False

def test_urls():
    """Test des URLs"""
    print("\n🔗 Test des URLs...")
    try:
        from movies.urls_simple import urlpatterns
        print(f"✅ URLs importées: {len(urlpatterns)} patterns")
        return True
    except Exception as e:
        print(f"❌ Erreur des URLs: {e}")
        return False

def test_admin():
    """Test de l'administration"""
    print("\n⚙️ Test de l'administration...")
    try:
        from movies.admin_simple import MovieAdmin, GenreAdmin, ReviewAdmin
        print("✅ Configuration admin importée avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur de l'admin: {e}")
        return False

def run_all_tests():
    """Exécute tous les tests"""
    print("🧪 TESTS DU SYSTÈME DE RECOMMANDATION DJANGO")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_recommendation_engine,
        test_tmdb_command,
        test_views,
        test_urls,
        test_admin
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test.__name__}: {e}")
            failed += 1
    
    print(f"\n📊 RÉSULTATS DES TESTS")
    print("=" * 30)
    print(f"✅ Tests réussis: {passed}")
    print(f"❌ Tests échoués: {failed}")
    print(f"📈 Taux de réussite: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 Tous les tests sont passés ! Le système est prêt.")
        print("\n🚀 Prochaines étapes:")
        print("1. Configurez votre clé API TMDb dans .env")
        print("2. Lancez: python manage_simple.py runserver")
        print("3. Visitez: http://127.0.0.1:8000")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez la configuration.")

if __name__ == "__main__":
    run_all_tests()
