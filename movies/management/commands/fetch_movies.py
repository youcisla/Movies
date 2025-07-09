import requests
from django.core.management.base import BaseCommand
from movies.models import Movie

API_KEY = 'aa6299adee2926856b3fde9e3eae2aee'  # Remplace avec ta clé API

def fetch_movies_from_tmdb():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()

    for movie in data['results']:
        Movie.objects.get_or_create(
            title=movie['title'],
            genre=movie['genre_ids'][0] if movie['genre_ids'] else 'Unknown',
            release_year=int(movie['release_date'][:4]),
            description=movie['overview']
        )

class Command(BaseCommand):
    help = 'Fetch popular movies from TMDb API'

    def handle(self, *args, **kwargs):
        fetch_movies_from_tmdb()
        self.stdout.write(self.style.SUCCESS('Successfully fetched movies'))
