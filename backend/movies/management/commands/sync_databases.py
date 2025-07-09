"""
Management command to sync existing Django data to MongoDB and Neo4j
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from movies.models import Movie, Review, Watchlist
from movies.mongodb_sync import sync_movie_to_mongodb, sync_review_to_mongodb, sync_user_to_mongodb
from movie_recommender.neo4j_connection import neo4j_conn
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync existing Django data to MongoDB and Neo4j'

    def add_arguments(self, parser):
        parser.add_argument(
            '--movies-only',
            action='store_true',
            help='Sync only movies',
        )
        parser.add_argument(
            '--users-only',
            action='store_true',
            help='Sync only users',
        )
        parser.add_argument(
            '--reviews-only',
            action='store_true',
            help='Sync only reviews',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔄 Début de la synchronisation vers MongoDB et Neo4j...')
        )

        if not any([options['movies_only'], options['users_only'], options['reviews_only']]):
            # Sync everything
            self.sync_users()
            self.sync_movies()
            self.sync_reviews()
            self.sync_watchlists()
        else:
            if options['users_only']:
                self.sync_users()
            if options['movies_only']:
                self.sync_movies()
            if options['reviews_only']:
                self.sync_reviews()

        self.stdout.write(
            self.style.SUCCESS('✅ Synchronisation terminée!')
        )

    def sync_users(self):
        """Sync all users to MongoDB and Neo4j"""
        self.stdout.write('👥 Synchronisation des utilisateurs...')
        
        users = User.objects.all()
        for user in users:
            try:
                # Sync to MongoDB
                sync_user_to_mongodb(user)
                
                # Sync to Neo4j
                neo4j_conn.create_user_node(user.id, user.username)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur pour l\'utilisateur {user.username}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ {users.count()} utilisateurs synchronisés')
        )

    def sync_movies(self):
        """Sync all movies to MongoDB and Neo4j"""
        self.stdout.write('🎬 Synchronisation des films...')
        
        movies = Movie.objects.all()
        for movie in movies:
            try:
                # Sync to MongoDB
                sync_movie_to_mongodb(movie)
                
                # Sync to Neo4j
                genres = [genre.name for genre in movie.genres.all()]
                neo4j_conn.create_movie_node(movie.id, movie.title, genres)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur pour le film {movie.title}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ {movies.count()} films synchronisés')
        )

    def sync_reviews(self):
        """Sync all reviews to MongoDB and Neo4j"""
        self.stdout.write('⭐ Synchronisation des avis...')
        
        reviews = Review.objects.all()
        for review in reviews:
            try:
                # Sync to MongoDB
                sync_review_to_mongodb(review)
                
                # Sync to Neo4j
                neo4j_conn.create_user_rating_relationship(
                    review.user.id, 
                    review.movie.id, 
                    review.rating, 
                    review.comment
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur pour l\'avis de {review.user.username}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ {reviews.count()} avis synchronisés')
        )

    def sync_watchlists(self):
        """Sync all watchlist items to Neo4j"""
        self.stdout.write('📚 Synchronisation des listes de films...')
        
        watchlist_items = Watchlist.objects.all()
        for item in watchlist_items:
            try:
                # Sync to Neo4j
                neo4j_conn.create_user_watchlist_relationship(
                    item.user.id, 
                    item.movie.id
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur pour la liste de {item.user.username}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ {watchlist_items.count()} éléments de liste synchronisés')
        )
