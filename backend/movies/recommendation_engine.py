"""
Recommendation engine for movie recommendations
Integrates with Neo4j for enhanced recommendations
"""
from .models import Movie, Review, Genre, MovieInteraction
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from collections import defaultdict, Counter
import logging
import math

logger = logging.getLogger(__name__)


def get_recommendations_for_user(user, limit=10, recommendation_type='hybrid'):
    """
    Get personalized recommendations for a user with enhanced intelligence
    Uses content-based filtering, collaborative filtering, and user behavior analysis
    """
    try:
        if recommendation_type == 'content':
            return get_content_based_recommendations(user, limit)
        elif recommendation_type == 'collaborative':
            return get_collaborative_filtering_recommendations(user, limit)
        elif recommendation_type == 'trending':
            return get_trending_movies(limit)
        else:  # hybrid
            return get_hybrid_recommendations(user, limit)
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return get_popular_movies(limit)


def get_content_based_recommendations(user, limit=10):
    """
    Get recommendations based on user's preferences and viewing history
    Analyzes user's favorite genres, ratings, and viewing patterns
    """
    try:
        # Get user's reviews and preferences
        user_reviews = Review.objects.filter(user=user)
        
        if not user_reviews.exists():
            # New user - recommend popular movies from various genres
            return get_diverse_popular_movies(limit)
        
        # Analyze user preferences
        genre_preferences = analyze_user_genre_preferences(user)
        rating_preferences = analyze_user_rating_patterns(user)
        
        # Get candidate movies
        candidate_movies = Movie.objects.exclude(
            id__in=user_reviews.values_list('movie_id', flat=True)
        )
        
        # Score movies based on user preferences
        scored_movies = []
        for movie in candidate_movies:
            score = calculate_content_score(movie, genre_preferences, rating_preferences)
            if score > 0:
                scored_movies.append((movie, score))
        
        # Sort by score and return top recommendations
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        return [movie for movie, score in scored_movies[:limit]]
        
    except Exception as e:
        logger.error(f"Error in content-based recommendations: {e}")
        return get_popular_movies(limit)


def analyze_user_genre_preferences(user):
    """
    Analyze user's genre preferences based on their ratings
    Returns a dictionary with genre preferences weighted by ratings
    """
    genre_scores = defaultdict(float)
    genre_counts = defaultdict(int)
    
    user_reviews = Review.objects.filter(user=user).select_related('movie')
    
    for review in user_reviews:
        movie_genres = review.movie.genres.all()
        rating_weight = review.rating / 5.0  # Normalize rating to 0-1
        
        for genre in movie_genres:
            genre_scores[genre.id] += rating_weight
            genre_counts[genre.id] += 1
    
    # Calculate average preference for each genre
    genre_preferences = {}
    for genre_id, total_score in genre_scores.items():
        genre_preferences[genre_id] = total_score / genre_counts[genre_id]
    
    return genre_preferences


def analyze_user_rating_patterns(user):
    """
    Analyze user's rating patterns to understand their preferences
    """
    user_reviews = Review.objects.filter(user=user)
    
    ratings = [review.rating for review in user_reviews]
    if not ratings:
        return {'avg_rating': 3.0, 'std_rating': 1.0}
    
    avg_rating = sum(ratings) / len(ratings)
    variance = sum((r - avg_rating) ** 2 for r in ratings) / len(ratings)
    std_rating = math.sqrt(variance)
    
    return {
        'avg_rating': avg_rating,
        'std_rating': std_rating,
        'total_reviews': len(ratings)
    }


