from django.contrib import admin
from .models import Movie, Review, Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'tmdb_id')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year', 'vote_average', 'popularity', 'created_at')
    list_filter = ('genres', 'release_date', 'created_at')
    search_fields = ('title', 'original_title', 'overview')
    filter_horizontal = ('genres',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'original_title', 'overview', 'release_date', 'runtime')
        }),
        ('TMDb', {
            'fields': ('tmdb_id', 'poster_path', 'backdrop_path', 'vote_average', 'vote_count', 'popularity')
        }),
        ('Relations', {
            'fields': ('genres',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'movie__title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Avis', {
            'fields': ('user', 'movie', 'rating', 'comment')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Personnalisation du site admin
admin.site.site_header = "Movie Recommender Admin"
admin.site.site_title = "Movie Recommender"
admin.site.index_title = "Administration du système de recommandation"
