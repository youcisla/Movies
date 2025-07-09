from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Movie, Review, Genre, Watchlist, UserPreference, MovieInteraction
from .recommendation_engine import (
    get_recommendations_for_user, 
    get_popular_movies, 
    get_movies_by_genre,
    record_interaction,
    sync_user_review_to_neo4j,
    sync_user_watchlist_to_neo4j
)
from .tmdb_service import tmdb_service
import json


# Vue d'accueil
def home(request):
    """Page d'accueil avec films populaires et recommandations"""
    context = {
        'popular_movies': get_popular_movies(12),
        'genres': Genre.objects.all()[:8],
    }
    
    if request.user.is_authenticated:
        context['recommended_movies'] = get_recommendations_for_user(request.user, limit=12)
        context['user_reviews_count'] = Review.objects.filter(user=request.user).count()
        context['watchlist_count'] = Watchlist.objects.filter(user=request.user).count()
    
    return render(request, 'movies/home.html', context)


# Liste des films
class MovieListView(ListView):
    model = Movie
    template_name = 'movies/movie_list.html'
    context_object_name = 'movies'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Movie.objects.all()
        
        # Filtrage par recherche
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(overview__icontains=search_query)
            )
        
        # Filtrage par genre
        genre_id = self.request.GET.get('genre')
        if genre_id:
            queryset = queryset.filter(genres__id=genre_id)
        
        # Filtrage par année
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(release_date__year=year)
        
        # Tri
        sort_by = self.request.GET.get('sort', '-popularity')
        if sort_by in ['-popularity', '-vote_average', '-release_date', 'title']:
            queryset = queryset.order_by(sort_by)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        context['current_genre'] = self.request.GET.get('genre')
        context['current_search'] = self.request.GET.get('search', '')
        context['current_year'] = self.request.GET.get('year', '')
        context['current_sort'] = self.request.GET.get('sort', '-popularity')
        return context