def calculate_content_score(movie, genre_preferences, rating_preferences):
    """
    Calculate content-based score for a movie based on user preferences
    """
    score = 0.0
    
    # Genre preference score
    movie_genres = movie.genres.all()
    if movie_genres.exists():
        genre_score = 0
        for genre in movie_genres:
            if genre.id in genre_preferences:
                genre_score += genre_preferences[genre.id]
        genre_score /= len(movie_genres)  # Average genre preference
        score += genre_score * 0.4  # 40% weight for genre preference
    
    # Movie quality score (based on vote_average)
    if movie.vote_average > 0:
        quality_score = movie.vote_average / 10.0  # Normalize to 0-1
        score += quality_score * 0.3  # 30% weight for quality
    
    # Popularity boost for well-known movies
    if movie.vote_count > 100:
        popularity_score = min(movie.popularity / 100.0, 1.0)  # Cap at 1.0
        score += popularity_score * 0.2  # 20% weight for popularity
    
    # Recency bonus for newer movies
    if movie.release_date:
        from datetime import datetime, timedelta
        days_since_release = (datetime.now().date() - movie.release_date).days
        if days_since_release < 365:  # Within last year
            recency_score = (365 - days_since_release) / 365.0
            score += recency_score * 0.1  # 10% weight for recency
    
    return score


def get_collaborative_filtering_recommendations(user, limit=10):
    """
    Enhanced collaborative filtering using user similarity
    """
    try:
        # Find users with similar preferences
        similar_users = find_similar_users(user)
        
        if not similar_users:
            return get_content_based_recommendations(user, limit)
        
        # Get movies liked by similar users
        recommended_movies = []
        user_reviewed_movies = set(
            Review.objects.filter(user=user).values_list('movie_id', flat=True)
        )
        
        movie_scores = defaultdict(float)
        
        for similar_user, similarity_score in similar_users:
            similar_user_reviews = Review.objects.filter(
                user=similar_user, rating__gte=4
            ).select_related('movie')
            
            for review in similar_user_reviews:
                if review.movie.id not in user_reviewed_movies:
                    # Score based on similarity and rating
                    score = similarity_score * (review.rating / 5.0)
                    movie_scores[review.movie] += score
        
        # Sort by score
        sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
        return [movie for movie, score in sorted_movies[:limit]]
        
    except Exception as e:
        logger.error(f"Error in collaborative filtering: {e}")
        return get_content_based_recommendations(user, limit)


def find_similar_users(user, limit=10):
    """
    Find users with similar movie preferences using cosine similarity
    """
    user_reviews = Review.objects.filter(user=user)
    if not user_reviews.exists():
        return []
    
    user_movie_ratings = {
        review.movie_id: review.rating 
        for review in user_reviews
    }
    
    # Find other users who have reviewed the same movies
    other_users = User.objects.exclude(id=user.id).filter(
        review__movie_id__in=user_movie_ratings.keys()
    ).distinct()
    
    similar_users = []
    
    for other_user in other_users:
        other_reviews = Review.objects.filter(user=other_user)
        other_movie_ratings = {
            review.movie_id: review.rating 
            for review in other_reviews
        }
        
        # Calculate cosine similarity
        similarity = calculate_cosine_similarity(user_movie_ratings, other_movie_ratings)
        if similarity > 0.1:  # Minimum similarity threshold
            similar_users.append((other_user, similarity))
    
    # Sort by similarity and return top users
    similar_users.sort(key=lambda x: x[1], reverse=True)
    return similar_users[:limit]


def calculate_cosine_similarity(ratings1, ratings2):
    """
    Calculate cosine similarity between two rating vectors
    """
    # Find common movies
    common_movies = set(ratings1.keys()) & set(ratings2.keys())
    
    if len(common_movies) < 2:  # Need at least 2 common movies
        return 0.0
    
    # Calculate cosine similarity
    sum_11 = sum(ratings1[movie] * ratings1[movie] for movie in common_movies)
    sum_22 = sum(ratings2[movie] * ratings2[movie] for movie in common_movies)
    sum_12 = sum(ratings1[movie] * ratings2[movie] for movie in common_movies)
    
    denominator = math.sqrt(sum_11) * math.sqrt(sum_22)
    if denominator == 0:
        return 0.0
    
    return sum_12 / denominator


