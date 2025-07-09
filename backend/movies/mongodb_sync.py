"""
MongoDB sync utilities for the Movie Recommendation System
"""
from movie_recommender.mongodb_connection import (
    get_movies_collection, 
    get_reviews_collection,
    get_users_collection,
    get_interactions_collection
)
from .models import Movie, Review, Genre
from django.contrib.auth.models import User
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def sync_movie_to_mongodb(movie):
    """
    Sync a Django Movie object to MongoDB
    """
    try:
        movies_collection = get_movies_collection()
        if movies_collection is None:
            logger.debug("MongoDB not available, skipping movie sync")
            return
        
        movie_doc = {
            '_id': movie.id,
            'tmdb_id': movie.tmdb_id,
            'title': movie.title,
            'original_title': movie.original_title,
            'overview': movie.overview,
            'release_date': movie.release_date.isoformat() if movie.release_date else None,
            'runtime': movie.runtime,
            'poster_path': movie.poster_path,
            'backdrop_path': movie.backdrop_path,
            'vote_average': movie.vote_average,
            'vote_count': movie.vote_count,
            'popularity': movie.popularity,
            'genres': [{'id': genre.id, 'name': genre.name} for genre in movie.genres.all()],
            'created_at': movie.created_at.isoformat() if movie.created_at else None,
            'updated_at': movie.updated_at.isoformat() if movie.updated_at else None,
            'synced_at': datetime.utcnow().isoformat()
        }
        
        movies_collection.replace_one(
            {'_id': movie.id},
            movie_doc,
            upsert=True
        )
        
        logger.debug(f"Movie {movie.title} synced to MongoDB")
        
    except Exception as e:
        logger.error(f"Error syncing movie to MongoDB: {e}")

def sync_review_to_mongodb(review):
    """
    Sync a Django Review object to MongoDB
    """
    try:
        reviews_collection = get_reviews_collection()
        if reviews_collection is None:
            logger.debug("MongoDB not available, skipping review sync")
            return
        
        review_doc = {
            '_id': review.id,
            'user_id': review.user.id,
            'username': review.user.username,
            'movie_id': review.movie.id,
            'movie_title': review.movie.title,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat() if review.created_at else None,
            'updated_at': review.updated_at.isoformat() if review.updated_at else None,
            'synced_at': datetime.utcnow().isoformat()
        }
        
        reviews_collection.replace_one(
            {'_id': review.id},
            review_doc,
            upsert=True
        )
        
        logger.debug(f"Review by {review.user.username} synced to MongoDB")
        
    except Exception as e:
        logger.error(f"Error syncing review to MongoDB: {e}")

def sync_user_to_mongodb(user):
    """
    Sync a Django User object to MongoDB
    """
    try:
        users_collection = get_users_collection()
        
        user_doc = {
            '_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            'synced_at': datetime.utcnow().isoformat()
        }
        
        users_collection.replace_one(
            {'_id': user.id},
            user_doc,
            upsert=True
        )
        
        logger.debug(f"User {user.username} synced to MongoDB")
        
    except Exception as e:
        logger.error(f"Error syncing user to MongoDB: {e}")

def sync_interaction_to_mongodb(user, movie, interaction_type):
    """
    Sync user interaction to MongoDB
    """
    try:
        interactions_collection = get_interactions_collection()
        
        interaction_doc = {
            'user_id': user.id,
            'username': user.username,
            'movie_id': movie.id,
            'movie_title': movie.title,
            'interaction_type': interaction_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        interactions_collection.insert_one(interaction_doc)
        
        logger.debug(f"Interaction {interaction_type} by {user.username} synced to MongoDB")
        
    except Exception as e:
        logger.error(f"Error syncing interaction to MongoDB: {e}")

def get_movie_analytics_from_mongodb():
    """
    Get movie analytics data from MongoDB
    """
    try:
        movies_collection = get_movies_collection()
        reviews_collection = get_reviews_collection()
        
        # Get top rated movies
        pipeline = [
            {
                '$lookup': {
                    'from': 'reviews',
                    'localField': '_id',
                    'foreignField': 'movie_id',
                    'as': 'reviews'
                }
            },
            {
                '$addFields': {
                    'avg_user_rating': {'$avg': '$reviews.rating'},
                    'review_count': {'$size': '$reviews'}
                }
            },
            {
                '$match': {
                    'review_count': {'$gte': 1}
                }
            },
            {
                '$sort': {
                    'avg_user_rating': -1,
                    'review_count': -1
                }
            },
            {
                '$limit': 20
            }
        ]
        
        top_movies = list(movies_collection.aggregate(pipeline))
        return top_movies
        
    except Exception as e:
        logger.error(f"Error getting analytics from MongoDB: {e}")
        return []
