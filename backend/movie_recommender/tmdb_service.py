"""
TMDb API service for fetching movie data
"""

import requests
import time
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class TMDbService:
    """Service for interacting with The Movie Database API"""
    
    def __init__(self):
        self.api_key = settings.TMDB_SETTINGS['api_key']
        self.base_url = settings.TMDB_SETTINGS['base_url']
        self.image_base_url = settings.TMDB_SETTINGS['image_base_url']
        self.rate_limit = settings.TMDB_SETTINGS['rate_limit']
        self.session = requests.Session()
        
    def _make_request(self, endpoint, params=None):
        """Make a request to TMDb API with rate limiting"""
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        # Rate limiting
        time.sleep(1.0 / self.rate_limit)
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDb API request failed: {e}")
            return None
    
    def get_movie_details(self, movie_id):
        """Get detailed movie information"""
        cache_key = f"tmdb_movie_{movie_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        endpoint = f"movie/{movie_id}"
        params = {
            'append_to_response': 'credits,videos,reviews,similar,recommendations'
        }
        
        result = self._make_request(endpoint, params)
        
        if result:
            cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour
        
        return result
    
    def search_movies(self, query, page=1):
        """Search for movies"""
        endpoint = "search/movie"
        params = {
            'query': query,
            'page': page,
            'include_adult': False
        }
        
        return self._make_request(endpoint, params)
    
    def get_popular_movies(self, page=1):
        """Get popular movies"""
        cache_key = f"tmdb_popular_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        endpoint = "movie/popular"
        params = {'page': page}
        
        result = self._make_request(endpoint, params)
        
        if result:
            cache.set(cache_key, result, timeout=1800)  # Cache for 30 minutes
        
        return result
    
    def get_top_rated_movies(self, page=1):
        """Get top-rated movies"""
        cache_key = f"tmdb_top_rated_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        endpoint = "movie/top_rated"
        params = {'page': page}
        
        result = self._make_request(endpoint, params)
        
        if result:
            cache.set(cache_key, result, timeout=1800)  # Cache for 30 minutes
        
        return result
    
    def get_upcoming_movies(self, page=1):
        """Get upcoming movies"""
        cache_key = f"tmdb_upcoming_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        endpoint = "movie/upcoming"
        params = {'page': page}
        
        result = self._make_request(endpoint, params)
        
        if result:
            cache.set(cache_key, result, timeout=1800)  # Cache for 30 minutes
        
        return result
    
    def get_movie_genres(self):
        """Get all movie genres"""
        cache_key = "tmdb_genres"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        endpoint = "genre/movie/list"
        result = self._make_request(endpoint)
        
        if result:
            cache.set(cache_key, result, timeout=86400)  # Cache for 24 hours
        
        return result
    
    def get_person_details(self, person_id):
        """Get detailed person information"""
        cache_key = f"tmdb_person_{person_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        endpoint = f"person/{person_id}"
        params = {
            'append_to_response': 'movie_credits,tv_credits'
        }
        
        result = self._make_request(endpoint, params)
        
        if result:
            cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour
        
        return result
    
    def get_similar_movies(self, movie_id, page=1):
        """Get similar movies"""
        endpoint = f"movie/{movie_id}/similar"
        params = {'page': page}
        
        return self._make_request(endpoint, params)
    
    def get_movie_recommendations(self, movie_id, page=1):
        """Get movie recommendations"""
        endpoint = f"movie/{movie_id}/recommendations"
        params = {'page': page}
        
        return self._make_request(endpoint, params)
    
    def get_full_image_url(self, path, size='w500'):
        """Get full image URL"""
        if not path:
            return None
        return f"https://image.tmdb.org/t/p/{size}{path}"
    
    def discover_movies(self, **kwargs):
        """Discover movies with filters"""
        endpoint = "discover/movie"
        params = kwargs
        
        return self._make_request(endpoint, params)

# Global TMDb service instance
tmdb_service = TMDbService()
