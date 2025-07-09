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
    poster_path = models.CharField(max_length=255, blank=True)
    backdrop_path = models.CharField(max_length=255, blank=True)
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
    """Sync movie to MongoDB and Neo4j when saved"""
    try:
        from movie_recommender.mongodb_connection import get_movies_collection
        from movie_recommender.neo4j_connection import get_neo4j_connection

        # Sync to MongoDB
        movies_collection = get_movies_collection()
        if movies_collection:
            movies_collection.replace_one({'_id': instance.id}, instance.to_dict(), upsert=True)

        # Sync to Neo4j
        neo4j_conn = get_neo4j_connection()
        if neo4j_conn.is_connected:
            neo4j_conn.create_movie_node(instance.id, instance.title, [genre.name for genre in instance.genres.all()])
    except Exception as e:
        logger.error(f"Error syncing movie: {e}")

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
