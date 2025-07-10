from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # API endpoints
    path('', views.recommendations_list, name='recommendations_list'),
    path('user/<int:user_id>/', views.user_recommendations, name='user_recommendations'),
    path('similar/<int:movie_id>/', views.similar_movies, name='similar_movies'),
    path('trending/', views.trending_movies, name='trending_movies'),
    path('smart/', views.smart_recommendations, name='smart_recommendations'),
    path('action/', views.action_recommendations, name='action_recommendations'),
]
