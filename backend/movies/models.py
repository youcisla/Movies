from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


class Genre(models.Model):
    """Model pour gérer les genres de films"""
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Movie(models.Model):
    """Model pour stocker les informations des films"""
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255, blank=True)
    overview = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    runtime = models.IntegerField(null=True, blank=True)  # en minutes
    
    # Informations TMDb
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    backdrop_path = models.CharField(max_length=255, blank=True, null=True)
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    popularity = models.FloatField(default=0.0)
    
    # Relations
    genres = models.ManyToManyField(Genre, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def release_year(self):
        return self.release_date.year if self.release_date else None
    
    @property
    def poster_url(self):
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None
    
    @property
    def backdrop_url(self):
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/w1280{self.backdrop_path}"
        return None
    
    @property
    def average_rating(self):
        reviews = self.review_set.all()
        if reviews.exists():
            return sum([review.rating for review in reviews]) / len(reviews)
        return 0
    
    def to_dict(self):
        """Convert movie to dictionary for MongoDB storage"""
        return {
            '_id': self.id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'original_title': self.original_title,
            'overview': self.overview,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'runtime': self.runtime,
            'poster_path': self.poster_path,
            'backdrop_path': self.backdrop_path,
            'vote_average': self.vote_average,
            'vote_count': self.vote_count,
            'popularity': self.popularity,
            'genres': [genre.name for genre in self.genres.all()],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    class Meta:
        ordering = ['-created_at']


class Review(models.Model):
    """Model pour les avis des utilisateurs sur les films"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'movie']
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.movie.title} ({self.rating}/5)'


class UserPreference(models.Model):
    """Model pour stocker les préférences des utilisateurs"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorite_genres = models.ManyToManyField(Genre, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Preferences for {self.user.username}'


class Watchlist(models.Model):
    """Model pour la liste de films à regarder"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
        ordering = ['-added_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.movie.title} (Watchlist)'


class MovieInteraction(models.Model):
    """Model pour tracker les interactions des utilisateurs avec les films"""
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('like', 'Like'),
        ('share', 'Share'),
        ('search', 'Search'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f'{self.user.username} {self.interaction_type} {self.movie.title}'


@receiver(post_save, sender=Movie)
def movie_post_save(sender, instance, **kwargs):
    """Sync movie to Neo4j when saved"""
    try:
        from movie_recommender.neo4j_connection import get_neo4j_connection

        # Sync to MongoDB - fix collection checking
        try:
            movies_collection = get_movies_collection()
            if movies_collection is not None:
                movies_collection.replace_one({'_id': instance.id}, instance.to_dict(), upsert=True)
        except Exception as mongo_e:
            logger.debug(f"MongoDB sync skipped: {mongo_e}")

        # Sync to Neo4j with complete movie data
        neo4j_conn = get_neo4j_connection()
        if neo4j_conn.is_connected:
            movie_data = {
                "overview": instance.overview,
                "release_date": instance.release_date.isoformat() if instance.release_date else "",
                "runtime": instance.runtime or 0,
                "poster_path": instance.poster_path,
                "backdrop_path": instance.backdrop_path,
                "vote_average": instance.vote_average,
                "vote_count": instance.vote_count,
                "popularity": instance.popularity,
                "tmdb_id": instance.tmdb_id
            }
            neo4j_conn.create_movie_node(
                instance.id, 
                instance.title, 
                [genre.name for genre in instance.genres.all()],
                movie_data
            )
    except Exception as e:
        logger.error(f"Error syncing movie to Neo4j: {e}")

@receiver(post_save, sender=Review)
def review_post_save(sender, instance, **kwargs):
    """Sync review to MongoDB when saved"""
    try:
        from .mongodb_sync import sync_review_to_mongodb
        sync_review_to_mongodb(instance)
    except ImportError:
        logger.debug("MongoDB sync not available")
    except Exception as e:
        logger.error(f"Error syncing review to MongoDB: {e}")

@receiver(post_save, sender=User)
def user_post_save(sender, instance, **kwargs):
    """Sync user to MongoDB when saved"""
    try:
        from .mongodb_sync import sync_user_to_mongodb
        sync_user_to_mongodb(instance)
    except ImportError:
        logger.debug("MongoDB sync not available")
    except Exception as e:
        logger.error(f"Error syncing user to MongoDB: {e}")
