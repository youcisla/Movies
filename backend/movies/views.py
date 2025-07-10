from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db import connection
from django.contrib.auth.forms import UserCreationForm
import json
import logging

logger = logging.getLogger(__name__)

from .models import Movie, Review, Genre, Watchlist, UserPreference, MovieInteraction

# Add error handling for Neo4j imports
try:
    from .neo4j_recommendation_engine import neo4j_engine
    from .neo4j_movie_service import neo4j_movie_service
    NEO4J_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Neo4j services not available: {e}")
    neo4j_engine = None
    neo4j_movie_service = None
    NEO4J_AVAILABLE = False

try:
    from movie_recommender.neo4j_connection import get_neo4j_connection
except ImportError as e:
    logger.warning(f"Neo4j connection not available: {e}")
    get_neo4j_connection = None

from .tmdb_service import tmdb_service
from .recommendation_engine import get_action_movie_recommendations

logger = logging.getLogger(__name__)


# Vue d'accueil
def home(request):
    """Page d'accueil avec films populaires et recommandations"""
    try:
        popular_movies = []
        if NEO4J_AVAILABLE and neo4j_movie_service:
            neo4j_movies = neo4j_movie_service.get_popular_movies(12) or []
            # Convert Neo4j records to dictionaries and add pk field
            for movie in neo4j_movies:
                try:
                    # Convert Record to dict if needed
                    if hasattr(movie, '_asdict'):  # Neo4j Record object
                        movie_dict = dict(movie)
                    elif isinstance(movie, dict):
                        movie_dict = movie.copy()
                    else:
                        movie_dict = dict(movie)
                    
                    if movie_dict.get('movie_id'):  # Only include movies with valid IDs
                        movie_dict['pk'] = movie_dict['movie_id']  # Add pk for URL reversal
                        movie_dict['id'] = movie_dict['movie_id']  # Add id field for template compatibility
                        # Add poster URL if poster_path exists
                        if movie_dict.get('poster_path'):
                            movie_dict['poster_url'] = f"https://image.tmdb.org/t/p/w500{movie_dict['poster_path']}"
                        popular_movies.append(movie_dict)
                except Exception as e:
                    logger.warning(f"Error processing movie record: {e}")
                    continue
        
        # If Neo4j is empty or unavailable, use Django models as fallback
        if not popular_movies:
            logger.info("Using Django models as fallback for popular movies")
            django_movies = Movie.objects.filter(vote_average__gte=7.0).order_by('-popularity', '-vote_average')[:12]
            popular_movies = [
                {
                    'id': movie.id,
                    'movie_id': movie.id,
                    'title': movie.title,
                    'genres': [genre.name for genre in movie.genres.all()],
                    'rating': movie.vote_average,
                    'release_date': movie.release_date.isoformat() if movie.release_date else None,
                    'overview': movie.overview,
                    'poster_path': movie.poster_path,
                    'poster_url': f"https://image.tmdb.org/t/p/w500{movie.poster_path}" if movie.poster_path else "",
                    'pk': movie.id  # Add pk for URL reversal
                }
                for movie in django_movies
            ]
    except Exception as e:
        logger.error(f"Error fetching popular movies: {e}")
        popular_movies = []
    
    context = {
        'popular_movies': popular_movies,
        'genres': Genre.objects.all()[:8],
    }
    
    if request.user.is_authenticated:
        # Synchroniser l'utilisateur dans Neo4j si disponible
        if NEO4J_AVAILABLE and neo4j_movie_service:
            user_data = {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'date_joined': request.user.date_joined.isoformat(),
                'is_active': request.user.is_active
            }
            try:
                neo4j_movie_service.create_or_update_user(user_data)
                
                # Obtenir les recommandations intelligentes
                recommended_movies = neo4j_engine.get_recommendations_for_user(
                    request.user.id, limit=12, recommendation_type='smart'
                ) or []
                context['recommended_movies'] = recommended_movies
            except Exception as e:
                logger.error(f"Error fetching recommendations: {e}")
                context['recommended_movies'] = []
        else:
            context['recommended_movies'] = []
        
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
        
        # Enregistre l'interaction de visualisation dans Neo4j
        if self.request.user.is_authenticated:
            neo4j_engine.record_user_interaction(
                self.request.user.id, obj.id, 'view'
            )
        
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
        
        # Films similaires - utilise Neo4j
        try:
            if NEO4J_AVAILABLE and neo4j_movie_service:
                similar_movies_raw = neo4j_movie_service.get_similar_movies(movie.id, limit=6) or []
                similar_movies_data = []
                for sim_movie in similar_movies_raw:
                    try:
                        # Convert Record to dict if needed
                        if hasattr(sim_movie, '_asdict'):  # Neo4j Record object
                            movie_dict = dict(sim_movie)
                        elif isinstance(sim_movie, dict):
                            movie_dict = sim_movie.copy()
                        else:
                            movie_dict = dict(sim_movie)
                        
                        if movie_dict.get('movie_id'):
                            movie_dict['pk'] = movie_dict['movie_id']
                            movie_dict['id'] = movie_dict['movie_id']
                            # Add poster URL if poster_path exists
                            if movie_dict.get('poster_path'):
                                movie_dict['poster_url'] = f"https://image.tmdb.org/t/p/w500{movie_dict['poster_path']}"
                            similar_movies_data.append(movie_dict)
                    except Exception as e:
                        logger.warning(f"Error processing similar movie record: {e}")
                        continue
                context['similar_movies'] = similar_movies_data
            else:
                context['similar_movies'] = []
        except Exception as e:
            logger.error(f"Error fetching similar movies: {e}")
            context['similar_movies'] = []
        
        return context


