from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Analytics endpoints
    path('', views.analytics_dashboard, name='dashboard'),
    path('popularity/', views.movie_popularity, name='movie_popularity'),
    path('ratings/', views.ratings_analytics, name='ratings_analytics'),
    path('user-stats/', views.user_statistics, name='user_statistics'),
    path('genre-trends/', views.genre_trends, name='genre_trends'),
]
