"""
MongoDB connection and utilities for the Movie Recommendation System
"""
import pymongo
from pymongo import MongoClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MongoDBConnection:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self._connection_attempted = False
    
    def connect(self):
        """Connect to MongoDB with retry logic"""
        if self._connection_attempted:
            return
            
        self._connection_attempted = True
        try:
            mongodb_uri = settings.MONGODB_URI
            if not mongodb_uri:
                raise ValueError("MONGODB_URI is not configured in settings")
                
            self.client = MongoClient(
                mongodb_uri,
                connectTimeoutMS=10000,
                serverSelectionTimeoutMS=10000,
                retryWrites=True,
                w='majority'
            )
            self.db = self.client["movierec"]
            self.is_connected = True
            logger.info("✅ Connected to MongoDB Atlas.")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.is_connected = False
    
    def get_collection(self, collection_name):
        """Get a MongoDB collection"""
        if not self._connection_attempted:
            self.connect()
            
        if not self.is_connected:
            logger.warning(f"MongoDB not connected. Cannot get collection '{collection_name}'")
            return None
            
        return self.db[collection_name] if self.is_connected else None
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Global MongoDB connection instance - initialized lazily
_mongodb_conn = None

def get_mongodb_connection():
    """Get or create MongoDB connection instance"""
    global _mongodb_conn
    if _mongodb_conn is None:
        _mongodb_conn = MongoDBConnection()
    return _mongodb_conn

def get_movies_collection():
    """Get movies collection"""
    conn = get_mongodb_connection()
    collection = conn.get_collection('movies')
    if collection is None:
        logger.warning("MongoDB not available, returning None for movies collection")
    return collection

def get_reviews_collection():
    """Get reviews collection"""
    conn = get_mongodb_connection()
    collection = conn.get_collection('reviews')
    if collection is None:
        logger.warning("MongoDB not available, returning None for reviews collection")
    return collection

def get_users_collection():
    """Get users collection"""
    conn = get_mongodb_connection()
    collection = conn.get_collection('users')
    if collection is None:
        logger.warning("MongoDB not available, returning None for users collection")
    return collection

def get_interactions_collection():
    """Get user interactions collection"""
    conn = get_mongodb_connection()
    collection = conn.get_collection('interactions')
    if collection is None:
        logger.warning("MongoDB not available, returning None for interactions collection")
    return collection
