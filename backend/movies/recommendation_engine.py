"""
Recommendation engine for movie recommendations
Integrates with MongoDB and Neo4j for enhanced recommendations
"""
from .models import Movie, Review, Genre, MovieInteraction
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
import logging

logger = logging.getLogger(__name__)


def get_recommendations_for_user(user, limit=10, recommendation_type='hybrid'):
    """
    Get personalized recommendations for a user
    Uses both MongoDB and Neo4j when available
    """
    try:
        # Fetch recommendations from Neo4j
        from movie_recommender.neo4j_connection import get_neo4j_connection
        
        neo4j_conn = get_neo4j_connection()
        if neo4j_conn.is_connected:
            neo4j_recommendations = neo4j_conn.get_user_recommendations(user.id, limit)
            if neo4j_recommendations:
                return neo4j_recommendations

        # Fallback to MongoDB
        from movie_recommender.mongodb_connection import get_mongodb_connection
        
        mongodb_conn = get_mongodb_connection()
        if mongodb_conn.is_connected:
            movies_collection = mongodb_conn.get_collection('movies')
            if movies_collection:
                return list(movies_collection.find().limit(limit))

        # Fallback to SQLite
        return get_popular_movies(limit)
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
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
    Stores in both SQLite and MongoDB
    """
    try:
        # Store in SQLite
        MovieInteraction.objects.create(
            user=user,
            movie=movie,
            interaction_type=interaction_type
        )
        
        # Store in MongoDB if available
        sync_interaction_to_mongodb(user, movie, interaction_type)
        
        # Store in Neo4j if available
        sync_interaction_to_neo4j(user, movie, interaction_type)
        
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")


def sync_interaction_to_mongodb(user, movie, interaction_type):
    """
    Sync interaction to MongoDB
    """
    try:
        from movie_recommender.mongodb_connection import get_interactions_collection
        
        collection = get_interactions_collection()
        if collection is None:
            return
        
        interaction_doc = {
            'user_id': user.id,
            'movie_id': movie.id,
            'interaction_type': interaction_type,
            'timestamp': user.last_login or user.date_joined
        }
        
        collection.insert_one(interaction_doc)
        logger.debug(f"Synced interaction to MongoDB: {user.username} {interaction_type} {movie.title}")
        
    except Exception as e:
        logger.error(f"Error syncing interaction to MongoDB: {e}")


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


def get_similar_movies(movie, limit=6):
    """
    Get movies similar to the given movie based on genres
    Enhanced with Neo4j graph-based similarity
    """
    try:
        # Get Neo4j-based similar movies first
        neo4j_similar = get_neo4j_similar_movies(movie, limit)
        if neo4j_similar:
            return neo4j_similar
        
        # Fallback to genre-based similarity
        movie_genres = movie.genres.all()
        if not movie_genres.exists():
            return []
        
        similar_movies = Movie.objects.filter(
            genres__in=movie_genres
        ).exclude(
            id=movie.id
        ).distinct().order_by('-vote_average', '-popularity')[:limit]
        
        return list(similar_movies)
    except Exception as e:
        logger.error(f"Error getting similar movies: {e}")
        return []


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
