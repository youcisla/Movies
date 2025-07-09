from django.core.management.base import BaseCommand
from movies.models import Movie
import requests

class Command(BaseCommand):
    help = "Importe les films populaires depuis TMDb (plusieurs pages) et les ajoute à la base Movie."

    def handle(self, *args, **options):
        API_KEY = "aa6299adee2926856b3fde9e3eae2aee"  # Remplace par ta clé si besoin
        total_count = 0
        for page in range(1, 11):  # Récupère les 10 premières pages (200 films)
            url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=fr-FR&page={page}"
            response = requests.get(url)
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Erreur TMDb page {page}: {response.status_code}"))
                break
            data = response.json()
            count = 0
            for movie_data in data.get("results", []):
                tmdb_id = movie_data.get("id")
                title = movie_data.get("title")
                original_title = movie_data.get("original_title", "")
                overview = movie_data.get("overview", "")
                release_date = movie_data.get("release_date") or None
                poster_path = movie_data.get("poster_path", "")
                backdrop_path = movie_data.get("backdrop_path", "")
                vote_average = movie_data.get("vote_average", 0.0)
                vote_count = movie_data.get("vote_count", 0)
                popularity = movie_data.get("popularity", 0.0)
                movie, created = Movie.objects.get_or_create(
                    tmdb_id=tmdb_id,
                    defaults={
                        "title": title,
                        "original_title": original_title,
                        "overview": overview,
                        "release_date": release_date,
                        "poster_path": poster_path,
                        "backdrop_path": backdrop_path,
                        "vote_average": vote_average,
                        "vote_count": vote_count,
                        "popularity": popularity,
                    }
                )
                if created:
                    count += 1
            total_count += count
            self.stdout.write(self.style.SUCCESS(f"{count} films importés depuis TMDb page {page}."))
        self.stdout.write(self.style.SUCCESS(f"Total: {total_count} films importés depuis TMDb."))
