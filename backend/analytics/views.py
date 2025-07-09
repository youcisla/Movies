from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.contrib.auth.decorators import login_required
from movies.models import Movie, Review, Genre, MovieInteraction
from django.contrib.auth.models import User


def analytics_dashboard(request):
    """Analytics dashboard with basic stats"""
    total_movies = Movie.objects.count()
    total_reviews = Review.objects.count()
    total_users = User.objects.count()
    avg_rating = Review.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    
    return JsonResponse({
        'total_movies': total_movies,
        'total_reviews': total_reviews,
        'total_users': total_users,
        'average_rating': round(avg_rating, 2),
    })


def movie_popularity(request):
    """Get movie popularity statistics"""
    popular_movies = Movie.objects.order_by('-popularity')[:10]
    
    return JsonResponse({
        'popular_movies': [
            {
                'id': movie.id,
                'title': movie.title,
                'popularity': movie.popularity,
                'vote_average': movie.vote_average,
                'vote_count': movie.vote_count,
            }
            for movie in popular_movies
        ]
    })


def ratings_analytics(request):
    """Get ratings analytics"""
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[str(i)] = Review.objects.filter(rating=i).count()
    
    # Top rated movies
    top_rated = Movie.objects.annotate(
        avg_rating=Avg('review__rating'),
        review_count=Count('review')
    ).filter(review_count__gte=5).order_by('-avg_rating')[:10]
    
    return JsonResponse({
        'rating_distribution': rating_distribution,
        'top_rated_movies': [
            {
                'id': movie.id,
                'title': movie.title,
                'avg_rating': round(movie.avg_rating, 2),
                'review_count': movie.review_count,
            }
            for movie in top_rated if movie.avg_rating
        ]
    })


@login_required
def user_statistics(request):
    """Get user statistics"""
    user = request.user
    user_reviews = Review.objects.filter(user=user)
    user_interactions = MovieInteraction.objects.filter(user=user)
    
    # User's favorite genres
    favorite_genres = {}
    for review in user_reviews.filter(rating__gte=4):
        for genre in review.movie.genres.all():
            favorite_genres[genre.name] = favorite_genres.get(genre.name, 0) + 1
    
    return JsonResponse({
        'user_id': user.id,
        'username': user.username,
        'total_reviews': user_reviews.count(),
        'avg_rating': user_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'total_interactions': user_interactions.count(),
        'favorite_genres': dict(sorted(favorite_genres.items(), key=lambda x: x[1], reverse=True)[:5])
    })


def genre_trends(request):
    """Get genre popularity trends"""
    genre_stats = []
    
    for genre in Genre.objects.all():
        movie_count = genre.movie_set.count()
        avg_rating = Review.objects.filter(
            movie__genres=genre
        ).aggregate(Avg('rating'))['rating__avg'] or 0
        
        genre_stats.append({
            'id': genre.id,
            'name': genre.name,
            'movie_count': movie_count,
            'avg_rating': round(avg_rating, 2),
        })
    
    # Sort by movie count
    genre_stats.sort(key=lambda x: x['movie_count'], reverse=True)
    
    return JsonResponse({
        'genre_trends': genre_stats
    })
