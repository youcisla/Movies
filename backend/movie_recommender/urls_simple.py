"""
URL configuration for movie_recommender project - Version Simple

Système de recommandation de films Django avec MongoDB, Neo4j et TMDb API.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Django Movie Recommendation System - Simple',
        'version': '1.0.0'
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Main application - Version Simple
    path('', include('movies.urls_simple')),
]

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = "Movie Recommendation System Admin"
admin.site.site_title = "Movie Recommendation System"
admin.site.index_title = "Administration du système de recommandation"
