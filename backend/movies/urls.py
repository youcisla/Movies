from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('movies/', views.MovieListView.as_view(), name='movie_list'),
    path('movies/<int:pk>/', views.MovieDetailView.as_view(), name='movie_detail'),
    path('search/', views.search, name='search'),
    path('genre/<int:genre_id>/', views.movies_by_genre, name='movies_by_genre'),
    
    # Recommandations
    path('recommendations/', views.recommendations, name='recommendations'),
    
    # Avis
    path('movies/<int:movie_id>/review/', views.add_review, name='add_review'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    
    # Watchlist
    path('watchlist/', views.watchlist, name='watchlist'),
    path('movies/<int:movie_id>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
    
    # Profil
    path('profile/', views.profile, name='profile'),
    
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # API
    path('api/popular/', views.api_popular_movies, name='api_popular_movies'),
    path('api/recommendations/', views.api_recommendations, name='api_recommendations'),
    path('api/neo4j_movies/', views.api_neo4j_movies, name='api_neo4j_movies'),
]
