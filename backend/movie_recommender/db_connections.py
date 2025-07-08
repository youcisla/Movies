"""
Database connection utilities for MongoDB and Neo4j
"""

import os
from pymongo import MongoClient
from py2neo import Graph
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class DatabaseConnections:
    """Singleton class to manage database connections"""
    
    _instance = None
    _mongodb_client = None
    _neo4j_graph = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnections, cls).__new__(cls)
        return cls._instance
    
    def get_mongodb_client(self):
        """Get MongoDB client connection"""
        if self._mongodb_client is None:
            try:
                self._mongodb_client = MongoClient(
                    settings.MONGODB_URI,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000
                )
                # Test connection
                self._mongodb_client.admin.command('ping')
                logger.info("MongoDB connection established successfully")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
        return self._mongodb_client
    
    def get_mongodb_database(self, db_name='moviedb'):
        """Get MongoDB database"""
        client = self.get_mongodb_client()
        return client[db_name]
    
    def get_neo4j_graph(self):
        """Get Neo4j graph connection"""
        if self._neo4j_graph is None:
            try:
                self._neo4j_graph = Graph(
                    settings.NEO4J_SETTINGS['uri'],
                    auth=(
                        settings.NEO4J_SETTINGS['username'],
                        settings.NEO4J_SETTINGS['password']
                    )
                )
                # Test connection
                self._neo4j_graph.run("RETURN 1")
                logger.info("Neo4j connection established successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
        return self._neo4j_graph
    
    def close_connections(self):
        """Close all database connections"""
        if self._mongodb_client:
            self._mongodb_client.close()
            self._mongodb_client = None
            logger.info("MongoDB connection closed")
        
        if self._neo4j_graph:
            # Neo4j connections are managed by the driver
            self._neo4j_graph = None
            logger.info("Neo4j connection closed")

# Global database connections instance
db_connections = DatabaseConnections()

# Convenience functions
def get_mongodb():
    """Get MongoDB database"""
    return db_connections.get_mongodb_database()

def get_neo4j():
    """Get Neo4j graph"""
    return db_connections.get_neo4j_graph()

def test_connections():
    """Test all database connections"""
    try:
        # Test MongoDB
        mongodb = get_mongodb()
        mongodb.test_collection.insert_one({'test': 'connection'})
        mongodb.test_collection.delete_one({'test': 'connection'})
        logger.info("MongoDB connection test successful")
        
        # Test Neo4j
        neo4j = get_neo4j()
        neo4j.run("RETURN 1 AS test")
        logger.info("Neo4j connection test successful")
        
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
