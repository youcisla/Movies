from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from movies.models import Movie, Review
import random

class Command(BaseCommand):
    help = "Crée des reviews de test : chaque utilisateur note un film différent."

    def handle(self, *args, **options):
        users = list(User.objects.all())
        movies = list(Movie.objects.all())
        if not users or not movies:
            self.stdout.write(self.style.ERROR("Aucun utilisateur ou film trouvé."))
            return
        count = 0
        for i, user in enumerate(users):
            movie = movies[i % len(movies)]
            rating = random.randint(3, 5)
            comment = f"Review automatique de {user.username} sur {movie.title}"
            review, created = Review.objects.get_or_create(
                user=user,
                movie=movie,
                defaults={
                    'rating': rating,
                    'comment': comment
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} reviews créées."))
