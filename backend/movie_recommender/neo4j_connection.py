"""
Neo4j connection and utilities for the Movie Recommendation System
"""
from neo4j import GraphDatabase
from django.conf import settings
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Neo4jConnection:
    """Neo4j connection manager"""
    
    def __init__(self):
        self.driver = None
        self.is_connected = False
        self._connection_attempted = False
    
    def connect(self):
        """Connect to Neo4j with retry logic"""
        if self._connection_attempted:
            return

        self._connection_attempted = True
        try:
            # Ensure Neo4j settings are configured
            neo4j_uri = os.getenv("NEO4J_URI")
            neo4j_username = os.getenv("NEO4J_USERNAME")
            neo4j_password = os.getenv("NEO4J_PASSWORD")

            if not all([neo4j_uri, neo4j_username, neo4j_password]):
                raise ValueError("Neo4j connection settings are not properly configured in .env file")

            logger.info(f"Attempting to connect to Neo4j with URI: {neo4j_uri[:30]}...")
            
            # For Neo4j AuraDB, use specific configuration to handle routing issues
            if any(scheme in neo4j_uri for scheme in ["neo4j+s", "bolt+s", "bolt+ssc"]):
                # AuraDB specific configuration - optimized for "Unable to retrieve routing information" errors
                
                # Parse URI to get hostname for bolt connection
                parsed_uri = neo4j_uri.replace("neo4j+s://", "").replace("bolt+s://", "").replace("bolt+ssc://", "")
                hostname = parsed_uri.split("/")[0].split(":")[0]
                
                # Strategy order: Use the working bolt+ssc configuration first
                strategies = [
                    {
                        "name": "Current Working Configuration",
                        "uri": neo4j_uri,  # Use the exact URI from .env (bolt+ssc://)
                        "config": {
                            "connection_timeout": 30,
                            "max_connection_lifetime": 300,
                            "max_connection_pool_size": 10
                        }
                    },
                    {
                        "name": "Bolt+SSC Alternative (Strict SSL)",
                        "uri": f"bolt+ssc://{hostname}:7687",
                        "config": {
                            "connection_timeout": 30,
                            "max_connection_lifetime": 300,
                            "max_connection_pool_size": 10
                        }
                    },
                    {
                        "name": "Direct Bolt+S (Bypass Routing) - Fallback",
                        "uri": f"bolt+s://{hostname}:7687",
                        "config": {
                            "connection_timeout": 30,
                            "max_connection_lifetime": 200,
                            "max_connection_pool_size": 1
                        }
                    },
                    {
                        "name": "Single Instance Mode - Fallback",
                        "uri": f"bolt+s://{hostname}:7687",
                        "config": {
                            "connection_timeout": 60,
                            "max_connection_lifetime": 300,
                            "max_connection_pool_size": 1,
                            "connection_acquisition_timeout": 120
                        }
                    },
                    {
                        "name": "Original URI with Extended Timeout - Fallback",
                        "uri": neo4j_uri,
                        "config": {
                            "connection_timeout": 60,
                            "max_connection_lifetime": 300,
                            "connection_acquisition_timeout": 120
                        }
                    },
                    {
                        "name": "Conservative Original URI - Fallback",
                        "uri": neo4j_uri,
                        "config": {
                            "connection_timeout": 45,
                            "max_connection_lifetime": 200
                        }
                    }
                ]
                
                last_error = None
                for strategy in strategies:
                    try:
                        logger.info(f"Attempting {strategy['name']} for Neo4j AuraDB...")
                        self.driver = GraphDatabase.driver(
                            strategy['uri'],
                            auth=(neo4j_username, neo4j_password),
                            **strategy['config']
                        )
                        
                        # Test the connection immediately
                        with self.driver.session() as test_session:
                            result = test_session.run("RETURN 1 as test")
                            if result.single()["test"] == 1:
                                logger.info(f"✅ {strategy['name']} successful! URI: {strategy['uri'][:50]}...")
                                break
                                
                    except Exception as strategy_error:
                        last_error = strategy_error
                        logger.warning(f"❌ {strategy['name']} failed: {strategy_error}")
                        if self.driver:
                            self.driver.close()
                            self.driver = None
                        continue
                
                # If all strategies failed, raise the last error
                if not self.driver:
                    raise last_error if last_error else Exception("All AuraDB connection strategies failed")
                    
            else:
                # Standard configuration for bolt:// or neo4j:// URIs
                self.driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_username, neo4j_password),
                    encrypted=True,
                    trust="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES"
                )

            # Test the connection with a simple query
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    self.is_connected = True
                    logger.info("✅ Connected to Neo4j successfully.")
                else:
                    raise Exception("Connection test failed")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            logger.error(f"Neo4j URI: {neo4j_uri[:30] if neo4j_uri else 'Not set'}...")
            logger.error(f"Neo4j Username: {neo4j_username if neo4j_username else 'Not set'}")
            logger.error("Please check your Neo4j AuraDB credentials and network connectivity")
            self.is_connected = False
            if self.driver:
                self.driver.close()
                self.driver = None
    
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
            # For AuraDB, use default session without specifying database
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record for record in result]
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            # Try to reconnect on error
            self.is_connected = False
            self._connection_attempted = False
            return []
    
    def create_user_node(self, user_id, username):
        """Create a user node in Neo4j"""
        query = """
        MERGE (u:User {id: $user_id})
        SET u.username = $username, u.created_at = datetime()
        RETURN u
        """
        return self.run_query(query, {"user_id": user_id, "username": username})
    
    def create_movie_node(self, movie_id, title, genres=None, movie_data=None):
        """Create a movie node in Neo4j with complete data"""
        query = """
        MERGE (m:Movie {id: $movie_id})
        SET m.title = $title, m.created_at = datetime()
        """
        
        params = {"movie_id": movie_id, "title": title}
        
        # Add additional movie properties if provided
        if movie_data:
            query += """
            , m.overview = $overview
            , m.release_date = $release_date
            , m.runtime = $runtime
            , m.poster_path = $poster_path
            , m.backdrop_path = $backdrop_path
            , m.vote_average = $vote_average
            , m.vote_count = $vote_count
            , m.popularity = $popularity
            , m.tmdb_id = $tmdb_id
            """
            params.update({
                "overview": movie_data.get("overview", ""),
                "release_date": movie_data.get("release_date", ""),
                "runtime": movie_data.get("runtime", 0),
                "poster_path": movie_data.get("poster_path", ""),
                "backdrop_path": movie_data.get("backdrop_path", ""),
                "vote_average": movie_data.get("vote_average", 0.0),
                "vote_count": movie_data.get("vote_count", 0),
                "popularity": movie_data.get("popularity", 0.0),
                "tmdb_id": movie_data.get("tmdb_id")
            })
        
        if genres:
            query += ", m.genres = $genres"
            params["genres"] = genres
            
        query += " RETURN m"
        
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
