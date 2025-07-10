"""
Neo4j-only Movie Recommendation Engine
Intelligent recommendations using graph database relationships
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from movie_recommender.neo4j_connection import get_neo4j_connection

logger = logging.getLogger(__name__)

class Neo4jRecommendationEngine:
    """
    Advanced recommendation engine using only Neo4j graph database
    Provides intelligent, context-aware movie recommendations
    """
    
    def __init__(self):
        self.neo4j = get_neo4j_connection()
        
    def get_recommendations_for_user(self, user_id, limit=10, recommendation_type='smart'):
        """
        Get personalized recommendations with high intelligence
        
        Types:
        - 'smart': Automatically chooses best strategy based on user profile
        - 'action': Specialized action movie recommendations
        - 'collaborative': Based on similar users
        - 'content': Based on movie characteristics
        - 'trending': Popular and recent movies
        """
        if not self.neo4j.is_connected:
            self.neo4j.connect()
            
        if recommendation_type == 'smart':
            return self._get_smart_recommendations(user_id, limit)
        elif recommendation_type == 'action':
            return self._get_action_recommendations(user_id, limit)
        elif recommendation_type == 'collaborative':
            return self._get_collaborative_recommendations(user_id, limit)
        elif recommendation_type == 'content':
            return self._get_content_based_recommendations(user_id, limit)
        elif recommendation_type == 'trending':
            return self._get_trending_recommendations(user_id, limit)
        else:
            return self._get_hybrid_recommendations(user_id, limit)
    
    def _get_smart_recommendations(self, user_id, limit=10):
        """
        Smart recommendations - analyzes user behavior and chooses best strategy
        """
        # Analyze user profile
        user_profile = self._analyze_user_profile(user_id)
        
        if user_profile['total_ratings'] == 0:
            return self._get_diverse_popular_movies(limit)
        elif user_profile['action_preference'] > 0.3:
            return self._get_action_recommendations(user_id, limit)
        elif user_profile['total_ratings'] < 5:
            return self._get_trending_recommendations(user_id, limit)
        else:
            return self._get_hybrid_recommendations(user_id, limit)
    
    def _get_action_recommendations(self, user_id, limit=10):
        """
        Specialized action movie recommendations with high intelligence
        """
        # Check if user has watched action movies
        user_action_history = self._get_user_action_history(user_id)
        
        if not user_action_history:
            return self._get_popular_action_movies(limit)
        
        # Experienced action movie watcher - intelligent scoring
        query = """
        // Get user's action movie preferences
        MATCH (u:User {id: $user_id})-[r:RATED]->(m:Movie)
        WHERE 'Action' IN m.genres AND r.rating >= 4
        WITH u, collect(m) as liked_action_movies, avg(r.rating) as avg_action_rating
        
        // Find action movies user hasn't seen
        MATCH (candidate:Movie)
        WHERE 'Action' IN candidate.genres 
        AND NOT EXISTS((u)-[:RATED]->(candidate))
        AND NOT EXISTS((u)-[:WANTS_TO_WATCH]->(candidate))
        AND candidate.vote_average >= 6.0
        AND candidate.vote_count >= 100
        
        // Calculate intelligent score
        WITH u, candidate, avg_action_rating, liked_action_movies,
             // Quality score (30%)
             (candidate.vote_average / 10.0) * 0.3 as quality_score,
             // Popularity score (20%)
             (candidate.popularity / 100.0) * 0.2 as popularity_score,
             // Genre diversity score (30%) - bonus for action + other genres user likes
             size([g IN candidate.genres WHERE g IN [g2 IN liked_movie.genres WHERE liked_movie IN liked_action_movies | g2]]) * 0.05 as genre_score,
             // Recency bonus (20%) - newer movies get bonus
             CASE 
               WHEN candidate.release_date > date() - duration({years: 2}) THEN 0.2
               WHEN candidate.release_date > date() - duration({years: 5}) THEN 0.1
               ELSE 0.0
             END as recency_score
        
        WITH candidate, 
             quality_score + popularity_score + genre_score + recency_score as final_score
        
        RETURN candidate.id as movie_id, 
               candidate.title as title,
               candidate.genres as genres,
               candidate.vote_average as rating,
               candidate.release_date as release_date,
               final_score
        ORDER BY final_score DESC
        LIMIT $limit
        """
        
        result = self.neo4j.run_query(query, {"user_id": user_id, "limit": limit})
        return self._format_movie_results(result)
    
    def _get_collaborative_recommendations(self, user_id, limit=10):
        """
        Advanced collaborative filtering using graph relationships
        """
        query = """
        // Find users with similar taste (Jaccard similarity)
        MATCH (u:User {id: $user_id})-[r1:RATED]->(m:Movie)
        WHERE r1.rating >= 4
        WITH u, collect(m) as user_liked_movies
        
        MATCH (other:User)-[r2:RATED]->(m2:Movie)
        WHERE other <> u AND r2.rating >= 4 AND m2 IN user_liked_movies
        WITH u, user_liked_movies, other, collect(m2) as common_movies
        WHERE size(common_movies) >= 2
        
        MATCH (other)-[r3:RATED]->(all_other_movies:Movie)
        WHERE r3.rating >= 4
        WITH u, user_liked_movies, other, common_movies, collect(all_other_movies) as other_liked_movies
        
        // Calculate Jaccard similarity
        WITH u, user_liked_movies, other,
             toFloat(size(common_movies)) / size(user_liked_movies + [m IN other_liked_movies WHERE NOT m IN user_liked_movies]) as similarity
        WHERE similarity > 0.1
        ORDER BY similarity DESC
        LIMIT 10
        
        // Get recommendations from similar users
        MATCH (other)-[r:RATED]->(rec:Movie)
        WHERE r.rating >= 4 
        AND NOT EXISTS((u)-[:RATED]->(rec))
        AND NOT EXISTS((u)-[:WANTS_TO_WATCH]->(rec))
        
        WITH rec, count(other) as recommendation_count, avg(r.rating) as avg_rating
        ORDER BY recommendation_count DESC, avg_rating DESC
        
        RETURN rec.id as movie_id,
               rec.title as title,
               rec.genres as genres,
               rec.vote_average as rating,
               recommendation_count,
               avg_rating
        LIMIT $limit
        """
        
        result = self.neo4j.run_query(query, {"user_id": user_id, "limit": limit})
        return self._format_movie_results(result)
    
    def _get_content_based_recommendations(self, user_id, limit=10):
        """
        Content-based recommendations using movie characteristics
        """
        query = """
        // Analyze user preferences
        MATCH (u:User {id: $user_id})-[r:RATED]->(m:Movie)
        WHERE r.rating >= 4
        WITH u, 
             [g IN collect(m.genres) WHERE g IS NOT NULL | g] as all_genres,
             avg(r.rating) as user_avg_rating,
             avg(m.vote_average) as preferred_quality
        
        // Calculate genre preferences
        UNWIND all_genres as genre_list
        UNWIND genre_list as genre
        WITH u, user_avg_rating, preferred_quality, genre, count(genre) as genre_count
        ORDER BY genre_count DESC
        WITH u, user_avg_rating, preferred_quality, collect({genre: genre, count: genre_count}) as genre_preferences
        
        // Find candidate movies
        MATCH (candidate:Movie)
        WHERE NOT EXISTS((u)-[:RATED]->(candidate))
        AND NOT EXISTS((u)-[:WANTS_TO_WATCH]->(candidate))
        AND candidate.vote_average >= (preferred_quality * 0.8)
        
        // Score based on genre preferences
        WITH u, candidate, genre_preferences, user_avg_rating,
             [gp IN genre_preferences WHERE gp.genre IN candidate.genres | gp.count] as matching_genre_scores
        
        WITH candidate,
             // Genre match score (40%)
             (reduce(s = 0, score IN matching_genre_scores | s + score) / 10.0) * 0.4 as genre_score,
             // Quality score (35%)
             (candidate.vote_average / 10.0) * 0.35 as quality_score,
             // Popularity score (25%)
             (log(candidate.popularity + 1) / 10.0) * 0.25 as popularity_score
        
        WITH candidate, genre_score + quality_score + popularity_score as final_score
        WHERE final_score > 0.1
        
        RETURN candidate.id as movie_id,
               candidate.title as title,
               candidate.genres as genres,
               candidate.vote_average as rating,
               final_score
        ORDER BY final_score DESC
        LIMIT $limit
        """
        
        result = self.neo4j.run_query(query, {"user_id": user_id, "limit": limit})
        return self._format_movie_results(result)
    
    def _get_trending_recommendations(self, user_id, limit=10):
        """
        Get trending and popular movies user hasn't seen
        """
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (trending:Movie)
        WHERE NOT EXISTS((u)-[:RATED]->(trending))
        AND NOT EXISTS((u)-[:WANTS_TO_WATCH]->(trending))
        AND trending.vote_average >= 7.0
        AND trending.vote_count >= 500
        AND trending.release_date >= date() - duration({years: 3})
        
        WITH trending,
             (trending.vote_average / 10.0) * 0.4 as quality_score,
             (trending.popularity / 100.0) * 0.4 as popularity_score,
             CASE 
               WHEN trending.release_date >= date() - duration({months: 6}) THEN 0.2
               WHEN trending.release_date >= date() - duration({years: 1}) THEN 0.15
               ELSE 0.1
             END as recency_score
        
        WITH trending, quality_score + popularity_score + recency_score as final_score
        
        RETURN trending.id as movie_id,
               trending.title as title,
               trending.genres as genres,
               trending.vote_average as rating,
               trending.release_date as release_date,
               final_score
        ORDER BY final_score DESC
        LIMIT $limit
        """
        
        result = self.neo4j.run_query(query, {"user_id": user_id, "limit": limit})
        return self._format_movie_results(result)
    
    def _get_hybrid_recommendations(self, user_id, limit=10):
        """
        Combine multiple recommendation strategies
        """
        # Get recommendations from different strategies
        collaborative = self._get_collaborative_recommendations(user_id, limit)
        content_based = self._get_content_based_recommendations(user_id, limit)
        trending = self._get_trending_recommendations(user_id, limit // 3)
        
        # Combine and diversify
        movie_scores = defaultdict(float)
        
        # Weight collaborative filtering (40%)
        for i, movie in enumerate(collaborative):
            score = (limit - i) / limit * 0.4
            movie_scores[movie['movie_id']] += score
        
        # Weight content-based (40%)
        for i, movie in enumerate(content_based):
            score = (limit - i) / limit * 0.4
            movie_scores[movie['movie_id']] += score
        
        # Weight trending (20%)
        for i, movie in enumerate(trending):
            score = (limit - i) / limit * 0.2
            movie_scores[movie['movie_id']] += score
        
        # Sort by combined score and return top results
        sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get movie details for top scored movies
        top_movie_ids = [movie_id for movie_id, score in sorted_movies[:limit]]
        
        if not top_movie_ids:
            return self._get_diverse_popular_movies(limit)
        
        # Fetch movie details
        query = """
        MATCH (m:Movie)
        WHERE m.id IN $movie_ids
        RETURN m.id as movie_id,
               m.title as title,
               m.genres as genres,
               m.vote_average as rating,
               m.release_date as release_date
        """
        
        result = self.neo4j.run_query(query, {"movie_ids": top_movie_ids})
        return self._format_movie_results(result)
    
    def _analyze_user_profile(self, user_id):
        """
        Analyze user's viewing preferences and behavior
        """
        query = """
        MATCH (u:User {id: $user_id})
        OPTIONAL MATCH (u)-[r:RATED]->(m:Movie)
        
        WITH u, collect(r) as ratings, collect(m) as rated_movies
        
        UNWIND rated_movies as movie
        UNWIND movie.genres as genre
        
        WITH u, ratings, 
             count(CASE WHEN genre = 'Action' THEN 1 END) as action_count,
             count(genre) as total_genre_count,
             size(ratings) as total_ratings,
             avg([rating IN ratings | rating.rating]) as avg_rating
        
        RETURN {
            total_ratings: total_ratings,
            avg_rating: coalesce(avg_rating, 0.0),
            action_preference: toFloat(action_count) / CASE WHEN total_genre_count > 0 THEN total_genre_count ELSE 1 END
        } as profile
        """
        
        result = self.neo4j.run_query(query, {"user_id": user_id})
        if result:
            return result[0]['profile']
        else:
            return {'total_ratings': 0, 'avg_rating': 0.0, 'action_preference': 0.0}
    
    def _get_user_action_history(self, user_id):
        """
        Get user's action movie viewing history
        """
        query = """
        MATCH (u:User {id: $user_id})-[r:RATED]->(m:Movie)
        WHERE 'Action' IN m.genres
        RETURN count(m) as action_movies_count
        """
        
        result = self.neo4j.run_query(query, {"user_id": user_id})
        return result[0]['action_movies_count'] if result else 0
    
    def _get_popular_action_movies(self, limit=10):
        """
        Get popular action movies for new users
        """
        query = """
        MATCH (m:Movie)
        WHERE 'Action' IN m.genres 
        AND m.vote_average >= 7.0
        AND m.vote_count >= 1000
        
        RETURN m.id as movie_id,
               m.title as title,
               m.genres as genres,
               m.vote_average as rating,
               m.popularity as popularity
        ORDER BY m.vote_average DESC, m.popularity DESC
        LIMIT $limit
        """
        
        result = self.neo4j.run_query(query, {"limit": limit})
        return self._format_movie_results(result)
    
    def _get_diverse_popular_movies(self, limit=10):
        """
        Get diverse popular movies from different genres
        """
        query = """
        // Get top movies from each major genre
        UNWIND ['Action', 'Comedy', 'Drama', 'Thriller', 'Horror', 'Romance', 'Science Fiction', 'Adventure'] as genre
        MATCH (m:Movie)
        WHERE genre IN m.genres 
        AND m.vote_average >= 7.0
        AND m.vote_count >= 500
        
        WITH genre, m
        ORDER BY m.vote_average DESC, m.popularity DESC
        WITH genre, collect(m)[0..2] as top_movies
        
        UNWIND top_movies as movie
        RETURN DISTINCT movie.id as movie_id,
               movie.title as title,
               movie.genres as genres,
               movie.vote_average as rating
        ORDER BY movie.vote_average DESC
        LIMIT $limit
        """
        
        result = self.neo4j.run_query(query, {"limit": limit})
        return self._format_movie_results(result)
    
    def _format_movie_results(self, neo4j_result):
        """
        Format Neo4j query results into standardized movie data
        """
        movies = []
        for record in neo4j_result:
            movie = {
                'movie_id': record.get('movie_id'),
                'title': record.get('title', 'Unknown Title'),
                'genres': record.get('genres', []),
                'rating': record.get('rating', 0.0),
                'release_date': record.get('release_date'),
                'overview': record.get('overview', ''),
                'popularity': record.get('popularity', 0.0)
            }
            movies.append(movie)
        return movies
    
    def record_user_interaction(self, user_id, movie_id, interaction_type, rating=None, comment=None):
        """
        Record user interaction with a movie
        """
        if interaction_type == 'rating':
            return self._record_rating(user_id, movie_id, rating, comment)
        elif interaction_type == 'watchlist':
            return self._record_watchlist(user_id, movie_id)
        elif interaction_type == 'view':
            return self._record_view(user_id, movie_id)
        elif interaction_type == 'like':
            return self._record_like(user_id, movie_id)
    
    def _record_view(self, user_id, movie_id):
        """Record that user viewed a movie"""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (m:Movie {id: $movie_id})
        MERGE (u)-[r:VIEWED]->(m)
        SET r.timestamp = datetime()
        RETURN r
        """
        return self.neo4j.run_query(query, {"user_id": user_id, "movie_id": movie_id})
    
    def _record_rating(self, user_id, movie_id, rating, comment=None):
        """Record user rating for a movie"""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (m:Movie {id: $movie_id})
        MERGE (u)-[r:RATED]->(m)
        SET r.rating = $rating,
            r.timestamp = datetime()
        """
        
        params = {"user_id": user_id, "movie_id": movie_id, "rating": rating}
        
        if comment:
            query += ", r.comment = $comment"
            params["comment"] = comment
            
        query += " RETURN r"
        
        return self.neo4j.run_query(query, params)
    
    def _record_watchlist(self, user_id, movie_id):
        """Record that user added movie to watchlist"""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (m:Movie {id: $movie_id})
        MERGE (u)-[r:WANTS_TO_WATCH]->(m)
        SET r.added_at = datetime()
        RETURN r
        """
        return self.neo4j.run_query(query, {"user_id": user_id, "movie_id": movie_id})
    
    def _record_like(self, user_id, movie_id):
        """Record that user liked a movie"""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (m:Movie {id: $movie_id})
        MERGE (u)-[r:LIKES]->(m)
        SET r.timestamp = datetime()
        RETURN r
        """
        return self.neo4j.run_query(query, {"user_id": user_id, "movie_id": movie_id})

# Global instance
neo4j_engine = Neo4jRecommendationEngine()
