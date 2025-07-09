"""
Management command to populate the database with sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from movies.models import Genre, Movie, Review
from datetime import date
import random


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Movie.objects.all().delete()
            Genre.objects.all().delete()
            Review.objects.all().delete()
            # Don't delete users, just clear their reviews

        # Create genres
        self.stdout.write('Creating genres...')
        genres_data = [
            (28, 'Action'),
            (12, 'Adventure'),
            (16, 'Animation'),
            (35, 'Comedy'),
            (80, 'Crime'),
            (99, 'Documentary'),
            (18, 'Drama'),
            (10751, 'Family'),
            (14, 'Fantasy'),
            (36, 'History'),
            (27, 'Horror'),
            (10402, 'Music'),
            (9648, 'Mystery'),
            (10749, 'Romance'),
            (878, 'Science Fiction'),
            (10770, 'TV Movie'),
            (53, 'Thriller'),
            (10752, 'War'),
            (37, 'Western'),
        ]

        for tmdb_id, name in genres_data:
            genre, created = Genre.objects.get_or_create(
                tmdb_id=tmdb_id,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(f'  Created genre: {name}')

        # Create sample movies
        self.stdout.write('Creating sample movies...')
        
        # Get some genres for the movies
        action = Genre.objects.get(name='Action')
        drama = Genre.objects.get(name='Drama')
        comedy = Genre.objects.get(name='Comedy')
        scifi = Genre.objects.get(name='Science Fiction')
        thriller = Genre.objects.get(name='Thriller')
        adventure = Genre.objects.get(name='Adventure')

        movies_data = [
            {
                'tmdb_id': 550,
                'title': 'Fight Club',
                'original_title': 'Fight Club',
                'overview': 'A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy.',
                'release_date': date(1999, 10, 15),
                'runtime': 139,
                'poster_path': '/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
                'backdrop_path': '/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg',
                'vote_average': 8.4,
                'vote_count': 24000,
                'popularity': 95.5,
                'genres': [drama, thriller]
            },
            {
                'tmdb_id': 13,
                'title': 'Forrest Gump',
                'original_title': 'Forrest Gump',
                'overview': 'A man with a low IQ has accomplished great things in his life and been present during significant historic events.',
                'release_date': date(1994, 6, 23),
                'runtime': 142,
                'poster_path': '/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg',
                'backdrop_path': '/3h1JZGDhZ8nzxdgvkxha0qBqi05.jpg',
                'vote_average': 8.5,
                'vote_count': 25000,
                'popularity': 89.2,
                'genres': [drama, comedy]
            },
            {
                'tmdb_id': 155,
                'title': 'The Dark Knight',
                'original_title': 'The Dark Knight',
                'overview': 'Batman raises the stakes in his war on crime with the help of Lt. Jim Gordon and DA Harvey Dent.',
                'release_date': date(2008, 7, 18),
                'runtime': 152,
                'poster_path': '/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
                'backdrop_path': '/hqkIcbrOHL86UncnHIsHVcVmzue.jpg',
                'vote_average': 9.0,
                'vote_count': 30000,
                'popularity': 98.7,
                'genres': [action, drama, thriller]
            },
            {
                'tmdb_id': 862,
                'title': 'Toy Story',
                'original_title': 'Toy Story',
                'overview': 'A cowboy doll is profoundly threatened when a new spaceman figure supplants him as top toy in a boy\'s room.',
                'release_date': date(1995, 10, 30),
                'runtime': 81,
                'poster_path': '/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg',
                'backdrop_path': '/4j0YyPWMGl7OgvE0kKvXLnBYi3t.jpg',
                'vote_average': 8.3,
                'vote_count': 15000,
                'popularity': 82.1,
                'genres': [comedy, adventure]
            },
            {
                'tmdb_id': 769,
                'title': 'GoodFellas',
                'original_title': 'GoodFellas',
                'overview': 'The story of Henry Hill and his life in the mob, covering his relationship with his wife Karen Hill.',
                'release_date': date(1990, 9, 12),
                'runtime': 146,
                'poster_path': '/aKuFiU82s5ISJpGZp7YkIr3kCUd.jpg',
                'backdrop_path': '/6FGq9t7Dt3QcrnUWpULnzuP6e6g.jpg',
                'vote_average': 8.7,
                'vote_count': 12000,
                'popularity': 75.3,
                'genres': [drama, thriller]
            },
            {
                'tmdb_id': 603,
                'title': 'The Matrix',
                'original_title': 'The Matrix',
                'overview': 'A computer hacker learns from mysterious rebels about the true nature of his reality.',
                'release_date': date(1999, 3, 30),
                'runtime': 136,
                'poster_path': '/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg',
                'backdrop_path': '/icmmSD4vTTDKOq2vvdulafOGw93.jpg',
                'vote_average': 8.2,
                'vote_count': 22000,
                'popularity': 91.8,
                'genres': [action, scifi, thriller]
            }
        ]

        for movie_data in movies_data:
            genres = movie_data.pop('genres')
            movie, created = Movie.objects.get_or_create(
                tmdb_id=movie_data['tmdb_id'],
                defaults=movie_data
            )
            
            if created:
                movie.genres.set(genres)
                self.stdout.write(f'  Created movie: {movie.title}')
            else:
                self.stdout.write(f'  Movie already exists: {movie.title}')

        # Create sample users and reviews if needed
        if not User.objects.filter(username='demo').exists():
            self.stdout.write('Creating demo user...')
            demo_user = User.objects.create_user(
                username='demo',
                email='demo@movieapp.com',
                password='demo123'
            )
            
            # Create some sample reviews
            movies = Movie.objects.all()
            for movie in movies[:3]:  # Add reviews for first 3 movies
                Review.objects.create(
                    user=demo_user,
                    movie=movie,
                    rating=random.randint(3, 5),
                    comment=f'Great movie! Really enjoyed {movie.title}.'
                )
            
            self.stdout.write('Created demo user and sample reviews')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data!')
        )
        self.stdout.write(f'Total genres: {Genre.objects.count()}')
        self.stdout.write(f'Total movies: {Movie.objects.count()}')
        self.stdout.write(f'Total reviews: {Review.objects.count()}')
