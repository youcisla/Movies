#!/usr/bin/env python
"""
Simple script to populate basic movie data for testing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommender.settings')
django.setup()

from movies.models import Movie, Genre
from datetime import date

def create_basic_data():
    """Create basic genres and sample movies"""
    
    # Create genres
    genres_data = [
        {'name': 'Action', 'tmdb_id': 28},
        {'name': 'Adventure', 'tmdb_id': 12},
        {'name': 'Animation', 'tmdb_id': 16},
        {'name': 'Comedy', 'tmdb_id': 35},
        {'name': 'Crime', 'tmdb_id': 80},
        {'name': 'Drama', 'tmdb_id': 18},
        {'name': 'Fantasy', 'tmdb_id': 14},
        {'name': 'Horror', 'tmdb_id': 27},
        {'name': 'Romance', 'tmdb_id': 10749},
        {'name': 'Science Fiction', 'tmdb_id': 878},
        {'name': 'Thriller', 'tmdb_id': 53},
    ]
    
    print("Creating genres...")
    for genre_data in genres_data:
        genre, created = Genre.objects.get_or_create(
            name=genre_data['name'],
            defaults={'tmdb_id': genre_data['tmdb_id']}
        )
        if created:
            print(f"Created genre: {genre.name}")
    
    # Create sample movies
    movies_data = [
        {
            'title': 'The Matrix',
            'overview': 'A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.',
            'release_date': date(1999, 3, 31),
            'vote_average': 8.2,
            'vote_count': 15000,
            'popularity': 85.5,
            'genres': ['Action', 'Science Fiction']
        },
        {
            'title': 'Inception',
            'overview': 'A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.',
            'release_date': date(2010, 7, 16),
            'vote_average': 8.8,
            'vote_count': 28000,
            'popularity': 92.3,
            'genres': ['Action', 'Science Fiction', 'Thriller']
        },
        {
            'title': 'The Dark Knight',
            'overview': 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests.',
            'release_date': date(2008, 7, 18),
            'vote_average': 9.0,
            'vote_count': 32000,
            'popularity': 95.7,
            'genres': ['Action', 'Crime', 'Drama']
        },
        {
            'title': 'Pulp Fiction',
            'overview': 'The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.',
            'release_date': date(1994, 10, 14),
            'vote_average': 8.9,
            'vote_count': 25000,
            'popularity': 88.4,
            'genres': ['Crime', 'Drama']
        },
        {
            'title': 'Forrest Gump',
            'overview': 'The presidencies of Kennedy and Johnson, the events of Vietnam, Watergate and other historical events unfold through the perspective of an Alabama man.',
            'release_date': date(1994, 7, 6),
            'vote_average': 8.8,
            'vote_count': 24000,
            'popularity': 87.2,
            'genres': ['Drama', 'Romance']
        }
    ]
    
    print("Creating sample movies...")
    for movie_data in movies_data:
        movie, created = Movie.objects.get_or_create(
            title=movie_data['title'],
            defaults={
                'overview': movie_data['overview'],
                'release_date': movie_data['release_date'],
                'vote_average': movie_data['vote_average'],
                'vote_count': movie_data['vote_count'],
                'popularity': movie_data['popularity']
            }
        )
        
        if created:
            # Add genres
            for genre_name in movie_data['genres']:
                try:
                    genre = Genre.objects.get(name=genre_name)
                    movie.genres.add(genre)
                except Genre.DoesNotExist:
                    print(f"Genre {genre_name} not found for movie {movie.title}")
            
            print(f"Created movie: {movie.title}")
        else:
            print(f"Movie already exists: {movie.title}")

if __name__ == '__main__':
    create_basic_data()
    print("Basic data creation completed!")
