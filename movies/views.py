import requests
from django.shortcuts import render

# Ta clé API TMDb
API_KEY = 'aa6299adee2926856b3fde9e3eae2aee'  # Remplace par ta clé API

def fetch_movies_from_tmdb():
    url = f'https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page=1'
    response = requests.get(url)
    data = response.json()

    movies = []  # Liste des films récupérés
    for movie in data['results']:
        movies.append({
            'title': movie['title'],
            'release_date': movie['release_date'],
            'overview': movie['overview'],
            'poster_path': f'https://image.tmdb.org/t/p/w500{movie["poster_path"]}',  # Construire l'URL de l'affiche
            'vote_average': movie['vote_average'],
            'vote_count': movie['vote_count']
        })

    return movies

def movie_list(request):
    movies = fetch_movies_from_tmdb()  # Appeler la fonction pour récupérer les films
    return render(request, 'movie_list.html', {'movies': movies})
