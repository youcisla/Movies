import requests
import time
from django.conf import settings
from django.core.cache import cache
from .models import Movie, Genre
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TMDbService:
    """Service pour interagir avec l'API TMDb"""
    
    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.image_base_url = settings.TMDB_SETTINGS.get('image_base_url', 'https://image.tmdb.org/t/p/w500')
        self.rate_limit = settings.TMDB_SETTINGS.get('rate_limit', 40)
        self.session = requests.Session()
        self.session.params.update({'api_key': self.api_key})
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
    
    def _rate_limit(self):
        """Implémente le rate limiting"""
        current_time = time.time()
        
        # Reset counter every 10 seconds
        if current_time - self.last_request_time > 10:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Wait if we've hit the rate limit
        if self.request_count >= self.rate_limit:
            sleep_time = 10 - (current_time - self.last_request_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.request_count = 0
            self.last_request_time = time.time()
        
        self.request_count += 1
    
    def _make_request(self, endpoint, params=None):
        """Effectue une requête vers l'API TMDb avec rate limiting"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête TMDb: {e}")
            return None
    
    def get_popular_movies(self, page=1):
        """Récupère les films populaires"""
        cache_key = f"tmdb_popular_movies_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = self._make_request('movie/popular', {'page': page})
        
        if data:
            cache.set(cache_key, data, 3600)  # Cache for 1 hour
        
        return data
    
    def get_movie_details(self, tmdb_id):
        """Récupère les détails d'un film"""
        cache_key = f"tmdb_movie_{tmdb_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = self._make_request(f'movie/{tmdb_id}')
        
        if data:
            cache.set(cache_key, data, 86400)  # Cache for 24 hours
        
        return data
    
    def search_movies(self, query, page=1):
        """Recherche des films"""
        cache_key = f"tmdb_search_{query}_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = self._make_request('search/movie', {
            'query': query,
            'page': page
        })
        
        if data:
            cache.set(cache_key, data, 1800)  # Cache for 30 minutes
        
        return data
    
    def get_genres(self):
        """Récupère la liste des genres"""
        cache_key = "tmdb_genres"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = self._make_request('genre/movie/list')
        
        if data:
            cache.set(cache_key, data, 86400)  # Cache for 24 hours
        
        return data
    
    def get_movies_by_genre(self, genre_id, page=1):
        """Récupère les films d'un genre spécifique"""
        cache_key = f"tmdb_genre_{genre_id}_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = self._make_request('discover/movie', {
            'with_genres': genre_id,
            'page': page,
            'sort_by': 'popularity.desc'
        })
        
        if data:
            cache.set(cache_key, data, 3600)  # Cache for 1 hour
        
        return data
    
    def save_movie_to_db(self, movie_data):
        """Sauvegarde un film dans la base de données"""
        try:
            # Parse release date
            release_date = None
            if movie_data.get('release_date'):
                try:
                    release_date = datetime.strptime(
                        movie_data['release_date'], '%Y-%m-%d'
                    ).date()
                except ValueError:
                    pass
            
            # Create or update movie
            movie, created = Movie.objects.update_or_create(
                tmdb_id=movie_data['id'],
                defaults={
                    'title': movie_data.get('title', ''),
                    'original_title': movie_data.get('original_title', ''),
                    'overview': movie_data.get('overview', ''),
                    'release_date': release_date,
                    'runtime': movie_data.get('runtime'),
                    'poster_path': movie_data.get('poster_path', ''),
                    'backdrop_path': movie_data.get('backdrop_path', ''),
                    'vote_average': movie_data.get('vote_average', 0.0),
                    'vote_count': movie_data.get('vote_count', 0),
                    'popularity': movie_data.get('popularity', 0.0),
                }
            )
            
            # Add genres
            if movie_data.get('genres'):
                for genre_data in movie_data['genres']:
                    genre, _ = Genre.objects.get_or_create(
                        tmdb_id=genre_data['id'],
                        defaults={'name': genre_data['name']}
                    )
                    movie.genres.add(genre)
            elif movie_data.get('genre_ids'):
                for genre_id in movie_data['genre_ids']:
                    try:
                        genre = Genre.objects.get(tmdb_id=genre_id)
                        movie.genres.add(genre)
                    except Genre.DoesNotExist:
                        pass
            
            return movie
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du film: {e}")
            return None
    
    def sync_genres(self):
        """Synchronise les genres avec TMDb"""
        data = self.get_genres()
        
        if not data or 'genres' not in data:
            return False
        
        for genre_data in data['genres']:
            Genre.objects.update_or_create(
                tmdb_id=genre_data['id'],
                defaults={'name': genre_data['name']}
            )
        
        return True
    
    def fetch_popular_movies(self, pages=5):
        """Récupère et sauvegarde les films populaires"""
        movies_saved = 0
        
        for page in range(1, pages + 1):
            data = self.get_popular_movies(page)
            
            if not data or 'results' not in data:
                continue
            
            for movie_data in data['results']:
                # Get detailed movie info
                detailed_movie = self.get_movie_details(movie_data['id'])
                
                if detailed_movie:
                    movie = self.save_movie_to_db(detailed_movie)
                    if movie:
                        movies_saved += 1
                        logger.info(f"Film sauvegardé: {movie.title}")
        
        return movies_saved


# Instance globale du service
tmdb_service = TMDbService()
