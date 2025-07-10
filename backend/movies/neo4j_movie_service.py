"""
Neo4j Movie Data Service
Manages movie data s        params = {
            'movie_id': movie_data.get('id'),
            'title': movie_data.get('title', ''),
            'overview': movie_data.get('overview', ''),
            'release_date': movie_data.get('release_date', '1900-01-01'),
            'vote_average': movie_data.get('vote_average', 0.0),
            'vote_count': movie_data.get('vote_count', 0),
            'popularity': movie_data.get('popularity', 0.0),
            'runtime': movie_data.get('runtime', 0),
            'budget': movie_data.get('budget', 0),
            'revenue': movie_data.get('revenue', 0),
            'poster_path': movie_data.get('poster_path', ''),
            'backdrop_path': movie_data.get('backdrop_path', ''),
            'genres': movie_data.get('genres', []),
            'keywords': movie_data.get('keywords', []),
            'cast': movie_data.get('cast', [])[:10],
            'director': movie_data.get('director', '')
        }nd operations in Neo4j
"""
import logging
from movie_recommender.neo4j_connection import get_neo4j_connection

logger = logging.getLogger(__name__)

class Neo4jMovieService:
    """
    Service for managing movie data in Neo4j
    """
    
    def __init__(self):
        self.neo4j = get_neo4j_connection()
    
    def create_or_update_movie(self, movie_data):
        """
        Create or update a movie node in Neo4j
        """
        query = """
        MERGE (m:Movie {id: $movie_id})
        SET m.title = $title,
            m.overview = $overview,
            m.release_date = date($release_date),
            m.vote_average = $vote_average,
            m.vote_count = $vote_count,
            m.popularity = $popularity,
            m.runtime = $runtime,
            m.budget = $budget,
            m.revenue = $revenue,
            m.poster_path = $poster_path,
            m.backdrop_path = $backdrop_path,
            m.genres = $genres,
            m.keywords = $keywords,
            m.cast = $cast,
            m.director = $director,
            m.updated_at = datetime()
        
        // Create genre relationships
        WITH m
        UNWIND $genres as genre_name
        MERGE (g:Genre {name: genre_name})
        MERGE (m)-[:HAS_GENRE]->(g)
        
        RETURN m
        """
        
        params = {
            'movie_id': movie_data.get('id'),
            'title': movie_data.get('title', ''),
            'overview': movie_data.get('overview', ''),
            'release_date': movie_data.get('release_date', '1900-01-01'),
            'vote_average': movie_data.get('vote_average', 0.0),
            'vote_count': movie_data.get('vote_count', 0),
            'popularity': movie_data.get('popularity', 0.0),
            'runtime': movie_data.get('runtime', 0),
            'budget': movie_data.get('budget', 0),
            'revenue': movie_data.get('revenue', 0),
            'genres': movie_data.get('genres', []),
            'keywords': movie_data.get('keywords', []),
            'cast': movie_data.get('cast', [])[:10],  # Top 10 cast members
            'director': movie_data.get('director', '')
        }
        
        return self.neo4j.run_query(query, params)
    
    def create_or_update_user(self, user_data):
        """
        Create or update a user node in Neo4j
        """
        query = """
        MERGE (u:User {id: $user_id})
        SET u.username = $username,
            u.email = $email,
            u.first_name = $first_name,
            u.last_name = $last_name,
            u.date_joined = datetime($date_joined),
            u.is_active = $is_active,
            u.updated_at = datetime()
        RETURN u
        """
        
        params = {
            'user_id': user_data.get('id'),
            'username': user_data.get('username', ''),
            'email': user_data.get('email', ''),
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'date_joined': user_data.get('date_joined', ''),
            'is_active': user_data.get('is_active', True)
        }
        
        return self.neo4j.run_query(query, params)
    
    def get_movie_by_id(self, movie_id):
        """
        Get movie details from Neo4j
        """
        query = """
        MATCH (m:Movie {id: $movie_id})
        OPTIONAL MATCH (m)-[:HAS_GENRE]->(g:Genre)
        RETURN m,
               collect(g.name) as genres
        """
        
        result = self.neo4j.run_query(query, {"movie_id": movie_id})
        if result:
            record = result[0]
            movie = dict(record['m'])
            movie['genres'] = record['genres']
            return movie
        return None
    
    def search_movies(self, query_text, limit=20):
        """
        Search movies by title or genre
        """
        query = """
        MATCH (m:Movie)
        WHERE toLower(m.title) CONTAINS toLower($query_text)
        OR any(genre IN m.genres WHERE toLower(genre) CONTAINS toLower($query_text))
        
        RETURN m.id as movie_id,
               m.title as title,
               m.genres as genres,
               m.vote_average as rating,
               m.release_date as release_date,
               m.overview as overview,
               m.poster_path as poster_path
        ORDER BY m.vote_average DESC, m.popularity DESC
        LIMIT $limit
        """
        
        return self.neo4j.run_query(query, {"query_text": query_text, "limit": limit})
    
    def get_movies_by_genre(self, genre_name, limit=20):
        """
        Get movies by specific genre
        """
        query = """
        MATCH (m:Movie)
        WHERE $genre_name IN m.genres
        AND m.vote_average >= 6.0
        
        RETURN m.id as movie_id,
               m.title as title,
               m.genres as genres,
               m.vote_average as rating,
               m.release_date as release_date,
               m.overview as overview,
               m.poster_path as poster_path
        ORDER BY m.vote_average DESC, m.popularity DESC
        LIMIT $limit
        """
        
        return self.neo4j.run_query(query, {"genre_name": genre_name, "limit": limit})
    
    def get_popular_movies(self, limit=20):
        """
        Get popular movies
        """
        query = """
        MATCH (m:Movie)
        WHERE m.vote_average >= 7.0
        AND m.vote_count >= 500
        
        RETURN m.id as movie_id,
               m.title as title,
               m.genres as genres,
               m.vote_average as rating,
               m.release_date as release_date,
               m.overview as overview,
               m.popularity as popularity,
               m.poster_path as poster_path,
               m.backdrop_path as backdrop_path
        ORDER BY m.popularity DESC, m.vote_average DESC
        LIMIT $limit
        """
        
        return self.neo4j.run_query(query, {"limit": limit})
    
    def get_user_watchlist(self, user_id):
        """
        Get user's watchlist
        """
        query = """
        MATCH (u:User {id: $user_id})-[r:WANTS_TO_WATCH]->(m:Movie)
        RETURN m.id as movie_id,
               m.title as title,
               m.genres as genres,
               m.vote_average as rating,
               r.added_at as added_at
        ORDER BY r.added_at DESC
        """
        
        return self.neo4j.run_query(query, {"user_id": user_id})
    
    def get_user_ratings(self, user_id):
        """
        Get user's movie ratings
        """
        query = """
        MATCH (u:User {id: $user_id})-[r:RATED]->(m:Movie)
        RETURN m.id as movie_id,
               m.title as title,
               m.genres as genres,
               r.rating as user_rating,
               r.comment as comment,
               r.timestamp as rated_at
        ORDER BY r.timestamp DESC
        """
        
        return self.neo4j.run_query(query, {"user_id": user_id})
    
    def get_similar_movies(self, movie_id, limit=6):
        """
        Get movies similar to a given movie
        """
        query = """
        MATCH (m:Movie {id: $movie_id})
        MATCH (similar:Movie)
        WHERE m <> similar
        
        // Calculate similarity based on genres, cast, director
        WITH m, similar,
             // Genre similarity
             size([g IN m.genres WHERE g IN similar.genres]) as common_genres,
             // Cast similarity  
             size([c IN m.cast WHERE c IN similar.cast]) as common_cast,
             // Director similarity
             CASE WHEN m.director = similar.director AND m.director <> '' THEN 1 ELSE 0 END as same_director
        
        WITH similar, 
             (common_genres * 0.4 + common_cast * 0.3 + same_director * 0.3) as similarity_score
        WHERE similarity_score > 0.1
        
        RETURN similar.id as movie_id,
               similar.title as title,
               similar.genres as genres,
               similar.vote_average as rating,
               similarity_score
        ORDER BY similarity_score DESC
        LIMIT $limit
        """
        
        return self.neo4j.run_query(query, {"movie_id": movie_id, "limit": limit})
    
    def get_trending_movies(self, days=30, limit=20):
        """
        Get trending movies based on recent interactions
        """
        query = """
        MATCH (u:User)-[r:RATED|VIEWED|LIKES]->(m:Movie)
        WHERE r.timestamp >= datetime() - duration({days: $days})
        
        WITH m, count(r) as interaction_count, avg(CASE WHEN r.rating IS NOT NULL THEN r.rating ELSE 5.0 END) as avg_rating
        WHERE interaction_count >= 3
        
        RETURN m.id as movie_id,
               m.title as title,
               m.genres as genres,
               m.vote_average as rating,
               m.release_date as release_date,
               interaction_count,
               avg_rating
        ORDER BY interaction_count DESC, avg_rating DESC
        LIMIT $limit
        """
        
        return self.neo4j.run_query(query, {"days": days, "limit": limit})
    
    def get_genre_statistics(self):
        """
        Get statistics about genres
        """
        query = """
        MATCH (m:Movie)
        UNWIND m.genres as genre
        WITH genre, count(m) as movie_count, avg(m.vote_average) as avg_rating
        WHERE movie_count >= 10
        RETURN genre,
               movie_count,
               avg_rating
        ORDER BY movie_count DESC
        """
        
        return self.neo4j.run_query(query)
    
    def cleanup_duplicate_movies(self):
        """
        Clean up duplicate movie entries
        """
        query = """
        MATCH (m1:Movie), (m2:Movie)
        WHERE m1.id < m2.id 
        AND m1.title = m2.title 
        AND m1.release_date = m2.release_date
        
        // Merge relationships from m2 to m1
        OPTIONAL MATCH (u:User)-[r]->(m2)
        FOREACH(rel IN CASE WHEN r IS NOT NULL THEN [r] ELSE [] END |
            MERGE (u)-[new_rel:RATED]->(m1)
            SET new_rel = properties(rel)
            DELETE rel
        )
        
        // Delete duplicate movie
        DETACH DELETE m2
        
        RETURN count(*) as duplicates_removed
        """
        
        return self.neo4j.run_query(query)

# Global instance
neo4j_movie_service = Neo4jMovieService()
