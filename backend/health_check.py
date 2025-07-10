#!/usr/bin/env python
"""
Quick health check script for the Django Movie Recommendation System
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommender.settings')
django.setup()

def health_check():
    """Perform a quick health check of the system"""
    print("🔍 Django Movie Recommendation System - Health Check")
    print("=" * 50)
    
    # Check Django settings
    try:
        from django.conf import settings
        print("✅ Django settings loaded successfully")
    except Exception as e:
        print(f"❌ Django settings error: {e}")
        return False
    
    # Check database connectivity
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    # Check models
    try:
        from movies.models import Movie, Genre, Review
        movie_count = Movie.objects.count()
        genre_count = Genre.objects.count()
        review_count = Review.objects.count()
        print(f"✅ Models working: {movie_count} movies, {genre_count} genres, {review_count} reviews")
    except Exception as e:
        print(f"❌ Models error: {e}")
        return False
    
    # Check apps
    try:
        from django.apps import apps
        installed_apps = [app.name for app in apps.get_app_configs()]
        required_apps = ['movies', 'analytics', 'accounts', 'dashboard_queries']
        missing_apps = [app for app in required_apps if app not in installed_apps]
        if missing_apps:
            print(f"⚠️  Missing apps: {missing_apps}")
        else:
            print("✅ All required apps are installed")
    except Exception as e:
        print(f"❌ Apps check error: {e}")
    
    # Check Neo4j (optional)
    try:
        from movie_recommender.neo4j_connection import get_neo4j_connection
        neo4j = get_neo4j_connection()
        # Simple test query
        result = neo4j.run_query("RETURN 1 as test", {})
        if result:
            print("✅ Neo4j connection successful")
        else:
            print("⚠️  Neo4j connection established but no result returned")
    except Exception as e:
        print(f"⚠️  Neo4j connection warning: {e}")
    
    print("=" * 50)
    print("🎉 Health check completed!")
    return True

if __name__ == '__main__':
    health_check()
