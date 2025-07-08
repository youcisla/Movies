#!/usr/bin/env python
"""
Script de test pour vérifier la clé API TMDb
"""

import requests
import json

# Votre clé API TMDb
API_KEY = "aa6299adee2926856b3fde9e3eae2aee"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhYTYyOTlhZGVlMjkyNjg1NmIzZmRlOWUzZWFlMmFlZSIsIm5iZiI6MTc1MTk4MjU5OC40MTQsInN1YiI6IjY4NmQyMjA2YjhlNjg5YTc1OTU0MDRmYSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.yABlbO8o6sU6edslFp1nUL1wpBJmCNkfpZNcgJ_Cs_0"

BASE_URL = "https://api.themoviedb.org/3"

def test_api_key():
    """Test de la clé API avec une requête simple"""
    print("🔑 Test de la clé API TMDb...")
    
    url = f"{BASE_URL}/authentication"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("✅ Clé API valide !")
            return True
        else:
            print(f"❌ Erreur de clé API: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_access_token():
    """Test du jeton d'accès avec les headers"""
    print("\n🎫 Test du jeton d'accès TMDb...")
    
    url = f"{BASE_URL}/account"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("✅ Jeton d'accès valide !")
            account_info = response.json()
            print(f"   Nom d'utilisateur: {account_info.get('username', 'N/A')}")
            print(f"   ID: {account_info.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ Erreur de jeton d'accès: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_popular_movies():
    """Test de récupération des films populaires"""
    print("\n🎬 Test de récupération des films populaires...")
    
    url = f"{BASE_URL}/movie/popular"
    params = {
        "api_key": API_KEY,
        "language": "fr-FR",
        "page": 1
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            movies = data.get('results', [])
            print(f"✅ {len(movies)} films récupérés avec succès !")
            
            # Afficher les 3 premiers films
            print("\n📽️ Premiers films récupérés:")
            for i, movie in enumerate(movies[:3], 1):
                title = movie.get('title', 'N/A')
                year = movie.get('release_date', 'N/A')[:4] if movie.get('release_date') else 'N/A'
                rating = movie.get('vote_average', 'N/A')
                print(f"   {i}. {title} ({year}) - Note: {rating}/10")
            
            return True
        else:
            print(f"❌ Erreur lors de la récupération: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_genres():
    """Test de récupération des genres"""
    print("\n🏷️ Test de récupération des genres...")
    
    url = f"{BASE_URL}/genre/movie/list"
    params = {
        "api_key": API_KEY,
        "language": "fr-FR"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            genres = data.get('genres', [])
            print(f"✅ {len(genres)} genres récupérés avec succès !")
            
            # Afficher les genres
            print("\n🎭 Genres disponibles:")
            for genre in genres[:10]:  # Afficher les 10 premiers
                print(f"   - {genre.get('name')} (ID: {genre.get('id')})")
            
            return True
        else:
            print(f"❌ Erreur lors de la récupération: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_movie_details():
    """Test de récupération des détails d'un film spécifique"""
    print("\n🎯 Test de récupération des détails d'un film...")
    
    # Film populaire : Avatar (2009) - ID: 19995
    movie_id = 19995
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": API_KEY,
        "language": "fr-FR"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            movie = response.json()
            print("✅ Détails du film récupérés avec succès !")
            
            print(f"\n🎬 Détails du film:")
            print(f"   Titre: {movie.get('title', 'N/A')}")
            print(f"   Titre original: {movie.get('original_title', 'N/A')}")
            print(f"   Année: {movie.get('release_date', 'N/A')}")
            print(f"   Durée: {movie.get('runtime', 'N/A')} minutes")
            print(f"   Note: {movie.get('vote_average', 'N/A')}/10")
            print(f"   Résumé: {movie.get('overview', 'N/A')[:100]}...")
            
            return True
        else:
            print(f"❌ Erreur lors de la récupération: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def main():
    """Exécute tous les tests"""
    print("🧪 TESTS DE L'API TMDb")
    print("=" * 40)
    
    tests = [
        ("Clé API", test_api_key),
        ("Jeton d'accès", test_access_token),
        ("Films populaires", test_popular_movies),
        ("Genres", test_genres),
        ("Détails de film", test_movie_details)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_name}: {e}")
            failed += 1
    
    print(f"\n📊 RÉSULTATS DES TESTS")
    print("=" * 30)
    print(f"✅ Tests réussis: {passed}")
    print(f"❌ Tests échoués: {failed}")
    print(f"📈 Taux de réussite: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 Tous les tests sont passés ! Votre API TMDb est prête.")
        print("\n🚀 Prochaines étapes:")
        print("1. Lancez: python manage_simple.py fetch_movies")
        print("2. Démarrez le serveur: python manage_simple.py runserver")
        print("3. Visitez: http://127.0.0.1:8000")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez votre configuration.")
    
    return failed == 0

if __name__ == "__main__":
    main()
