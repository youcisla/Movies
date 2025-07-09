from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from movies.models import Movie
from movies.recommendation_engine import (
    get_recommendations_for_user,
    get_similar_movies,
    get_trending_movies
)


@login_required
def recommendations_list(request):
    """Get recommendations for the current user"""
    recommendations = get_recommendations_for_user(request.user, limit=20)
    
    return JsonResponse({
        'recommendations': [
            {
                'id': movie.id,
                'title': movie.title,
                'poster_url': movie.poster_url,
                'vote_average': movie.vote_average,
                'release_year': movie.release_year,
            }
            for movie in recommendations
        ]
    })


def user_recommendations(request, user_id):
    """Get recommendations for a specific user"""
    user = get_object_or_404(User, id=user_id)
    recommendations = get_recommendations_for_user(user, limit=20)
    
    return JsonResponse({
        'user_id': user_id,
        'recommendations': [
            {
                'id': movie.id,
                'title': movie.title,
                'poster_url': movie.poster_url,
                'vote_average': movie.vote_average,
                'release_year': movie.release_year,
            }
            for movie in recommendations
        ]
    })


def similar_movies(request, movie_id):
    """Get movies similar to the specified movie"""
    movie = get_object_or_404(Movie, id=movie_id)
    similar = get_similar_movies(movie, limit=12)
    
    return JsonResponse({
        'movie_id': movie_id,
        'movie_title': movie.title,
        'similar_movies': [
            {
                'id': similar_movie.id,
                'title': similar_movie.title,
                'poster_url': similar_movie.poster_url,
                'vote_average': similar_movie.vote_average,
                'release_year': similar_movie.release_year,
            }
            for similar_movie in similar
        ]
    })


def trending_movies(request):
    """Get trending movies"""
    trending = get_trending_movies(limit=20)
    
    return JsonResponse({
        'trending_movies': [
            {
                'id': movie.id,
                'title': movie.title,
                'poster_url': movie.poster_url,
                'vote_average': movie.vote_average,
                'release_year': movie.release_year,
                'popularity': movie.popularity,
            }
            for movie in trending
        ]
    })