# Recommandations
@login_required
def recommendations(request):
    """Page des recommandations personnalisées avec intelligence améliorée"""
    recommendation_type = request.GET.get('type', 'smart')
    
    try:
        if NEO4J_AVAILABLE and neo4j_engine:
            # Utilise le nouveau moteur Neo4j pour toutes les recommandations
            neo4j_recommendations = neo4j_engine.get_recommendations_for_user(
                request.user.id, 
                limit=20,
                recommendation_type=recommendation_type
            ) or []
            
            # Convert Neo4j records to dictionaries
            recommended_movies = []
            for movie in neo4j_recommendations:
                try:
                    # Convert Record to dict if needed
                    if hasattr(movie, '_asdict'):  # Neo4j Record object
                        movie_dict = dict(movie)
                    elif isinstance(movie, dict):
                        movie_dict = movie.copy()
                    else:
                        movie_dict = dict(movie)
                    
                    if movie_dict.get('movie_id'):  # Only include movies with valid IDs
                        movie_dict['pk'] = movie_dict['movie_id']  # Add pk for URL reversal
                        movie_dict['id'] = movie_dict['movie_id']  # Add id field for template compatibility
                        # Add poster URL if poster_path exists
                        if movie_dict.get('poster_path'):
                            movie_dict['poster_url'] = f"https://image.tmdb.org/t/p/w500{movie_dict['poster_path']}"
                        recommended_movies.append(movie_dict)
                except Exception as e:
                    logger.warning(f"Error processing recommendation record: {e}")
                    continue
        else:
            recommended_movies = []
    except Exception as e:
        logger.error(f"Error fetching recommendations: {e}")
        recommended_movies = []
    
    # Pagination
    paginator = Paginator(recommended_movies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'movies': page_obj,
        'recommendation_type': recommendation_type,
        'page_obj': page_obj,
        'use_neo4j': NEO4J_AVAILABLE,
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
        
        # Sync to Neo4j avec le nouveau système
        neo4j_engine.record_user_interaction(
            request.user.id, movie.id, 'rating', rating=rating, comment=comment
        )
        
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
        # Sync removal to Neo4j if needed
        try:
            neo4j_engine.record_user_interaction(
                request.user.id, movie.id, 'remove_watchlist'
            )
        except Exception as e:
            logger.warning(f"Failed to sync watchlist removal to Neo4j: {e}")
        in_watchlist = False
    else:
        in_watchlist = True
        # Sync to Neo4j when adding to watchlist
        neo4j_engine.record_user_interaction(
            request.user.id, movie.id, 'watchlist'
        )
    
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
    
    try:
        if NEO4J_AVAILABLE and neo4j_movie_service:
            movies_data = neo4j_movie_service.get_movies_by_genre(genre.name, limit=100) or []
            # Convert Neo4j records to dictionaries and add pk field
            movies_with_pk = []
            for movie in movies_data:
                # Convert Record to dict if needed
                if hasattr(movie, '_asdict'):  # Neo4j Record object
                    movie_dict = dict(movie)
                elif isinstance(movie, dict):
                    movie_dict = movie.copy()
                else:
                    movie_dict = dict(movie)
                
                if movie_dict.get('movie_id'):
                    movie_dict['pk'] = movie_dict['movie_id']
                    movie_dict['id'] = movie_dict['movie_id']  # Add id field for template compatibility
                    # Add poster URL if poster_path exists
                    if movie_dict.get('poster_path'):
                        movie_dict['poster_url'] = f"https://image.tmdb.org/t/p/w500{movie_dict['poster_path']}"
                    movies_with_pk.append(movie_dict)
        else:
            # Fallback to Django ORM
            django_movies = Movie.objects.filter(genres=genre).order_by('-vote_average', '-popularity')[:100]
            movies_with_pk = [
                {
                    'id': movie.id,
                    'movie_id': movie.id,
                    'title': movie.title,
                    'genres': [g.name for g in movie.genres.all()],
                    'rating': movie.vote_average,
                    'release_date': movie.release_date.isoformat() if movie.release_date else None,
                    'overview': movie.overview,
                    'poster_path': movie.poster_path,
                    'poster_url': f"https://image.tmdb.org/t/p/w500{movie.poster_path}" if movie.poster_path else "",
                    'pk': movie.id
                }
                for movie in django_movies
            ]
    except Exception as e:
        logger.error(f"Error fetching movies by genre: {e}")
        # Fallback to Django ORM on error
        django_movies = Movie.objects.filter(genres=genre).order_by('-vote_average', '-popularity')[:100]
        movies_with_pk = [
            {
                'id': movie.id,
                'movie_id': movie.id,
                'title': movie.title,
                'genres': [g.name for g in movie.genres.all()],
                'rating': movie.vote_average,
                'release_date': movie.release_date.isoformat() if movie.release_date else None,
                'overview': movie.overview,
                'poster_path': movie.poster_path,
                'poster_url': f"https://image.tmdb.org/t/p/w500{movie.poster_path}" if movie.poster_path else "",
                'pk': movie.id
            }
            for movie in django_movies
        ]
    
    # Pagination
    paginator = Paginator(movies_with_pk, 12)
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
    movies_data = neo4j_movie_service.get_popular_movies(20)
    
    data = []
    for movie_data in movies_data:
        data.append({
            'id': movie_data.get('movie_id'),
            'title': movie_data.get('title'),
            'overview': movie_data.get('overview', '')[:200],
            'release_date': movie_data.get('release_date'),
            'vote_average': movie_data.get('rating'),
            'poster_url': '',  # Will need to be fetched separately or stored in Neo4j
            'genres': movie_data.get('genres', []),
        })
    
    return JsonResponse({'movies': data})


@csrf_exempt
@login_required
def api_recommendations(request):
    """API pour récupérer les recommandations"""
    limit = int(request.GET.get('limit', 20))
    recommendation_type = request.GET.get('type', 'smart')
    
    movies_data = neo4j_engine.get_recommendations_for_user(
        request.user.id,
        limit=limit,
        recommendation_type=recommendation_type
    )
    
    data = []
    for movie_data in movies_data:
        data.append({
            'id': movie_data.get('movie_id'),
            'title': movie_data.get('title'),
            'overview': '',  # Will need to be added to Neo4j schema
            'release_date': movie_data.get('release_date'),
            'vote_average': movie_data.get('rating'),
            'poster_url': '',  # Will need to be added to Neo4j schema
            'genres': movie_data.get('genres', []),
            'recommendation_score': movie_data.get('recommendation_score', 0.0)
        })
    
    return JsonResponse({'movies': data})


@csrf_exempt
@login_required
def api_neo4j_recommendations(request):
    """API pour récupérer les recommandations depuis Neo4j"""
    limit = int(request.GET.get('limit', 20))
    user_id = request.user.id
    neo4j_conn = get_neo4j_connection()
    recommendations = neo4j_conn.get_user_recommendations(user_id, limit=limit)
    # Formatage des résultats Neo4j (liste de dicts)
    data = []
    for rec in recommendations:
        data.append({
            'id': rec.get('movie_id'),
            'title': rec.get('title'),
        })
    return JsonResponse({'movies': data})


@csrf_exempt
def api_neo4j_movies(request):
    """API pour lister tous les films depuis Neo4j"""
    limit = int(request.GET.get('limit', 100))
    neo4j_conn = get_neo4j_connection()
    query = """
    MATCH (m:Movie)
    RETURN m.id as id, m.title as title
    ORDER BY m.title ASC
    LIMIT $limit
    """
    results = neo4j_conn.run_query(query, {"limit": limit})
    data = []
    for rec in results:
        data.append({
            'id': rec.get('id'),
            'title': rec.get('title'),
        })
    return JsonResponse({'movies': data})


# Authentication views
def login_view(request):
    """Vue de connexion"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Connexion réussie!')
            return redirect('movies:home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    return render(request, 'movies/login.html')

def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, 'Déconnexion réussie!')
    return redirect('movies:home')

def register_view(request):
    """Vue d'inscription"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username}!')
            return redirect('movies:login')
    else:
        form = UserCreationForm()
    return render(request, 'movies/register.html', {'form': form})

