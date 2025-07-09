"""
Neo4j connection and utilities for the Movie Recommendation System
"""
from neo4j import GraphDatabase
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jConnection:
    """Neo4j connection manager"""
    
    def __init__(self):
        self.driver = None
        self.is_connected = False
        self._connection_attempted = False
    
    def connect(self):
        """Connect to Neo4j"""
        if self._connection_attempted:
            return

        self._connection_attempted = True
        try:
            # Only try to connect if Neo4j settings are properly configured
            neo4j_uri = settings.NEO4J_URI
            neo4j_username = settings.NEO4J_USERNAME
            neo4j_password = settings.NEO4J_PASSWORD

            if not all([neo4j_uri, neo4j_username, neo4j_password]):
                raise ValueError("Neo4j connection settings are not properly configured.")

            self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
            try:
                # Ensure the database is initialized by creating a simple node
                with self.driver.session() as session:
                    session.run("CREATE CONSTRAINT IF NOT EXISTS ON (n:MovieRec) ASSERT n.id IS UNIQUE")
                self.is_connected = True
                logger.info("✅ Connected to Neo4j and initialized 'movierec' database.")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Neo4j database: {e}")
                self.is_connected = False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            self.is_connected = False
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def run_query(self, query, parameters=None):
        """Run a Cypher query"""
        if not self._connection_attempted:
            self.connect()
            
        if not self.is_connected:
            logger.warning("⚠️ Neo4j not connected. Cannot run query.")
            return []
            
        try:
            with self.driver.session(database="movierec") as session:
                result = session.run(query, parameters or {})
                return [record for record in result]
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return []
    
    def create_user_node(self, user_id, username):
        """Create a user node in Neo4j"""
        query = """
        MERGE (u:User {id: $user_id})
        SET u.username = $username, u.created_at = datetime()
        RETURN u
        """
        return self.run_query(query, {"user_id": user_id, "username": username})
    
    def create_movie_node(self, movie_id, title, genres=None):
        """Create a movie node in Neo4j"""
        query = """
        MERGE (m:Movie {id: $movie_id})
        SET m.title = $title, m.created_at = datetime()
        """
        if genres:
            query += ", m.genres = $genres"
        query += " RETURN m"
        
        params = {"movie_id": movie_id, "title": title}
        if genres:
            params["genres"] = genres
            
        return self.run_query(query, params)
    
    def create_user_rating_relationship(self, user_id, movie_id, rating, comment=None):
        """Create a RATED relationship between user and movie"""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (m:Movie {id: $movie_id})
        MERGE (u)-[r:RATED]->(m)
        SET r.rating = $rating, r.timestamp = datetime()
        """
        if comment:
            query += ", r.comment = $comment"
        query += " RETURN r"
        
        params = {"user_id": user_id, "movie_id": movie_id, "rating": rating}
        if comment:
            params["comment"] = comment
            
        return self.run_query(query, params)
    
    def create_user_watchlist_relationship(self, user_id, movie_id):
        """Create a WANTS_TO_WATCH relationship"""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (m:Movie {id: $movie_id})
        MERGE (u)-[r:WANTS_TO_WATCH]->(m)
        SET r.added_at = datetime()
        RETURN r
        """
        return self.run_query(query, {"user_id": user_id, "movie_id": movie_id})
    
    def get_user_recommendations(self, user_id, limit=10):
        """Get movie recommendations based on user preferences and similar users"""
        query = """
        MATCH (u:User {id: $user_id})-[r:RATED]->(m:Movie)
        WHERE r.rating >= 4
        WITH u, collect(m.genres) as liked_genres
        UNWIND liked_genres as genre_list
        UNWIND genre_list as genre
        
        MATCH (rec_movie:Movie)
        WHERE genre IN rec_movie.genres
        AND NOT EXISTS((u)-[:RATED]->(rec_movie))
        AND NOT EXISTS((u)-[:WANTS_TO_WATCH]->(rec_movie))
        
        RETURN DISTINCT rec_movie.id as movie_id, rec_movie.title as title
        LIMIT $limit
        """
        return self.run_query(query, {"user_id": user_id, "limit": limit})
    
    def get_similar_movies(self, movie_id, limit=6):
        """Get movies similar to the given movie"""
        query = """
        MATCH (m:Movie {id: $movie_id})
        MATCH (similar:Movie)
        WHERE m <> similar
        AND any(genre IN m.genres WHERE genre IN similar.genres)
        
        RETURN DISTINCT similar.id as movie_id, similar.title as title,
               size([g IN m.genres WHERE g IN similar.genres]) as common_genres
        ORDER BY common_genres DESC
        LIMIT $limit
        """
        return self.run_query(query, {"movie_id": movie_id, "limit": limit})

# Global Neo4j connection instance - initialized lazily
_neo4j_conn = None

def get_neo4j_connection():
    """Get or create Neo4j connection instance"""
    global _neo4j_conn
    if _neo4j_conn is None:
        _neo4j_conn = Neo4jConnection()
    return _neo4j_conn
