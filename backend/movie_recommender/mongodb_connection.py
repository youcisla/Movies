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
        """Connect to MongoDB and ensure the 'movierec' database exists"""
        if self._connection_attempted:
            return
            
        self._connection_attempted = True
        try:
            # Check if MONGODB_URI is properly configured
            mongodb_uri = settings.MONGODB_URI
            if not mongodb_uri:
                raise ValueError("MONGODB_URI is not configured in settings")
                
            logger.info(f"🔄 Attempting to connect to MongoDB Atlas...")
            self.client = MongoClient(
                mongodb_uri,
                connectTimeoutMS=10000,
                serverSelectionTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True,
                w='majority'
            )
            # Use movierec as the database name
            db_name = "movierec"
            self.db = self.client[db_name]
            
            # Ensure the 'movierec' database exists by creating a dummy collection if necessary
            if "movierec" not in self.client.list_database_names():
                self.db.create_collection("dummy_collection")
                self.db["dummy_collection"].drop()

            # Test connection
            self.client.admin.command('ping')
            self.is_connected = True
            logger.info(f"✅ Connected to MongoDB Atlas: movierec")
            
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
