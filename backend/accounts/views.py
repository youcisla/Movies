from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from movies.models import Review, Genre, UserPreference, Watchlist
from django.db.models import Avg
import json


@login_required
def user_profile(request):
    """Get user profile information"""
    user = request.user
    user_reviews = Review.objects.filter(user=user)
    watchlist_items = Watchlist.objects.filter(user=user)
    
    return JsonResponse({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'date_joined': user.date_joined.isoformat(),
        'total_reviews': user_reviews.count(),
        'avg_rating': user_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'watchlist_count': watchlist_items.count(),
    })


@login_required
def user_preferences(request):
    """Get user preferences"""
    try:
        preferences = UserPreference.objects.get(user=request.user)
        favorite_genres = list(preferences.favorite_genres.values('id', 'name'))
    except UserPreference.DoesNotExist:
        favorite_genres = []
    
    return JsonResponse({
        'favorite_genres': favorite_genres,
        'all_genres': list(Genre.objects.values('id', 'name'))
    })


@login_required
@require_http_methods(["POST"])
def update_preferences(request):
    """Update user preferences"""
    try:
        data = json.loads(request.body)
        genre_ids = data.get('favorite_genres', [])
        
        # Get or create user preferences
        preferences, created = UserPreference.objects.get_or_create(user=request.user)
        
        # Clear existing preferences and add new ones
        preferences.favorite_genres.clear()
        for genre_id in genre_ids:
            try:
                genre = Genre.objects.get(id=genre_id)
                preferences.favorite_genres.add(genre)
            except Genre.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': 'Preferences updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def user_stats(request):
    """Get detailed user statistics"""
    user = request.user
    user_reviews = Review.objects.filter(user=user)
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[str(i)] = user_reviews.filter(rating=i).count()
    
    # Favorite genres based on ratings
    favorite_genres = {}
    for review in user_reviews.filter(rating__gte=4):
        for genre in review.movie.genres.all():
            favorite_genres[genre.name] = favorite_genres.get(genre.name, 0) + 1
    
    # Recent reviews
    recent_reviews = user_reviews.order_by('-created_at')[:5]
    
    return JsonResponse({
        'user_id': user.id,
        'username': user.username,
        'total_reviews': user_reviews.count(),
        'avg_rating': user_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'rating_distribution': rating_distribution,
        'favorite_genres': dict(sorted(favorite_genres.items(), key=lambda x: x[1], reverse=True)[:5]),
        'recent_reviews': [
            {
                'movie_title': review.movie.title,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
            }
            for review in recent_reviews
        ]
    })