# API Views
@csrf_exempt
def api_movies_list(request):
    """API pour lister les films"""
    movies = Movie.objects.all()[:20]
    data = []
    for movie in movies:
        data.append({
            'id': movie.id,
            'title': movie.title,
            'overview': movie.overview,
            'release_date': movie.release_date.isoformat() if movie.release_date else None,
            'vote_average': float(movie.vote_average) if movie.vote_average else 0,
            'poster_path': movie.poster_path,
            'genres': [genre.name for genre in movie.genres.all()],
        })
    return JsonResponse({'movies': data})

@csrf_exempt
def api_movie_detail(request, movie_id):
    """API pour les détails d'un film"""
    movie = get_object_or_404(Movie, id=movie_id)
    data = {
        'id': movie.id,
        'title': movie.title,
        'overview': movie.overview,
        'release_date': movie.release_date.isoformat() if movie.release_date else None,
        'vote_average': float(movie.vote_average) if movie.vote_average else 0,
        'vote_count': movie.vote_count,
        'poster_path': movie.poster_path,
        'backdrop_path': movie.backdrop_path,
        'genres': [genre.name for genre in movie.genres.all()],
    }
    return JsonResponse(data)

@csrf_exempt
def api_movie_reviews(request, movie_id):
    """API pour les avis d'un film"""
    movie = get_object_or_404(Movie, id=movie_id)
    reviews = Review.objects.filter(movie=movie).order_by('-created_at')
    data = []
    for review in reviews:
        data.append({
            'id': review.id,
            'user': review.user.username,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat(),
        })
    return JsonResponse({'reviews': data})

