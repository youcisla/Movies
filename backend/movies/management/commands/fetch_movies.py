from django.core.management.base import BaseCommand
from django.conf import settings
from movies.models import Movie, Genre
import requests
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Récupère les films populaires depuis TMDb API'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Début de la récupération des films...'))
        
        # Vérifier que la clé API est configurée
        api_key = getattr(settings, 'TMDB_API_KEY', '')
        if not api_key:
            self.stdout.write(self.style.ERROR('❌ Clé API TMDb manquante. Vérifiez votre fichier .env'))
            return
        
        self.stdout.write(f'✅ Clé API TMDb trouvée: {api_key[:8]}...')
        
        # Récupérer d'abord les genres
        self.fetch_genres(api_key)
        
        # Récupérer les films populaires
        self.fetch_movies(api_key)
        
        self.stdout.write(self.style.SUCCESS('🎉 Films récupérés avec succès'))

    def fetch_genres(self, api_key):
        """Récupère et sauvegarde les genres depuis TMDb"""
        self.stdout.write('📂 Récupération des genres...')
        url = 'https://api.themoviedb.org/3/genre/movie/list'
        params = {
            'api_key': api_key,
            'language': 'fr-FR'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            genres_added = 0
            for genre_data in data.get('genres', []):
                genre, created = Genre.objects.get_or_create(
                    tmdb_id=genre_data['id'],
                    defaults={'name': genre_data['name']}
                )
                if created:
                    genres_added += 1
                    self.stdout.write(f"  + Genre ajouté: {genre.name}")
                    
            self.stdout.write(f'✅ Genres traités: {genres_added} nouveaux, {len(data.get("genres", []))} total')
                    
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors de la récupération des genres: {e}'))

    def fetch_movies(self, api_key):
        """Récupère les films populaires depuis TMDb API"""
        self.stdout.write('🎬 Récupération des films populaires...')
        url = 'https://api.themoviedb.org/3/movie/popular'
        
        total_movies = 0
        new_movies = 0
        
        # Récupérer plusieurs pages pour avoir plus de films
        for page in range(1, 4):  # Pages 1 à 3 (60 films)
            params = {
                'api_key': api_key,
                'language': 'fr-FR',
                'page': page
            }
            
            try:
                self.stdout.write(f'  📄 Traitement de la page {page}...')
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                page_new_movies = 0
                for movie_data in data.get('results', []):
                    if self.save_movie(movie_data):
                        page_new_movies += 1
                    total_movies += 1
                
                new_movies += page_new_movies
                self.stdout.write(f'    ✅ Page {page}: {len(data.get("results", []))} films, {page_new_movies} nouveaux')
                    
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'❌ Erreur page {page}: {e}'))
                continue
        
        self.stdout.write(f'📊 Résumé: {total_movies} films traités, {new_movies} nouveaux films ajoutés')

    def save_movie(self, movie_data):
        """Sauvegarde un film dans la base de données"""
        try:
            # Vérifier si le film existe déjà
            movie, created = Movie.objects.get_or_create(
                tmdb_id=movie_data['id'],
                defaults={
                    'title': movie_data.get('title', ''),
                    'original_title': movie_data.get('original_title', ''),
                    'overview': movie_data.get('overview', ''),
                    'release_date': movie_data.get('release_date') or None,
                    'poster_path': movie_data.get('poster_path', ''),
                    'backdrop_path': movie_data.get('backdrop_path', ''),
                    'vote_average': movie_data.get('vote_average', 0.0),
                    'vote_count': movie_data.get('vote_count', 0),
                    'popularity': movie_data.get('popularity', 0.0),
                }
            )
            
            # Ajouter les genres
            if movie_data.get('genre_ids'):
                for genre_id in movie_data['genre_ids']:
                    try:
                        genre = Genre.objects.get(tmdb_id=genre_id)
                        movie.genres.add(genre)
                    except Genre.DoesNotExist:
                        # Le genre n'existe pas, l'ignorer
                        pass
            
            if created:
                self.stdout.write(f"    + Film ajouté: {movie.title}")
                return True
            else:
                # Mettre à jour les informations si nécessaire
                updated = False
                for field, value in {
                    'vote_average': movie_data.get('vote_average', 0.0),
                    'vote_count': movie_data.get('vote_count', 0),
                    'popularity': movie_data.get('popularity', 0.0),
                }.items():
                    if getattr(movie, field) != value:
                        setattr(movie, field, value)
                        updated = True
                
                if updated:
                    movie.save()
                
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur sauvegarde {movie_data.get("title", "Inconnu")}: {e}'))
            return False
