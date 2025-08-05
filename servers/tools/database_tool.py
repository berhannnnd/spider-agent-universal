import json
import logging
import time
import os
from typing import Dict, Any, Optional
import pandas as pd

# Import database connectors
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    from psycopg2 import Error as PostgreSQLError
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

try:
    import snowflake.connector
    from snowflake.connector.errors import ProgrammingError, DatabaseError
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False

logger = logging.getLogger(__name__)

TIMEOUT = 60
MAX_CSV_CHARS = 2000

class DatabaseConnector:
    def __init__(self, db_type: str = "mysql"):
        self.db_type = db_type.lower()
        self.connection = None
        
    def get_credentials(self) -> Dict[str, Any]:
        """Load database credentials from config file"""
        credentials_path = f"credentials/{self.db_type}_credential.json"
        try:
            with open(credentials_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Credentials file not found at: {os.path.abspath(credentials_path)}")
            # Return default credentials for development
            if self.db_type == "mysql":
                return {
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "",
                    "database": "test"
                }
            elif self.db_type == "postgresql":
                return {
                    "host": "localhost",
                    "port": 5432,
                    "user": "postgres",
                    "password": "",
                    "database": "postgres"
                }
            elif self.db_type == "sqlite":
                return {
                    "database": "database.db"
                }
            else:
                raise
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            raise
    
    def connect(self):
        """Establish database connection"""
        credentials = self.get_credentials()
        
        try:
            if self.db_type == "mysql" and MYSQL_AVAILABLE:
                self.connection = mysql.connector.connect(**credentials)
            elif self.db_type == "postgresql" and POSTGRESQL_AVAILABLE:
                self.connection = psycopg2.connect(**credentials)
            elif self.db_type == "sqlite" and SQLITE_AVAILABLE:
                self.connection = sqlite3.connect(credentials["database"])
            elif self.db_type == "snowflake" and SNOWFLAKE_AVAILABLE:
                self.connection = snowflake.connector.connect(**credentials)
            else:
                raise Exception(f"Database type '{self.db_type}' not supported or driver not available")
                
        except Exception as e:
            logger.error(f"Failed to connect to {self.db_type}: {str(e)}")
            raise
    
    def execute_query(self, sql: str, timeout: int = TIMEOUT) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        if not self.connection:
            self.connect()
        
        start_time = time.time()
        content = ""
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)
            
            # Check if query returns data
            if cursor.description:
                # Fetch column names
                if self.db_type == "sqlite":
                    headers = [desc[0] for desc in cursor.description]
                else:
                    headers = [desc[0] for desc in cursor.description]
                
                rows = cursor.fetchall()
                
                if rows:
                    df = pd.DataFrame(rows, columns=headers)
                    full_csv_data = df.to_csv(index=False)
                    total_rows = len(df)
                    
                    # Truncate if too long
                    if len(full_csv_data) > MAX_CSV_CHARS:
                        truncated_csv = full_csv_data[:MAX_CSV_CHARS]
                        last_newline = truncated_csv.rfind('\n')
                        if last_newline > 0:
                            truncated_csv = truncated_csv[:last_newline]
                        
                        content = f"""Query executed successfully

```csv
{truncated_csv}
```

Note: Result truncated to {MAX_CSV_CHARS} characters. Complete result has {total_rows} rows and {len(full_csv_data)} characters."""
                    else:
                        content = f"""Query executed successfully

```csv
{full_csv_data}
```"""
                else:
                    content = "Query executed successfully, but no rows returned."
            else:
                # For non-SELECT queries
                if self.db_type != "sqlite":
                    self.connection.commit()
                content = "Query executed successfully."
                
        except Exception as e:
            content = f"Database Error: {str(e)}"
            logger.error(f"Database query error: {str(e)}")
        finally:
            execution_time = time.time() - start_time
            logger.info(f"Query execution completed in {execution_time:.2f} seconds")
        
        return {
            "content": f"EXECUTION RESULT of [execute_database_sql]:\n{content}"
        }
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

# Global database connector instance
_db_connector = None

def get_database_connector(db_type: str = "mysql") -> DatabaseConnector:
    """Get or create database connector instance"""
    global _db_connector
    if _db_connector is None or _db_connector.db_type != db_type:
        _db_connector = DatabaseConnector(db_type)
    return _db_connector

def execute_database_sql(sql: str, db_type: str = "mysql", **kwargs) -> Dict[str, Any]:
    """Execute SQL query on the specified database type"""
    logger.info(f"Executing {db_type.upper()} SQL: {sql}")
    
    timeout = kwargs.get('timeout', TIMEOUT)
    
    try:
        connector = get_database_connector(db_type)
        result = connector.execute_query(sql, timeout)
        return result
    except Exception as e:
        error_msg = f"Failed to execute query: {str(e)}"
        logger.error(error_msg)
        return {
            "content": f"EXECUTION RESULT of [execute_database_sql]:\n{error_msg}"
        }

def register_tools(registry):
    """Register database tools with the tool registry"""
    registry.register_tool("execute_database_sql", execute_database_sql)
    
    # Also register specific database tools for backward compatibility
    registry.register_tool("execute_mysql_sql", lambda sql, **kwargs: execute_database_sql(sql, "mysql", **kwargs))
    registry.register_tool("execute_postgresql_sql", lambda sql, **kwargs: execute_database_sql(sql, "postgresql", **kwargs))
    registry.register_tool("execute_sqlite_sql", lambda sql, **kwargs: execute_database_sql(sql, "sqlite", **kwargs))