@csrf_exempt
def api_genres_list(request):
    """API pour lister les genres"""
    genres = Genre.objects.all()
    data = []
    for genre in genres:
        data.append({
            'id': genre.id,
            'name': genre.name,
        })
    return JsonResponse({'genres': data})

@csrf_exempt
@login_required
def api_recommendations(request):
    """API pour les recommandations"""
    try:
        recommended_movies = neo4j_engine.get_recommendations_for_user(
            request.user.id, limit=20, recommendation_type='smart'
        )
        return JsonResponse({'movies': recommended_movies})
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return JsonResponse({'error': 'Unable to get recommendations'}, status=500)

# Dashboard Views
@login_required
def dashboard(request):
    """Dashboard intelligent avec Q&A interactif"""
    context = {
        'user': request.user,
        'total_movies': Movie.objects.count(),
        'total_reviews': Review.objects.count(),
        'user_reviews_count': Review.objects.filter(user=request.user).count(),
    }
    
    return render(request, 'movies/dashboard.html', context)

@csrf_exempt
def api_intelligent_qa(request):
    """API pour le Q&A intelligent"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            
            # Simple response system - can be enhanced with AI
            response = {
                'answer': f"Merci pour votre question: '{question}'. Cette fonctionnalité sera bientôt disponible.",
                'suggestions': [
                    'Quels sont les films les plus populaires?',
                    'Recommandez-moi un film d\'action',
                    'Quels sont les derniers films sortis?'
                ]
            }
            
            return JsonResponse(response)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def api_analytics(request):
    """API pour les analytics"""
    data = {
        'success': True,
        'popular_genres': 'Action, Drama, Comedy',
        'seasonal_trends': 'Action movies trending',
        'sentiment_analysis': 'Positive',
        'user_engagement': 'High'
    }
    return JsonResponse(data)

@csrf_exempt
def api_user_profile(request):
    """API pour le profil utilisateur"""
    if request.user.is_authenticated:
        data = {
            'username': request.user.username,
            'email': request.user.email,
            'reviews_count': Review.objects.filter(user=request.user).count(),
            'watchlist_count': Watchlist.objects.filter(user=request.user).count(),
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Not authenticated'}, status=401)

@csrf_exempt
def api_dashboard_queries(request):
    """API to handle dashboard queries"""
    try:
        data = {
            'success': True,
            'action_movies': [
                {'title': 'The Matrix', 'rating': 8.7},
                {'title': 'John Wick', 'rating': 7.4},
                {'title': 'Mad Max: Fury Road', 'rating': 8.1},
            ],
            'sci_fi_movies': [
                {'title': 'Blade Runner 2049', 'rating': 8.0},
                {'title': 'Interstellar', 'rating': 8.6},
                {'title': 'Ex Machina', 'rating': 7.7},
            ],
            'popular_this_week': [
                {'title': 'Dune', 'rating': 8.0},
                {'title': 'Spider-Man: No Way Home', 'rating': 8.4},
                {'title': 'The Batman', 'rating': 7.8},
            ],
            'comedy_trends': [
                {'title': 'Deadpool', 'rating': 8.0},
                {'title': 'The Grand Budapest Hotel', 'rating': 8.1},
                {'title': 'Knives Out', 'rating': 7.9},
            ],
            'top_directors': [
                {'director': 'Christopher Nolan'},
                {'director': 'Denis Villeneuve'},
                {'director': 'Quentin Tarantino'},
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Dashboard queries error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'action_movies': [],
            'sci_fi_movies': [],
            'popular_this_week': [],
            'comedy_trends': [],
            'top_directors': []
        })


@require_http_methods(["GET"])
def api_search_suggestions(request):
    """API endpoint for search suggestions"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    try:
        # Search for movie titles matching the query
        movies = Movie.objects.filter(
            title__icontains=query
        ).exclude(
            title__exact=''
        ).order_by('-popularity', '-vote_average')[:8]
        
        suggestions = []
        for movie in movies:
            suggestions.append({
                'title': movie.title,
                'type': 'movie',
                'year': movie.release_date.year if movie.release_date else None,
                'poster_url': f"https://image.tmdb.org/t/p/w92{movie.poster_path}" if movie.poster_path else None,
                'url': f"/movies/{movie.id}/"
            })
        
        # Also search for genres if query is long enough
        if len(query) >= 3:
            genres = Genre.objects.filter(
                name__icontains=query
            ).order_by('name')[:3]
            
            for genre in genres:
                suggestions.append({
                    'title': genre.name,
                    'type': 'genre',
                    'url': f"/movies/genre/{genre.id}/"
                })
        
        return JsonResponse({'suggestions': suggestions})
        
    except Exception as e:
        logger.error(f"Search suggestions error: {e}")
        return JsonResponse({'suggestions': []})
