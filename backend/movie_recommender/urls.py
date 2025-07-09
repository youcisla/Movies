"""
URL configuration for movie_recommender project.

A modern, production-ready movie recommendation system built with Django, MongoDB Atlas, and Neo4j AuraDB.
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
        'service': 'Django Movie Recommendation System',
        'version': '1.0.0'
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Main application
    path('', include('movies.urls')),
    
    # API endpoints
    path('api/', include([
        path('recommendations/', include('recommendations.urls')),
        path('analytics/', include('analytics.urls')),
        path('accounts/', include('accounts.urls')),
    ])),
]

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar (only add if not already present)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        try:
            import debug_toolbar
            urlpatterns = [
                path('__debug__/', include(debug_toolbar.urls)),
            ] + urlpatterns
        except ImportError:
            pass

# Admin site customization
admin.site.site_header = "Movie Recommendation System Admin"
admin.site.site_title = "Movie Recommendation System"
admin.site.index_title = "Welcome to Movie Recommendation System Administration"
