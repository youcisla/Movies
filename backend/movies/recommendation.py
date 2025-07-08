from .models import Review, Movie, Genre
from django.contrib.auth.models import User
from django.db.models import Avg, Count
import logging

logger = logging.getLogger(__name__)

def recommend_movies(user_id, limit=10):
    """
    Recommande des films basés sur les préférences utilisateur
    Algorithme simple basé sur les genres des films bien notés
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Récupérer les avis de l'utilisateur (note >= 4.0)
        user_reviews = Review.objects.filter(user=user, rating__gte=4.0)
        
        if not user_reviews.exists():
            # Si l'utilisateur n'a pas d'avis, recommander les films populaires
            return get_popular_movies(limit)
        
        # Identifier les genres préférés
        liked_genres = set()
        for review in user_reviews:
            movie_genres = review.movie.genres.all()
            for genre in movie_genres:
                liked_genres.add(genre)
        
        # Films déjà notés par l'utilisateur
        rated_movies = user_reviews.values_list('movie_id', flat=True)
        
        # Recommander des films des genres préférés non encore notés
        recommended_movies = []
        for genre in liked_genres:
            similar_movies = Movie.objects.filter(
                genres=genre
            ).exclude(
                id__in=rated_movies
            ).order_by('-vote_average', '-popularity')[:limit//len(liked_genres) + 1]
            
            recommended_movies.extend(similar_movies)
        
        # Retourner les films uniques triés par popularité
        unique_movies = list(set(recommended_movies))
        unique_movies.sort(key=lambda x: x.popularity, reverse=True)
        
        return unique_movies[:limit]
    
    except User.DoesNotExist:
        logger.error(f"Utilisateur {user_id} introuvable")
        return []
    except Exception as e:
        logger.error(f"Erreur lors de la recommandation: {e}")
        return []

def get_popular_movies(limit=10):
    """Retourne les films les plus populaires"""
    return Movie.objects.all().order_by('-popularity', '-vote_average')[:limit]

def get_movies_by_genre(genre_name, limit=20):
    """Retourne les films d'un genre spécifique"""
    try:
        genre = Genre.objects.get(name=genre_name)
        return Movie.objects.filter(genres=genre).order_by('-vote_average', '-popularity')[:limit]
    except Genre.DoesNotExist:
        return []

def get_similar_movies(movie_id, limit=6):
    """Retourne des films similaires basés sur les genres"""
    try:
        movie = Movie.objects.get(id=movie_id)
        movie_genres = movie.genres.all()
        
        if not movie_genres.exists():
            return []
        
        # Trouver des films avec des genres similaires
        similar_movies = Movie.objects.filter(
            genres__in=movie_genres
        ).exclude(
            id=movie_id
        ).distinct().order_by('-vote_average', '-popularity')[:limit]
        
        return similar_movies
    
    except Movie.DoesNotExist:
        return []

def get_user_stats(user):
    """Retourne les statistiques d'un utilisateur"""
    user_reviews = Review.objects.filter(user=user)
    return {
        'total_reviews': user_reviews.count(),
        'average_rating': user_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'favorite_genres': get_user_favorite_genres(user)
    }

def get_user_favorite_genres(user):
    """Retourne les genres favoris d'un utilisateur"""
    user_reviews = Review.objects.filter(user=user, rating__gte=4.0)
    genre_counts = {}
    
    for review in user_reviews:
        for genre in review.movie.genres.all():
            genre_counts[genre.name] = genre_counts.get(genre.name, 0) + 1
    
    # Trier par popularité
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    return [genre for genre, count in sorted_genres[:3]]  # Top 3 genres
