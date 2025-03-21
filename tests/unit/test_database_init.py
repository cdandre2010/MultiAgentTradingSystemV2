import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import sqlite3

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.init import init_sqlite, init_neo4j, init_influxdb, init_all_databases


class TestDatabaseInit(unittest.TestCase):
    """Test cases for database initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database file for testing
        self.test_db_path = os.path.join(os.path.dirname(__file__), 'test.db')
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the test database file if it exists
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    @patch('src.database.init.db_manager')
    def test_init_sqlite(self, mock_db_manager):
        """Test SQLite database initialization."""
        # Setup mock
        conn = sqlite3.connect(self.test_db_path)
        mock_db_manager.sqlite_conn = conn
        
        # Mock file open
        with patch('builtins.open', unittest.mock.mock_open(read_data="CREATE TABLE users (id TEXT PRIMARY KEY);")):
            # Call the function
            result = init_sqlite(self.test_db_path)
        
        # Check the result
        self.assertTrue(result)
        
        # Clean up
        conn.close()
    
    @patch('src.database.init.db_manager')
    def test_init_neo4j(self, mock_db_manager):
        """Test Neo4j database initialization."""
        # Setup mock
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_db_manager.neo4j_driver = mock_driver
        
        # Mock file open
        with patch('builtins.open', unittest.mock.mock_open(read_data="CREATE (n:Node {name: 'Test'});")):
            # Call the function
            result = init_neo4j()
        
        # Check the result
        self.assertTrue(result)
        mock_session.run.assert_called()
    
    @patch('src.database.init.db_manager')
    def test_init_influxdb(self, mock_db_manager):
        """Test InfluxDB database initialization."""
        # Setup mock
        mock_buckets_api = MagicMock()
        mock_buckets = MagicMock()
        mock_buckets.buckets = [MagicMock(name="market_data")]
        mock_buckets_api.find_buckets.return_value = mock_buckets
        
        mock_client = MagicMock()
        mock_client.buckets_api.return_value = mock_buckets_api
        
        mock_db_manager.influxdb_client = mock_client
        mock_db_manager.influxdb_bucket = "market_data"
        
        # Call the function
        result = init_influxdb()
        
        # Check the result
        self.assertTrue(result)
    
    @patch('src.database.init.init_sqlite')
    @patch('src.database.init.init_neo4j')
    @patch('src.database.init.init_influxdb')
    @patch('src.database.init.db_manager')
    def test_init_all_databases(self, mock_db_manager, mock_init_influxdb, mock_init_neo4j, mock_init_sqlite):
        """Test initialization of all databases."""
        # Setup mocks
        mock_db_manager.connect_all.return_value = {
            "sqlite": True,
            "neo4j": True,
            "influxdb": True
        }
        
        mock_init_sqlite.return_value = True
        mock_init_neo4j.return_value = True
        mock_init_influxdb.return_value = True
        
        # Call the function
        result = init_all_databases()
        
        # Check the result
        self.assertEqual(result, {
            "sqlite": True,
            "neo4j": True,
            "influxdb": True
        })


if __name__ == '__main__':
    unittest.main()