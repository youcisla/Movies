from django.urls import path
from . import views_simple as views

app_name = 'movies'

urlpatterns = [
    # Pages principales
    path('', views.movie_list, name='movie_list'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('recommendations/<int:user_id>/', views.movie_recommendations, name='movie_recommendations'),
    
    # Actions
    path('movie/<int:movie_id>/review/', views.add_review, name='add_review'),
    
    # Recherche et filtres
    path('search/', views.search_movies, name='search'),
    path('genre/<int:genre_id>/', views.movies_by_genre, name='movies_by_genre'),
    
    # API
    path('api/popular/', views.api_popular_movies, name='api_popular_movies'),
    path('api/recommendations/', views.api_recommendations, name='api_recommendations'),
]
