from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),  # Afficher la liste des films
    path('recommendations/<int:movie_id>/', views.movie_recommendations, name='movie_recommendations'),  # Recommandations pour un film
]
