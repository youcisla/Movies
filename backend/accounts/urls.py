from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Account management endpoints
    path('profile/', views.user_profile, name='profile'),
    path('preferences/', views.user_preferences, name='preferences'),
    path('update-preferences/', views.update_preferences, name='update_preferences'),
    path('stats/', views.user_stats, name='user_stats'),
]
