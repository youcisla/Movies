from django.db import models

# Modèle pour les films
class Movie(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    release_year = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return self.title

# Modèle pour les avis des utilisateurs
class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=255)
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    comment = models.TextField()

    def __str__(self):
        return f'Review for {self.movie.title} by {self.user_name}'