# Détails d'un film
class MovieDetailView(DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'
    
    def get_object(self):
        obj = super().get_object()
        
        # Enregistre l'interaction de visualisation
        if self.request.user.is_authenticated:
            record_interaction(self.request.user, obj, 'view')
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.get_object()
        
        # Avis du film
        reviews = Review.objects.filter(movie=movie).order_by('-created_at')
        context['reviews'] = reviews
        context['reviews_count'] = reviews.count()
        context['average_rating'] = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Avis de l'utilisateur actuel
        if self.request.user.is_authenticated:
            context['user_review'] = Review.objects.filter(
                user=self.request.user, 
                movie=movie
            ).first()
            
            # Vérifier si le film est dans la watchlist
            context['in_watchlist'] = Watchlist.objects.filter(
                user=self.request.user,
                movie=movie
            ).exists()
        
        # Films similaires
        if movie.genres.exists():
            similar_movies = Movie.objects.filter(
                genres__in=movie.genres.all()
            ).exclude(id=movie.id).distinct()[:6]
            context['similar_movies'] = similar_movies
        
        return context


# Recommandations
@login_required
def recommendations(request):
    """Page des recommandations personnalisées"""
    recommendation_type = request.GET.get('type', 'hybrid')
    
    recommended_movies = get_recommendations_for_user(
        request.user, 
        limit=20,
        recommendation_type=recommendation_type
    )
    
    # Pagination
    paginator = Paginator(recommended_movies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'movies': page_obj,
        'recommendation_type': recommendation_type,
        'page_obj': page_obj,
    }
    
    return render(request, 'movies/recommendations.html', context)


# Ajouter/Modifier un avis
@login_required
@require_http_methods(["POST"])
def add_review(request, movie_id):
    """Ajouter ou modifier un avis"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    try:
        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '').strip()
        
        if not (1 <= rating <= 5):
            return JsonResponse({'error': 'Note invalide'}, status=400)
        
        review, created = Review.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={
                'rating': rating,
                'comment': comment
            }
        )
        
        # Sync to Neo4j
        sync_user_review_to_neo4j(request.user, movie, rating, comment)
        
        return JsonResponse({
            'success': True,
            'created': created,
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%d/%m/%Y')
            }
        })
        
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': 'Données invalides'}, status=400)


# Supprimer un avis
@login_required
@require_http_methods(["DELETE"])
def delete_review(request, review_id):
    """Supprimer un avis"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return JsonResponse({'success': True})


# Watchlist
@login_required
def watchlist(request):
    """Page de la liste de films à regarder"""
    watchlist_items = Watchlist.objects.filter(user=request.user)
    
    # Pagination
    paginator = Paginator(watchlist_items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'watchlist_items': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'movies/watchlist.html', context)


# Ajouter/Supprimer de la watchlist
@login_required
@require_http_methods(["POST"])
def toggle_watchlist(request, movie_id):
    """Ajouter ou supprimer un film de la watchlist"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    watchlist_item, created = Watchlist.objects.get_or_create(
        user=request.user,
        movie=movie
    )
    
    if not created:
        watchlist_item.delete()
        in_watchlist = False
    else:
        in_watchlist = True
        # Sync to Neo4j when adding to watchlist
        sync_user_watchlist_to_neo4j(request.user, movie)
    
    return JsonResponse({
        'success': True,
        'in_watchlist': in_watchlist
    })


# Recherche
def search(request):
    """Page de recherche"""
    query = request.GET.get('q', '').strip()
    movies = []
    
    if query:
        # Recherche dans la base locale
        movies = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(overview__icontains=query)
        )[:20]
        
        # Si peu de résultats, recherche sur TMDb
        if movies.count() < 5:
            tmdb_results = tmdb_service.search_movies(query)
            
            if tmdb_results and 'results' in tmdb_results:
                for movie_data in tmdb_results['results'][:10]:
                    saved_movie = tmdb_service.save_movie_to_db(movie_data)
                    if saved_movie and saved_movie not in movies:
                        movies = list(movies) + [saved_movie]
    
    # Pagination
    paginator = Paginator(movies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'movies': page_obj,
        'query': query,
        'page_obj': page_obj,
    }
    
    return render(request, 'movies/search.html', context)


# Films par genre
def movies_by_genre(request, genre_id):
    """Films d'un genre spécifique"""
    genre = get_object_or_404(Genre, id=genre_id)
    movies = get_movies_by_genre(genre_id, limit=100)
    
    # Pagination
    paginator = Paginator(movies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'genre': genre,
        'movies': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'movies/genre.html', context)


# Profil utilisateur
@login_required
def profile(request):
    """Page de profil utilisateur"""
    user_reviews = Review.objects.filter(user=request.user).order_by('-created_at')
    user_watchlist = Watchlist.objects.filter(user=request.user).order_by('-added_at')
    
    # Statistiques
    stats = {
        'total_reviews': user_reviews.count(),
        'total_watchlist': user_watchlist.count(),
        'average_rating': user_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'favorite_genres': [],
    }
    
    # Genres préférés basés sur les avis
    genre_counts = {}
    for review in user_reviews.filter(rating__gte=4):
        for genre in review.movie.genres.all():
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    stats['favorite_genres'] = sorted(
        genre_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    context = {
        'user_reviews': user_reviews[:10],
        'user_watchlist': user_watchlist[:10],
        'stats': stats,
    }
    
    return render(request, 'movies/profile.html', context)


# API endpoints
@csrf_exempt
def api_popular_movies(request):
    """API pour récupérer les films populaires"""
    movies = get_popular_movies(20)
    
    data = []
    for movie in movies:
        data.append({
            'id': movie.id,
            'title': movie.title,
            'overview': movie.overview[:200],
            'release_date': movie.release_date.isoformat() if movie.release_date else None,
            'vote_average': movie.vote_average,
            'poster_url': movie.poster_url,
            'genres': [genre.name for genre in movie.genres.all()],
        })
    
    return JsonResponse({'movies': data})


@csrf_exempt
@login_required
def api_recommendations(request):
    """API pour récupérer les recommandations"""
    limit = int(request.GET.get('limit', 20))
    
    movies = get_recommendations_for_user(
        request.user,
        limit=limit
    )
    
    data = []
    for movie in movies:
        data.append({
            'id': movie.id,
            'title': movie.title,
            'overview': movie.overview[:200],
            'release_date': movie.release_date.isoformat() if movie.release_date else None,
            'vote_average': movie.vote_average,
            'poster_url': movie.poster_url,
            'genres': [genre.name for genre in movie.genres.all()],
        })
    
    return JsonResponse({'movies': data})


# Authentification
def login_view(request):
    """Page de connexion"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Connexion réussie!')
            return redirect('movies:home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'movies/login.html')


def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.success(request, 'Déconnexion réussie!')
    return redirect('movies:home')


from django.contrib.auth.forms import UserCreationForm

def register_view(request):
    """Page d'inscription"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username}!')
            login(request, user)
            return redirect('movies:home')
    else:
        form = UserCreationForm()
    
    return render(request, 'movies/register.html', {'form': form})