def get_hybrid_recommendations(user, limit=10):
    """
    Combine content-based and collaborative filtering for better recommendations
    """
    try:
        # Get recommendations from both methods
        content_recs = get_content_based_recommendations(user, limit * 2)
        collaborative_recs = get_collaborative_filtering_recommendations(user, limit * 2)
        
        # Combine and score
        movie_scores = defaultdict(float)
        
        # Weight content-based recommendations
        for i, movie in enumerate(content_recs):
            score = (len(content_recs) - i) / len(content_recs)
            movie_scores[movie] += score * 0.6  # 60% weight for content-based
        
        # Weight collaborative recommendations
        for i, movie in enumerate(collaborative_recs):
            score = (len(collaborative_recs) - i) / len(collaborative_recs)
            movie_scores[movie] += score * 0.4  # 40% weight for collaborative
        
        # Sort and return top recommendations
        sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
        return [movie for movie, score in sorted_movies[:limit]]
        
    except Exception as e:
        logger.error(f"Error in hybrid recommendations: {e}")
        return get_content_based_recommendations(user, limit)


def get_diverse_popular_movies(limit=10):
    """
    Get popular movies from diverse genres for new users
    """
    try:
        genres = Genre.objects.all()
        movies_per_genre = max(1, limit // len(genres))
        
        diverse_movies = []
        for genre in genres:
            genre_movies = Movie.objects.filter(
                genres=genre,
                vote_average__gte=7.0,
                vote_count__gte=100
            ).order_by('-popularity')[:movies_per_genre]
            diverse_movies.extend(genre_movies)
        
        # If we don't have enough, fill with popular movies
        if len(diverse_movies) < limit:
            additional_movies = Movie.objects.exclude(
                id__in=[m.id for m in diverse_movies]
            ).order_by('-popularity')[:limit - len(diverse_movies)]
            diverse_movies.extend(additional_movies)
        
        return diverse_movies[:limit]
        
    except Exception as e:
        logger.error(f"Error getting diverse popular movies: {e}")
        return get_popular_movies(limit)


def get_neo4j_recommendations(user, limit=10):
    """
    Get recommendations from Neo4j graph database
    """
    try:
        from movie_recommender.neo4j_connection import get_neo4j_connection
        
        neo4j_conn = get_neo4j_connection()
        if not neo4j_conn.is_connected:
            return []
        
        # Cypher query to find recommendations based on user similarity
        query = """
        MATCH (u:User {django_id: $user_id})-[:LIKES]->(m:Movie)<-[:LIKES]-(similar_user:User)
        WHERE similar_user <> u
        MATCH (similar_user)-[:LIKES]->(rec_movie:Movie)
        WHERE NOT (u)-[:LIKES]->(rec_movie)
        RETURN rec_movie.django_id as movie_id, COUNT(*) as score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        result = neo4j_conn.run_query(query, {"user_id": user.id, "limit": limit})
        
        if result:
            movie_ids = [record["movie_id"] for record in result]
            # Get Django Movie objects
            movies = Movie.objects.filter(id__in=movie_ids)
            # Order by Neo4j score
            ordered_movies = []
            for movie_id in movie_ids:
                movie = movies.filter(id=movie_id).first()
                if movie:
                    ordered_movies.append(movie)
            return ordered_movies
        
    except Exception as e:
        logger.error(f"Error getting Neo4j recommendations: {e}")
    
    return []


def get_popular_movies(limit=12):
    """
    Get popular movies
    """
    return list(Movie.objects.all().order_by('-popularity', '-vote_average')[:limit])


def get_movies_by_genre(genre_id, limit=20):
    """
    Get movies by genre
    """
    try:
        return list(Movie.objects.filter(
            genres__id=genre_id
        ).order_by('-vote_average', '-popularity')[:limit])
    except Exception as e:
        logger.error(f"Error getting movies by genre: {e}")
        return []


def record_interaction(user, movie, interaction_type):
    """
    Record user interaction with a movie
    Stores in both SQLite and Neo4j
    """
    try:
        # Store in SQLite
        MovieInteraction.objects.create(
            user=user,
            movie=movie,
            interaction_type=interaction_type
        )
        
        # Store in Neo4j if available
        sync_interaction_to_neo4j(user, movie, interaction_type)
        
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")


def sync_interaction_to_neo4j(user, movie, interaction_type):
    """
    Sync interaction to Neo4j
    """
    try:
        from movie_recommender.neo4j_connection import get_neo4j_connection
        
        neo4j_conn = get_neo4j_connection()
        if not neo4j_conn.is_connected:
            return
        
        # Create user and movie nodes if they don't exist
        create_user_query = """
        MERGE (u:User {django_id: $user_id, username: $username})
        """
        
        create_movie_query = """
        MERGE (m:Movie {django_id: $movie_id, title: $title})
        """
        
        neo4j_conn.run_query(create_user_query, {
            "user_id": user.id,
            "username": user.username
        })
        
        neo4j_conn.run_query(create_movie_query, {
            "movie_id": movie.id,
            "title": movie.title
        })
        
        # Create interaction relationship
        if interaction_type == 'view':
            relationship_query = """
            MATCH (u:User {django_id: $user_id})
            MATCH (m:Movie {django_id: $movie_id})
            MERGE (u)-[:VIEWED]->(m)
            """
        else:
            relationship_query = """
            MATCH (u:User {django_id: $user_id})
            MATCH (m:Movie {django_id: $movie_id})
            MERGE (u)-[:INTERACTED {type: $interaction_type}]->(m)
            """
        
        neo4j_conn.run_query(relationship_query, {
            "user_id": user.id,
            "movie_id": movie.id,
            "interaction_type": interaction_type
        })
        
        logger.debug(f"Synced interaction to Neo4j: {user.username} {interaction_type} {movie.title}")
        
    except Exception as e:
        logger.error(f"Error syncing interaction to Neo4j: {e}")


def sync_user_review_to_neo4j(user, movie, rating, comment):
    """
    Sync user review to Neo4j
    """
    try:
        from movie_recommender.neo4j_connection import get_neo4j_connection
        
        neo4j_conn = get_neo4j_connection()
        if not neo4j_conn.is_connected:
            return
        
        # Create user and movie nodes if they don't exist
        create_user_query = """
        MERGE (u:User {django_id: $user_id, username: $username})
        """
        
        create_movie_query = """
        MERGE (m:Movie {django_id: $movie_id, title: $title})
        """
        
        neo4j_conn.run_query(create_user_query, {
            "user_id": user.id,
            "username": user.username
        })
        
        neo4j_conn.run_query(create_movie_query, {
            "movie_id": movie.id,
            "title": movie.title
        })
        
        # Create review relationship
        if rating >= 4:
            # High rating = LIKES relationship
            review_query = """
            MATCH (u:User {django_id: $user_id})
            MATCH (m:Movie {django_id: $movie_id})
            MERGE (u)-[:LIKES {rating: $rating, comment: $comment}]->(m)
            """
        else:
            # Low rating = DISLIKES relationship
            review_query = """
            MATCH (u:User {django_id: $user_id})
            MATCH (m:Movie {django_id: $movie_id})
            MERGE (u)-[:RATED {rating: $rating, comment: $comment}]->(m)
            """
        
        neo4j_conn.run_query(review_query, {
            "user_id": user.id,
            "movie_id": movie.id,
            "rating": rating,
            "comment": comment
        })
        
        logger.debug(f"Synced review to Neo4j: {user.username} rated {movie.title} {rating}/5")
        
    except Exception as e:
        logger.error(f"Error syncing review to Neo4j: {e}")


def sync_user_watchlist_to_neo4j(user, movie):
    """
    Sync user watchlist to Neo4j
    """
    try:
        from movie_recommender.neo4j_connection import get_neo4j_connection
        
        neo4j_conn = get_neo4j_connection()
        if not neo4j_conn.is_connected:
            return
        
        # Create user and movie nodes if they don't exist
        create_user_query = """
        MERGE (u:User {django_id: $user_id, username: $username})
        """
        
        create_movie_query = """
        MERGE (m:Movie {django_id: $movie_id, title: $title})
        """
        
        neo4j_conn.run_query(create_user_query, {
            "user_id": user.id,
            "username": user.username
        })
        
        neo4j_conn.run_query(create_movie_query, {
            "movie_id": movie.id,
            "title": movie.title
        })
        
        # Create watchlist relationship
        watchlist_query = """
        MATCH (u:User {django_id: $user_id})
        MATCH (m:Movie {django_id: $movie_id})
        MERGE (u)-[:WANTS_TO_WATCH]->(m)
        """
        
        neo4j_conn.run_query(watchlist_query, {
            "user_id": user.id,
            "movie_id": movie.id
        })
        
        logger.debug(f"Synced watchlist to Neo4j: {user.username} wants to watch {movie.title}")
        
    except Exception as e:
        logger.error(f"Error syncing watchlist to Neo4j: {e}")


def remove_user_watchlist_from_neo4j(user, movie):
    """
    Supprime la relation WANTS_TO_WATCH dans Neo4j
    """
    try:
        from movie_recommender.neo4j_connection import get_neo4j_connection
        neo4j_conn = get_neo4j_connection()
        if not neo4j_conn.is_connected:
            return
        query = """
        MATCH (u:User {django_id: $user_id})-[r:WANTS_TO_WATCH]->(m:Movie {django_id: $movie_id})
        DELETE r
        """
        neo4j_conn.run_query(query, {
            "user_id": user.id,
            "movie_id": movie.id
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error removing watchlist from Neo4j: {e}")


def get_similar_movies(movie, limit=6):
    """
    Get movies similar to the given movie using intelligent content analysis
    Enhanced with multiple similarity factors
    """
    try:
        # Get Neo4j-based similar movies first
        neo4j_similar = get_neo4j_similar_movies(movie, limit)
        if neo4j_similar:
            return neo4j_similar
        
        # Enhanced content-based similarity
        return get_content_based_similar_movies(movie, limit)
        
    except Exception as e:
        logger.error(f"Error getting similar movies: {e}")
        return []


def get_content_based_similar_movies(movie, limit=6):
    """
    Find similar movies using multiple content factors
    """
    try:
        movie_genres = movie.genres.all()
        if not movie_genres.exists():
            return []
        
        # Get candidate movies from same genres
        candidate_movies = Movie.objects.filter(
            genres__in=movie_genres
        ).exclude(
            id=movie.id
        ).distinct()
        
        # Score each candidate movie
        scored_movies = []
        for candidate in candidate_movies:
            similarity_score = calculate_movie_similarity(movie, candidate)
            if similarity_score > 0:
                scored_movies.append((candidate, similarity_score))
        
        # Sort by similarity score
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        return [movie for movie, score in scored_movies[:limit]]
        
    except Exception as e:
        logger.error(f"Error in content-based similar movies: {e}")
        return []


def calculate_movie_similarity(movie1, movie2):
    """
    Calculate similarity between two movies using multiple factors
    """
    similarity_score = 0.0
    
    # Genre similarity (40% weight)
    genre_similarity = calculate_genre_similarity(movie1, movie2)
    similarity_score += genre_similarity * 0.4
    
    # Rating similarity (20% weight)
    rating_similarity = calculate_rating_similarity(movie1, movie2)
    similarity_score += rating_similarity * 0.2
    
    # Release year similarity (15% weight)
    year_similarity = calculate_year_similarity(movie1, movie2)
    similarity_score += year_similarity * 0.15
    
    # Popularity similarity (15% weight)
    popularity_similarity = calculate_popularity_similarity(movie1, movie2)
    similarity_score += popularity_similarity * 0.15
    
    # Runtime similarity (10% weight)
    runtime_similarity = calculate_runtime_similarity(movie1, movie2)
    similarity_score += runtime_similarity * 0.1
    
    return similarity_score


def calculate_genre_similarity(movie1, movie2):
    """
    Calculate genre overlap between two movies
    """
    genres1 = set(movie1.genres.values_list('id', flat=True))
    genres2 = set(movie2.genres.values_list('id', flat=True))
    
    if not genres1 or not genres2:
        return 0.0
    
    intersection = len(genres1 & genres2)
    union = len(genres1 | genres2)
    
    return intersection / union if union > 0 else 0.0


def calculate_rating_similarity(movie1, movie2):
    """
    Calculate similarity based on movie ratings
    """
    if movie1.vote_average == 0 or movie2.vote_average == 0:
        return 0.0
    
    rating_diff = abs(movie1.vote_average - movie2.vote_average)
    # Convert to similarity (closer ratings = higher similarity)
    return max(0, 1 - (rating_diff / 10.0))


def calculate_year_similarity(movie1, movie2):
    """
    Calculate similarity based on release years
    """
    if not movie1.release_date or not movie2.release_date:
        return 0.0
    
    year_diff = abs(movie1.release_date.year - movie2.release_date.year)
    # Movies within 5 years get high similarity
    if year_diff <= 5:
        return 1.0 - (year_diff / 5.0)
    # Movies within 10 years get moderate similarity
    elif year_diff <= 10:
        return 0.5 - ((year_diff - 5) / 10.0)
    else:
        return 0.0


def calculate_popularity_similarity(movie1, movie2):
    """
    Calculate similarity based on popularity levels
    """
    if movie1.popularity == 0 or movie2.popularity == 0:
        return 0.0
    
    # Use log scale for popularity to reduce impact of extreme values
    pop1 = math.log(movie1.popularity + 1)
    pop2 = math.log(movie2.popularity + 1)
    
    pop_diff = abs(pop1 - pop2)
    max_diff = max(pop1, pop2)
    
    return max(0, 1 - (pop_diff / max_diff)) if max_diff > 0 else 0.0


def calculate_runtime_similarity(movie1, movie2):
    """
    Calculate similarity based on movie runtime
    """
    if not movie1.runtime or not movie2.runtime:
        return 0.0
    
    runtime_diff = abs(movie1.runtime - movie2.runtime)
    # Movies within 30 minutes get high similarity
    if runtime_diff <= 30:
        return 1.0 - (runtime_diff / 30.0)
    # Movies within 60 minutes get moderate similarity
    elif runtime_diff <= 60:
        return 0.5 - ((runtime_diff - 30) / 60.0)
    else:
        return 0.0


def get_neo4j_similar_movies(movie, limit=6):
    """
    Get similar movies from Neo4j based on user behavior patterns
    """
    try:
        from movie_recommender.neo4j_connection import get_neo4j_connection
        
        neo4j_conn = get_neo4j_connection()
        if not neo4j_conn.is_connected:
            return []
        
        # Find movies that users who liked this movie also liked
        query = """
        MATCH (m:Movie {django_id: $movie_id})<-[:LIKES]-(u:User)-[:LIKES]->(similar:Movie)
        WHERE similar <> m
        RETURN similar.django_id as movie_id, COUNT(*) as score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        result = neo4j_conn.run_query(query, {"movie_id": movie.id, "limit": limit})
        
        if result:
            movie_ids = [record["movie_id"] for record in result]
            movies = Movie.objects.filter(id__in=movie_ids)
            # Order by Neo4j score
            ordered_movies = []
            for movie_id in movie_ids:
                similar_movie = movies.filter(id=movie_id).first()
                if similar_movie:
                    ordered_movies.append(similar_movie)
            return ordered_movies
        
    except Exception as e:
        logger.error(f"Error getting Neo4j similar movies: {e}")
    
    return []


def get_trending_movies(limit=20):
    """
    Get trending movies based on recent interactions
    Enhanced with MongoDB analytics
    """
    try:
        # Get MongoDB-based trending movies
        mongodb_trending = get_mongodb_trending_movies(limit)
        if mongodb_trending:
            return mongodb_trending
        
        # Fallback to SQLite-based trending
        trending_movies = Movie.objects.annotate(
            interaction_count=Count('movieinteraction')
        ).order_by('-interaction_count', '-popularity')[:limit]
        
        return list(trending_movies)
    except Exception as e:
        logger.error(f"Error getting trending movies: {e}")
        return get_popular_movies(limit)


def get_mongodb_trending_movies(limit=20):
    """
    Get trending movies from MongoDB analytics
    """
    try:
        from movie_recommender.mongodb_connection import get_interactions_collection
        
        collection = get_interactions_collection()
        if collection is None:
            return []
        
        # Aggregate recent interactions
        pipeline = [
            {"$group": {
                "_id": "$movie_id",
                "interaction_count": {"$sum": 1}
            }},
            {"$sort": {"interaction_count": -1}},
            {"$limit": limit}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        if results:
            movie_ids = [result["_id"] for result in results]
            movies = Movie.objects.filter(id__in=movie_ids)
            # Order by MongoDB aggregation results
            ordered_movies = []
            for result in results:
                movie = movies.filter(id=result["_id"]).first()
                if movie:
                    ordered_movies.append(movie)
            return ordered_movies
        
    except Exception as e:
        logger.error(f"Error getting MongoDB trending movies: {e}")
    
    return []


def analyze_and_update_user_preferences(user, movie, interaction_type='view'):
    """
    Analyze user interaction and update preferences automatically
    This makes the system learn from user behavior
    """
    try:
        from .models import UserPreference
        
        # Get or create user preferences
        user_pref, created = UserPreference.objects.get_or_create(user=user)
        
        if interaction_type in ['view', 'like', 'rate_high']:
            # Add movie genres to favorite genres if user shows positive interaction
            movie_genres = movie.genres.all()
            
            # If user rated highly (4-5 stars) or viewed, add to preferences
            for genre in movie_genres:
                if not user_pref.favorite_genres.filter(id=genre.id).exists():
                    user_pref.favorite_genres.add(genre)
            
            logger.debug(f"Updated preferences for {user.username} based on {movie.title}")
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")


def get_action_movie_recommendations(user, limit=10):
    """
    Specialized recommendations for action movie fans
    If user watched an action movie, recommend similar action movies with intelligent scoring
    """
    try:
        # Get action genre
        action_genre = Genre.objects.filter(name__icontains='Action').first()
        if not action_genre:
            return get_recommendations_for_user(user, limit)
        
        # Get user's rating patterns for action movies
        action_reviews = Review.objects.filter(
            user=user,
            movie__genres=action_genre
        )
        
        if not action_reviews.exists():
            # New to action - recommend popular action movies
            return get_popular_action_movies_for_new_user(limit)
        
        # Analyze what type of action movies user prefers
        avg_action_rating = action_reviews.aggregate(Avg('rating'))['rating__avg']
        
        # Get action movies user hasn't seen
        seen_movies = action_reviews.values_list('movie_id', flat=True)
        candidate_movies = Movie.objects.filter(
            genres=action_genre
        ).exclude(id__in=seen_movies)
        
        # Score action movies based on user's action preferences
        scored_movies = []
        for movie in candidate_movies:
            score = calculate_action_movie_score(movie, user, avg_action_rating)
            if score > 0:
                scored_movies.append((movie, score))
        
        # Sort by score and return recommendations
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        return [movie for movie, score in scored_movies[:limit]]
        
    except Exception as e:
        logger.error(f"Error getting action movie recommendations: {e}")
        return get_recommendations_for_user(user, limit)


def calculate_action_movie_score(movie, user, user_avg_action_rating):
    """
    Calculate score for action movies based on user preferences
    """
    score = 0.0
    
    # Base quality score
    if movie.vote_average >= user_avg_action_rating:
        score += 0.3  # Prefer movies with rating similar to user's taste
    
    # Popularity boost
    if movie.vote_count > 500:  # Well-known action movies
        score += 0.2
    
    # Check for sub-genres that user might like
    user_reviewed_genres = set()
    user_reviews = Review.objects.filter(user=user, rating__gte=4)
    for review in user_reviews:
        user_reviewed_genres.update(review.movie.genres.values_list('name', flat=True))
    
    movie_genres = set(movie.genres.values_list('name', flat=True))
    genre_overlap = len(user_reviewed_genres & movie_genres)
    
    if genre_overlap > 1:  # Multiple genre matches
        score += 0.3
    elif genre_overlap == 1:
        score += 0.15
    
    # Recency bonus for newer action movies
    if movie.release_date:
        from datetime import datetime, timedelta
        days_since_release = (datetime.now().date() - movie.release_date).days
        if days_since_release < 730:  # Within last 2 years
            score += 0.2
    
    return score


def get_popular_action_movies_for_new_user(limit=10):
    """
    Get popular action movies for users new to the action genre
    """
    try:
        action_genre = Genre.objects.filter(name__icontains='Action').first()
        if not action_genre:
            return get_popular_movies(limit)
        
        return list(Movie.objects.filter(
            genres=action_genre,
            vote_average__gte=7.0,
            vote_count__gte=1000
        ).order_by('-vote_average', '-popularity')[:limit])
        
    except Exception as e:
        logger.error(f"Error getting popular action movies: {e}")
        return get_popular_movies(limit)


def get_smart_recommendations_based_on_last_viewed(user, limit=10):
    """
    Get smart recommendations based on the last movie the user viewed
    This is what gets called when a user views any movie
    """
    try:
        # Get user's last viewed movie
        last_interaction = MovieInteraction.objects.filter(
            user=user,
            interaction_type='view'
        ).order_by('-created_at').first()
        
        if not last_interaction:
            return get_recommendations_for_user(user, limit)
        
        last_movie = last_interaction.movie
        
        # Update user preferences based on this viewing
        analyze_and_update_user_preferences(user, last_movie, 'view')
        
        # Check if it's an action movie
        action_genre = Genre.objects.filter(name__icontains='Action').first()
        if action_genre and last_movie.genres.filter(id=action_genre.id).exists():
            # User watched an action movie - get action recommendations
            return get_action_movie_recommendations(user, limit)
        
        # For other genres, use enhanced content-based recommendations
        return get_content_based_recommendations_for_genre(user, last_movie, limit)
        
    except Exception as e:
        logger.error(f"Error getting smart recommendations: {e}")
        return get_recommendations_for_user(user, limit)


def get_content_based_recommendations_for_genre(user, reference_movie, limit=10):
    """
    Get recommendations based on a reference movie's genre and characteristics
    """
    try:
        reference_genres = reference_movie.genres.all()
        if not reference_genres.exists():
            return get_recommendations_for_user(user, limit)
        
        # Get user's reviewed movies to exclude
        reviewed_movies = Review.objects.filter(user=user).values_list('movie_id', flat=True)
        
        # Find movies with similar characteristics
        candidate_movies = Movie.objects.filter(
            genres__in=reference_genres
        ).exclude(
            id__in=reviewed_movies
        ).exclude(
            id=reference_movie.id
        ).distinct()
        
        # Score based on similarity to reference movie
        scored_movies = []
        for movie in candidate_movies:
            similarity_score = calculate_movie_similarity(reference_movie, movie)
            if similarity_score > 0.3:  # Minimum similarity threshold
                scored_movies.append((movie, similarity_score))
        
        # Sort by similarity
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        return [movie for movie, score in scored_movies[:limit]]
        
    except Exception as e:
        logger.error(f"Error getting genre-based recommendations: {e}")
        return get_recommendations_for_user(user, limit)
