"""
Improved Neo4j connection for AuraDB routing issues
This version handles "Unable to retrieve routing information" errors
"""
import os
import logging
import time
from neo4j import GraphDatabase
from django.conf import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ImprovedNeo4jConnection:
    """
    Improved Neo4j connection manager that handles AuraDB routing issues
    """
    
    def __init__(self):
        self.driver = None
        self.is_connected = False
        self._connection_attempted = False
        self._last_connection_attempt = 0
        self._retry_delay = 30  # 30 seconds between retries
    
    def connect(self, force_retry=False):
        """Connect to Neo4j with improved error handling for AuraDB"""
        current_time = time.time()
        
        # Avoid rapid reconnection attempts
        if (not force_retry and 
            self._connection_attempted and 
            current_time - self._last_connection_attempt < self._retry_delay):
            logger.warning("⏳ Too soon to retry connection. Waiting...")
            return
        
        self._last_connection_attempt = current_time
        self._connection_attempted = True
        
        try:
            # Get credentials
            neo4j_uri = os.getenv("NEO4J_URI")
            neo4j_username = os.getenv("NEO4J_USERNAME")
            neo4j_password = os.getenv("NEO4J_PASSWORD")

            if not all([neo4j_uri, neo4j_username, neo4j_password]):
                raise ValueError("Neo4j connection settings are not properly configured in .env file")

            logger.info(f"🔗 Attempting to connect to Neo4j AuraDB...")
            
            # Configuration strategies to handle routing issues
            strategies = [
                {
                    "name": "Extended Timeout Strategy",
                    "config": {
                        "connection_timeout": 120,  # 2 minutes
                        "max_connection_lifetime": 600,  # 10 minutes
                        "connection_acquisition_timeout": 180,  # 3 minutes
                        "max_connection_pool_size": 5,
                    }
                },
                {
                    "name": "Single Connection Strategy", 
                    "config": {
                        "connection_timeout": 60,
                        "max_connection_pool_size": 1,
                        "max_connection_lifetime": 300,
                        "connection_acquisition_timeout": 120,
                    }
                },
                {
                    "name": "Conservative Strategy",
                    "config": {
                        "connection_timeout": 45,
                        "max_connection_lifetime": 200,
                        "max_connection_pool_size": 3,
                        "connection_acquisition_timeout": 90,
                    }
                },
                {
                    "name": "Minimal Strategy",
                    "config": {
                        "connection_timeout": 30,
                    }
                }
            ]
            
            # Try each strategy
            for strategy in strategies:
                try:
                    logger.info(f"🧪 Trying {strategy['name']}...")
                    
                    self.driver = GraphDatabase.driver(
                        neo4j_uri,
                        auth=(neo4j_username, neo4j_password),
                        **strategy['config']
                    )
                    
                    # Test the connection with a simple query
                    with self.driver.session() as session:
                        result = session.run("RETURN 1 as test, datetime() as timestamp")
                        record = result.single()
                        
                        if record and record["test"] == 1:
                            timestamp = record["timestamp"]
                            logger.info(f"✅ Connected successfully using {strategy['name']}")
                            logger.info(f"📅 Server timestamp: {timestamp}")
                            
                            # Get database info
                            try:
                                db_info = session.run("CALL dbms.components() YIELD name, versions, edition")
                                for db_record in db_info:
                                    logger.info(f"🗃️  Database: {db_record['name']} {db_record['versions'][0]} ({db_record['edition']})")
                            except Exception as db_e:
                                logger.warning(f"Could not get database info: {db_e}")
                            
                            self.is_connected = True
                            return True
                
                except Exception as e:
                    error_msg = str(e)
                    if "Unable to retrieve routing information" in error_msg:
                        logger.warning(f"❌ {strategy['name']} failed: Routing information error")
                    elif "SSLCertVerificationError" in error_msg:
                        logger.warning(f"❌ {strategy['name']} failed: SSL certificate error")
                    elif "ConnectionResetError" in error_msg:
                        logger.warning(f"❌ {strategy['name']} failed: Connection reset")
                    else:
                        logger.warning(f"❌ {strategy['name']} failed: {error_msg}")
                    
                    if self.driver:
                        try:
                            self.driver.close()
                        except:
                            pass
                        self.driver = None
                    continue
            
            # If all strategies failed
            logger.error("❌ All connection strategies failed")
            logger.error("💡 Possible issues:")
            logger.error("   • Neo4j AuraDB instance is paused or not running")
            logger.error("   • IP address not in allowlist")
            logger.error("   • Network/firewall restrictions")
            logger.error("   • Incorrect credentials")
            
            self.is_connected = False
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            self.is_connected = False
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            try:
                self.driver.close()
                logger.info("🔌 Neo4j connection closed")
            except Exception as e:
                logger.warning(f"Error closing Neo4j connection: {e}")
            finally:
                self.driver = None
                self.is_connected = False
    
    def run_query(self, query, parameters=None, retry_on_failure=True):
        """Run a Cypher query with improved error handling"""
        if not self._connection_attempted:
            self.connect()
        
        if not self.is_connected:
            if retry_on_failure:
                logger.warning("⚠️ Neo4j not connected. Attempting to reconnect...")
                if self.connect(force_retry=True):
                    logger.info("✅ Reconnection successful")
                else:
                    logger.warning("❌ Reconnection failed. Cannot run query.")
                    return []
            else:
                logger.warning("⚠️ Neo4j not connected. Cannot run query.")
                return []
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Neo4j query error: {error_msg}")
            
            # Check if it's a connection issue
            if any(keyword in error_msg.lower() for keyword in 
                   ['connection', 'routing', 'network', 'timeout', 'ssl']):
                logger.warning("🔄 Connection issue detected. Marking as disconnected.")
                self.is_connected = False
                
                if retry_on_failure:
                    logger.info("🔄 Attempting to reconnect and retry query...")
                    if self.connect(force_retry=True):
                        try:
                            with self.driver.session() as session:
                                result = session.run(query, parameters or {})
                                return [record.data() for record in result]
                        except Exception as retry_e:
                            logger.error(f"Retry also failed: {retry_e}")
            
            return []
    
    def test_connection(self):
        """Test the current connection"""
        if not self.is_connected:
            return False
        
        try:
            result = self.run_query("RETURN 'Connection test' as message", retry_on_failure=False)
            return len(result) > 0
        except:
            return False
    
    def get_connection_status(self):
        """Get detailed connection status"""
        status = {
            "is_connected": self.is_connected,
            "connection_attempted": self._connection_attempted,
            "last_attempt": self._last_connection_attempt,
            "driver_exists": self.driver is not None
        }
        
        if self.is_connected and self.test_connection():
            status["test_query"] = "✅ Pass"
        else:
            status["test_query"] = "❌ Fail"
        
        return status

# Global improved Neo4j connection instance
_improved_neo4j_conn = None

def get_improved_neo4j_connection():
    """Get or create improved Neo4j connection instance"""
    global _improved_neo4j_conn
    if _improved_neo4j_conn is None:
        _improved_neo4j_conn = ImprovedNeo4jConnection()
    return _improved_neo4j_conn
