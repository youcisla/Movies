from django.contrib import admin
from .models import Movie, Genre, Review, UserPreference, Watchlist, MovieInteraction


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
        ('Basic Information', {
            'fields': ('title', 'original_title', 'overview', 'release_date', 'runtime')
        }),
        ('TMDb Data', {
            'fields': ('tmdb_id', 'poster_path', 'backdrop_path', 'vote_average', 'vote_count', 'popularity')
        }),
        ('Relations', {
            'fields': ('genres',)
        }),
        ('Metadata', {
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


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    filter_horizontal = ('favorite_genres',)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'movie__title')
    ordering = ('-added_at',)


@admin.register(MovieInteraction)
class MovieInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'interaction_type', 'timestamp')
    list_filter = ('interaction_type', 'timestamp')
    search_fields = ('user__username', 'movie__title')
    ordering = ('-timestamp',)


# Customize admin site
admin.site.site_header = "Movie Recommender Admin"
admin.site.site_title = "Movie Recommender"
admin.site.index_title = "Administration Dashboard"
