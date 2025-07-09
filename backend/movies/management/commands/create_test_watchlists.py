from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from movies.models import Movie, Watchlist
import random

class Command(BaseCommand):
    help = "Crée des watchlists de test : chaque utilisateur ajoute un film différent à sa watchlist."

    def handle(self, *args, **options):
        users = list(User.objects.all())
        movies = list(Movie.objects.all())
        if not users or not movies:
            self.stdout.write(self.style.ERROR("Aucun utilisateur ou film trouvé."))
            return
        count = 0
        for i, user in enumerate(users):
            print(f"Traitement user {user.username}")  # Debug étape 5
            movie = movies[(i + 1) % len(movies)]  # Décalage pour ne pas prendre le même que la review
            watchlist, created = Watchlist.objects.get_or_create(
                user=user,
                movie=movie
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} watchlists créées."))
