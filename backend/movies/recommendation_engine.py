from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count
from .models import Movie, Review, UserPreference, MovieInteraction, Genre
from collections import defaultdict, Counter
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Moteur de recommandation pour les films"""
    
    def __init__(self, user):
        self.user = user
        self.user_reviews = Review.objects.filter(user=user)
        self.user_interactions = MovieInteraction.objects.filter(user=user)
        self.user_preferences = UserPreference.objects.filter(user=user).first()
    
    def get_user_favorite_genres(self):
        """Récupère les genres préférés de l'utilisateur"""
        favorite_genres = set()
        
        # Genres des films bien notés
        high_rated_movies = self.user_reviews.filter(rating__gte=4)
        for review in high_rated_movies:
            favorite_genres.update(review.movie.genres.all())
        
        # Genres des préférences utilisateur
        if self.user_preferences:
            favorite_genres.update(self.user_preferences.favorite_genres.all())
        
        return list(favorite_genres)
    
    def get_similar_users(self, limit=10):
        """Trouve des utilisateurs avec des goûts similaires"""
        # Utilisateurs qui ont noté les mêmes films
        user_movies = set(self.user_reviews.values_list('movie_id', flat=True))
        
        if not user_movies:
            return []
        
        # Trouve les utilisateurs qui ont noté les mêmes films
        similar_users = defaultdict(int)
        
        for movie_id in user_movies:
            other_reviews = Review.objects.filter(
                movie_id=movie_id
            ).exclude(user=self.user)
            
            for review in other_reviews:
                # Calcule la similarité basée sur les notes
                user_rating = self.user_reviews.filter(movie_id=movie_id).first().rating
                if abs(user_rating - review.rating) <= 1:  # Tolérance de 1 point
                    similar_users[review.user_id] += 1
        
        # Trie par similarité
        sorted_users = sorted(similar_users.items(), key=lambda x: x[1], reverse=True)
        
        return [User.objects.get(id=user_id) for user_id, _ in sorted_users[:limit]]
    
    def get_content_based_recommendations(self, limit=10):
        """Recommandations basées sur le contenu"""
        recommendations = []
        favorite_genres = self.get_user_favorite_genres()
        
        if not favorite_genres:
            return Movie.objects.filter(vote_average__gte=7.0).order_by('-popularity')[:limit]
        
        # Films des genres préférés non encore vus
        watched_movies = set(self.user_reviews.values_list('movie_id', flat=True))
        
        # Films populaires des genres préférés
        for genre in favorite_genres:
            movies = Movie.objects.filter(
                genres=genre
            ).exclude(
                id__in=watched_movies
            ).order_by('-vote_average', '-popularity')[:5]
            
            recommendations.extend(movies)
        
        # Supprime les doublons et limite
        seen = set()
        unique_recommendations = []
        
        for movie in recommendations:
            if movie.id not in seen:
                seen.add(movie.id)
                unique_recommendations.append(movie)
                if len(unique_recommendations) >= limit:
                    break
        
        return unique_recommendations
    
    def get_collaborative_recommendations(self, limit=10):
        """Recommandations collaboratives"""
        similar_users = self.get_similar_users()
        
        if not similar_users:
            return []
        
        # Films bien notés par des utilisateurs similaires
        watched_movies = set(self.user_reviews.values_list('movie_id', flat=True))
        recommendations = defaultdict(list)
        
        for similar_user in similar_users:
            high_rated_reviews = Review.objects.filter(
                user=similar_user,
                rating__gte=4
            ).exclude(movie_id__in=watched_movies)
            
            for review in high_rated_reviews:
                recommendations[review.movie].append(review.rating)
        
        # Calcule le score moyen pour chaque film
        scored_movies = []
        for movie, ratings in recommendations.items():
            avg_rating = sum(ratings) / len(ratings)
            scored_movies.append((movie, avg_rating, len(ratings)))
        
        # Trie par score moyen et nombre de votes
        scored_movies.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        return [movie for movie, _, _ in scored_movies[:limit]]
    
    def get_trending_recommendations(self, limit=10):
        """Recommandations basées sur les tendances"""
        # Films populaires récents
        recent_date = datetime.now().date() - timedelta(days=30)
        
        trending_movies = Movie.objects.filter(
            release_date__gte=recent_date
        ).order_by('-popularity', '-vote_average')[:limit]
        
        if trending_movies.count() < limit:
            # Complète avec des films populaires
            additional_movies = Movie.objects.exclude(
                id__in=[m.id for m in trending_movies]
            ).order_by('-popularity')[:limit - trending_movies.count()]
            
            trending_movies = list(trending_movies) + list(additional_movies)
        
        return trending_movies
    
    def get_hybrid_recommendations(self, limit=20):
        """Recommandations hybrides combinant plusieurs approches"""
        recommendations = []
        
        # 50% basé sur le contenu
        content_based = self.get_content_based_recommendations(limit // 2)
        recommendations.extend(content_based)
        
        # 30% collaboratif
        collaborative = self.get_collaborative_recommendations(limit // 3)
        recommendations.extend(collaborative)
        
        # 20% tendances
        trending = self.get_trending_recommendations(limit // 5)
        recommendations.extend(trending)
        
        # Supprime les doublons
        seen = set()
        unique_recommendations = []
        
        for movie in recommendations:
            if movie.id not in seen:
                seen.add(movie.id)
                unique_recommendations.append(movie)
                if len(unique_recommendations) >= limit:
                    break
        
        # Complète avec des films populaires si nécessaire
        if len(unique_recommendations) < limit:
            additional_movies = Movie.objects.exclude(
                id__in=[m.id for m in unique_recommendations]
            ).order_by('-vote_average', '-popularity')[:limit - len(unique_recommendations)]
            
            unique_recommendations.extend(additional_movies)
        
        return unique_recommendations[:limit]
    
    def get_genre_recommendations(self, genre_id, limit=10):
        """Recommandations pour un genre spécifique"""
        try:
            genre = Genre.objects.get(id=genre_id)
        except Genre.DoesNotExist:
            return []
        
        # Films non vus de ce genre
        watched_movies = set(self.user_reviews.values_list('movie_id', flat=True))
        
        movies = Movie.objects.filter(
            genres=genre
        ).exclude(
            id__in=watched_movies
        ).order_by('-vote_average', '-popularity')[:limit]
        
        return movies
    
    def get_similar_movies(self, movie_id, limit=10):
        """Trouve des films similaires à un film donné"""
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return []
        
        # Films du même genre
        similar_movies = Movie.objects.filter(
            genres__in=movie.genres.all()
        ).exclude(
            id=movie_id
        ).annotate(
            genre_count=Count('genres')
        ).order_by('-genre_count', '-vote_average')[:limit]
        
        return similar_movies


def get_recommendations_for_user(user, recommendation_type='hybrid', limit=20):
    """Fonction principale pour obtenir des recommandations"""
    engine = RecommendationEngine(user)
    
    if recommendation_type == 'content':
        return engine.get_content_based_recommendations(limit)
    elif recommendation_type == 'collaborative':
        return engine.get_collaborative_recommendations(limit)
    elif recommendation_type == 'trending':
        return engine.get_trending_recommendations(limit)
    elif recommendation_type == 'hybrid':
        return engine.get_hybrid_recommendations(limit)
    else:
        return engine.get_hybrid_recommendations(limit)


def get_popular_movies(limit=20):
    """Récupère les films populaires pour les utilisateurs non connectés"""
    return Movie.objects.filter(
        vote_average__gte=6.0
    ).order_by('-popularity', '-vote_average')[:limit]


def get_movies_by_genre(genre_id, limit=20):
    """Récupère les films d'un genre spécifique"""
    try:
        genre = Genre.objects.get(id=genre_id)
        return Movie.objects.filter(
            genres=genre
        ).order_by('-vote_average', '-popularity')[:limit]
    except Genre.DoesNotExist:
        return []


def record_interaction(user, movie, interaction_type):
    """Enregistre une interaction utilisateur"""
    if not user.is_authenticated:
        return
    
    MovieInteraction.objects.create(
        user=user,
        movie=movie,
        interaction_type=interaction_type
    )
