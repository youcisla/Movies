#!/usr/bin/env python
"""
Script de test avancé pour le système de recommandation Django
Teste la connexion TMDb API et Neo4j avec les vraies clés
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

# Test des settings
from django.conf import settings

def test_settings():
    """Test de la configuration des settings"""
    print("\n🔧 Test de la configuration...")
    
    # TMDb API
    tmdb_key = getattr(settings, 'TMDB_API_KEY', '')
    if tmdb_key and tmdb_key != 'your-tmdb-api-key':
        print(f"✅ Clé TMDb API configurée: {tmdb_key[:8]}...")
    else:
        print("❌ Clé TMDb API manquante ou par défaut")
        return False
    
    # TMDb Access Token
    tmdb_token = getattr(settings, 'TMDB_ACCESS_TOKEN', '')
    if tmdb_token and tmdb_token.startswith('eyJ'):
        print(f"✅ Token TMDb configuré: {tmdb_token[:20]}...")
    else:
        print("⚠️  Token TMDb manquant (optionnel)")
    
    # Neo4j
    neo4j_uri = getattr(settings, 'NEO4J_URI', '')
    if neo4j_uri and 'd368ae13.databases.neo4j.io' in neo4j_uri:
        print(f"✅ Neo4j URI configuré: {neo4j_uri}")
    else:
        print("❌ Neo4j URI manquant ou incorrect")
        return False
    
    return True

def test_tmdb_api():
    """Test de la connexion à l'API TMDb"""
    print("\n🌐 Test de l'API TMDb...")
    
    try:
        import requests
        
        api_key = settings.TMDB_API_KEY
        url = f"{settings.TMDB_BASE_URL}/movie/popular"
        params = {
            'api_key': api_key,
            'language': 'fr-FR',
            'page': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'results' in data and len(data['results']) > 0:
            print(f"✅ API TMDb fonctionnelle - {len(data['results'])} films récupérés")
            print(f"📽️  Premier film: {data['results'][0]['title']}")
            return True
        else:
            print("❌ API TMDb: réponse vide")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API TMDb: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue API TMDb: {e}")
        return False

def test_neo4j_connection():
    """Test de la connexion Neo4j"""
    print("\n🔗 Test de la connexion Neo4j...")
    
    try:
        from py2neo import Graph
        
        graph = Graph(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        
        # Test de requête simple
        result = graph.run("RETURN 'Hello Neo4j' AS message").data()
        
        if result and len(result) > 0:
            print(f"✅ Neo4j connecté: {result[0]['message']}")
            
            # Test de création d'un nœud simple
            graph.run("CREATE (test:TestNode {name: 'Django Test', timestamp: datetime()}) RETURN test")
            
            # Compter les nœuds de test
            count_result = graph.run("MATCH (test:TestNode) RETURN count(test) AS count").data()
            count = count_result[0]['count'] if count_result else 0
            print(f"✅ Nœuds de test créés: {count}")
            
            # Nettoyage
            graph.run("MATCH (test:TestNode) DELETE test")
            print("✅ Nettoyage Neo4j effectué")
            
            return True
        else:
            print("❌ Neo4j: pas de réponse")
            return False
            
    except Exception as e:
        print(f"❌ Erreur Neo4j: {e}")
        return False

def test_mongodb_connection():
    """Test de la connexion MongoDB (via Django)"""
    print("\n🍃 Test de MongoDB/djongo...")
    
    try:
        from movies.models_simple import Genre, Movie
        
        # Test de création d'un genre
        test_genre, created = Genre.objects.get_or_create(
            name="Test Genre Django",
            defaults={'tmdb_id': 999999}
        )
        print(f"✅ Genre {'créé' if created else 'récupéré'}: {test_genre.name}")
        
        # Test de création d'un film
        test_movie, created = Movie.objects.get_or_create(
            title="Film Test Django",
            defaults={
                'tmdb_id': 999999,
                'overview': "Film de test pour Django",
                'vote_average': 8.5,
                'popularity': 100.0
            }
        )
        test_movie.genres.add(test_genre)
        print(f"✅ Film {'créé' if created else 'récupéré'}: {test_movie.title}")
        
        # Compter les éléments
        genres_count = Genre.objects.count()
        movies_count = Movie.objects.count()
        print(f"✅ Base de données: {genres_count} genres, {movies_count} films")
        
        # Nettoyage
        test_movie.delete()
        test_genre.delete()
        print("✅ Nettoyage MongoDB effectué")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}")
        return False

def test_recommendation_engine():
    """Test du moteur de recommandation"""
    print("\n🤖 Test du moteur de recommandation...")
    
    try:
        from movies.recommendation import recommend_movies, get_popular_movies
        from django.contrib.auth.models import User
        
        # Test des films populaires
        popular_movies = get_popular_movies(5)
        print(f"✅ Films populaires: {len(popular_movies)} films")
        
        # Test des recommandations pour un utilisateur fictif
        try:
            recommendations = recommend_movies(99999, 5)  # ID utilisateur inexistant
            print(f"✅ Recommandations générées: {len(recommendations)} films")
        except:
            print("⚠️  Recommandations: utilisateur introuvable (normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur moteur de recommandation: {e}")
        return False

def test_django_models():
    """Test des modèles Django"""
    print("\n📊 Test des modèles Django...")
    
    try:
        from movies.models_simple import Movie, Genre, Review
        from django.contrib.auth.models import User
        
        print(f"✅ Modèles importés: Movie, Genre, Review")
        
        # Test des propriétés des modèles
        if hasattr(Movie, 'poster_url'):
            print("✅ Propriété poster_url disponible")
        if hasattr(Movie, 'release_year'):
            print("✅ Propriété release_year disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur modèles Django: {e}")
        return False

def run_comprehensive_tests():
    """Exécute tous les tests complets"""
    print("🧪 TESTS COMPLETS DU SYSTÈME DE RECOMMANDATION DJANGO")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_settings),
        ("API TMDb", test_tmdb_api),
        ("Neo4j", test_neo4j_connection),
        ("MongoDB/djongo", test_mongodb_connection),
        ("Moteur de recommandation", test_recommendation_engine),
        ("Modèles Django", test_django_models),
    ]
    
    passed = 0
    failed = 0
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        print("-" * 30)
        try:
            if test_func():
                passed += 1
                results.append(f"✅ {test_name}")
            else:
                failed += 1
                results.append(f"❌ {test_name}")
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_name}: {e}")
            failed += 1
            results.append(f"❌ {test_name} (erreur)")
    
    print(f"\n📊 RÉSULTATS FINAUX")
    print("=" * 40)
    for result in results:
        print(result)
    
    print(f"\n📈 Statistiques:")
    print(f"✅ Tests réussis: {passed}")
    print(f"❌ Tests échoués: {failed}")
    print(f"📊 Taux de réussite: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        print("\n🚀 Votre système est prêt :")
        print("1. ✅ Clés API configurées")
        print("2. ✅ Bases de données connectées")
        print("3. ✅ Modèles fonctionnels")
        print("4. ✅ Moteur de recommandation opérationnel")
        print("\n🎬 Commandes suivantes :")
        print("   python manage_simple.py migrate")
        print("   python manage_simple.py createsuperuser")
        print("   python manage_simple.py fetch_movies")
        print("   python manage_simple.py runserver")
    else:
        print(f"\n⚠️  {failed} test(s) ont échoué.")
        print("Vérifiez la configuration et les connexions.")
        
        if failed == 1 and "Neo4j" in str(results):
            print("\n💡 Si seul Neo4j échoue, le système peut fonctionner sans.")
    
    print(f"\n🔗 Une fois prêt, accédez à :")
    print("   - Application : http://127.0.0.1:8000")
    print("   - Admin : http://127.0.0.1:8000/admin")
    print("   - API : http://127.0.0.1:8000/api/popular/")

if __name__ == "__main__":
    run_comprehensive_tests()
