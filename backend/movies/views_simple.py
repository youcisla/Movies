from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.views.generic import ListView, DetailView

from .models import Movie, Review, Genre
from .recommendation import recommend_movies, get_popular_movies, get_movies_by_genre
import json


def movie_list(request):
    """Vue pour afficher la liste des films"""
    movies = Movie.objects.all()
    
    # Recherche
    search_query = request.GET.get('search')
    if search_query:
        movies = movies.filter(
            Q(title__icontains=search_query) | 
            Q(overview__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(movies.order_by('-popularity'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'movies': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'search_query': search_query or '',
    }
    
    return render(request, 'movie_list_simple.html', context)


def movie_detail(request, movie_id):
    """Vue pour afficher les détails d'un film"""
    movie = get_object_or_404(Movie, id=movie_id)
    reviews = Review.objects.filter(movie=movie).order_by('-created_at')
    
    context = {
        'movie': movie,
        'reviews': reviews,
        'reviews_count': reviews.count(),
        'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
    }
    
    return render(request, 'movie_detail_simple.html', context)


def movie_recommendations(request, user_id):
    """Vue pour afficher les recommandations personnalisées"""
    try:
        user = User.objects.get(id=user_id)
        recommended_movies = recommend_movies(user_id)
        
        context = {
            'movies': recommended_movies,
            'user': user,
        }
        
        return render(request, 'movie_recommendations_simple.html', context)
    
    except User.DoesNotExist:
        messages.error(request, "Utilisateur introuvable")
        return redirect('movies:movie_list')


@login_required
def add_review(request, movie_id):
    """Vue pour ajouter un avis sur un film"""
    if request.method == 'POST':
        movie = get_object_or_404(Movie, id=movie_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        if rating:
            # Vérifier si l'utilisateur a déjà noté ce film
            review, created = Review.objects.get_or_create(
                user=request.user,
                movie=movie,
                defaults={
                    'rating': float(rating),
                    'comment': comment
                }
            )
            
            if not created:
                # Mettre à jour l'avis existant
                review.rating = float(rating)
                review.comment = comment
                review.save()
                messages.success(request, "Votre avis a été mis à jour")
            else:
                messages.success(request, "Votre avis a été ajouté")
        else:
            messages.error(request, "Veuillez sélectionner une note")
    
    return redirect('movies:movie_detail', movie_id=movie_id)


def api_popular_movies(request):
    """API pour récupérer les films populaires"""
    movies = get_popular_movies(20)
    movies_data = []
    
    for movie in movies:
        movies_data.append({
            'id': movie.id,
            'title': movie.title,
            'overview': movie.overview,
            'release_year': movie.release_year,
            'vote_average': movie.vote_average,
            'poster_url': movie.poster_url,
            'genres': [genre.name for genre in movie.genres.all()]
        })
    
    return JsonResponse({'movies': movies_data})


@login_required
def api_recommendations(request):
    """API pour récupérer les recommandations personnalisées"""
    recommended_movies = recommend_movies(request.user.id)
    movies_data = []
    
    for movie in recommended_movies:
        movies_data.append({
            'id': movie.id,
            'title': movie.title,
            'overview': movie.overview,
            'release_year': movie.release_year,
            'vote_average': movie.vote_average,
            'poster_url': movie.poster_url,
            'genres': [genre.name for genre in movie.genres.all()]
        })
    
    return JsonResponse({'movies': movies_data})


def search_movies(request):
    """Vue pour la recherche de films"""
    query = request.GET.get('q', '')
    movies = []
    
    if query:
        movies = Movie.objects.filter(
            Q(title__icontains=query) | 
            Q(overview__icontains=query)
        ).order_by('-popularity')[:50]
    
    context = {
        'movies': movies,
        'query': query,
    }
    
    return render(request, 'movie_list_simple.html', context)


def movies_by_genre(request, genre_id):
    """Vue pour afficher les films d'un genre spécifique"""
    genre = get_object_or_404(Genre, id=genre_id)
    movies = Movie.objects.filter(genres=genre).order_by('-vote_average', '-popularity')
    
    # Pagination
    paginator = Paginator(movies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'movies': page_obj,
        'genre': genre,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'movie_list_simple.html', context)
