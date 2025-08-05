# 🛠️ Tools Documentation

This document provides detailed information about all available tools in the Spider Agent Universal system.

## Overview

The Spider Agent Universal system includes four core tools that enable comprehensive database operations and system interactions:

1. **execute_database_sql** - Multi-database SQL execution
2. **execute_bash** - System command execution  
3. **execute_snowflake_sql** - Snowflake-specific operations
4. **terminate** - Task completion and result finalization

---

## 📊 Database SQL Tool (execute_database_sql)

### Description
A versatile database tool that supports multiple database types with intelligent connection management and result processing.

### Workflow Diagram

```mermaid
graph TD
    A[Tool Call: execute_database_sql] --> B{Parse Parameters}
    B --> C[Validate SQL Query]
    C --> D{Check DB Type}
    
    D -->|MySQL| E1[Load MySQL Credentials]
    D -->|PostgreSQL| E2[Load PostgreSQL Credentials]
    D -->|SQLite| E3[Load SQLite Credentials]
    D -->|Snowflake| E4[Load Snowflake Credentials]
    
    E1 --> F1[Create MySQL Connection]
    E2 --> F2[Create PostgreSQL Connection]
    E3 --> F3[Create SQLite Connection]
    E4 --> F4[Create Snowflake Connection]
    
    F1 --> G[Execute SQL Query]
    F2 --> G
    F3 --> G
    F4 --> G
    
    G --> H{Query Success?}
    H -->|Yes| I[Fetch Results]
    H -->|No| J[Capture Error]
    
    I --> K[Convert to CSV Format]
    K --> L{Result Size Check}
    L -->|< 2000 chars| M[Return Full Result]
    L -->|> 2000 chars| N[Truncate at Line Boundary]
    N --> O[Add Truncation Notice]
    
    J --> P[Format Error Message]
    M --> Q[Return Response]
    O --> Q
    P --> Q
    
    Q --> R[Close Connection]
    R --> S[End]
```

### Supported Databases
- **MySQL** - Full support with mysql-connector-python
- **PostgreSQL** - Full support with psycopg2
- **SQLite** - Built-in support with sqlite3
- **Snowflake** - Enterprise support with snowflake-connector-python

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sql` | string | ✅ | - | The SQL query to execute |
| `db_type` | string | ❌ | "mysql" | Database type (mysql/postgresql/sqlite/snowflake) |
| `timeout` | integer | ❌ | 60 | Query timeout in seconds |

### Usage Examples

#### Basic SELECT Query
```json
{
  "function": "execute_database_sql",
  "parameters": {
    "sql": "SELECT * FROM users LIMIT 10",
    "db_type": "mysql"
  }
}
```

#### PostgreSQL Query
```json
{
  "function": "execute_database_sql",
  "parameters": {
    "sql": "SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01'",
    "db_type": "postgresql"
  }
}
```

#### SQLite Query
```json
{
  "function": "execute_database_sql",
  "parameters": {
    "sql": "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)",
    "db_type": "sqlite"
  }
}
```

### Configuration

#### Credential Files
Create JSON files in the `credentials/` directory:

**MySQL** (`credentials/mysql_credential.json`):
```json
{
  "host": "localhost",
  "port": 3306,
  "user": "username",
  "password": "password",
  "database": "database_name"
}
```

**PostgreSQL** (`credentials/postgresql_credential.json`):
```json
{
  "host": "localhost",
  "port": 5432,
  "user": "postgres",
  "password": "password",
  "database": "database_name"
}
```

**SQLite** (`credentials/sqlite_credential.json`):
```json
{
  "database": "/path/to/database.db"
}
```

### Features

#### 🔄 Connection Management
- **Singleton Pattern**: Reuses connections for better performance
- **Auto-reconnection**: Handles connection drops gracefully
- **Type Switching**: Dynamically switches between database types

#### 📊 Result Processing
- **CSV Output**: Results formatted as CSV for easy reading
- **Smart Truncation**: Limits output to 2000 characters at line boundaries
- **Row Counting**: Shows total rows even when truncated
- **Error Handling**: Comprehensive error messages

#### ⏱️ Performance
- **Connection Pooling**: Reuses database connections
- **Timeout Protection**: 60-second default timeout
- **Memory Efficient**: Streams large result sets

### Return Format

#### Successful Query
```json
{
  "content": "EXECUTION RESULT of [execute_database_sql]:\nQuery executed successfully\n\n```csv\nid,name,email\n1,John Doe,john@example.com\n2,Jane Smith,jane@example.com\n```"
}
```

#### Truncated Results
```json
{
  "content": "EXECUTION RESULT of [execute_database_sql]:\nQuery executed successfully\n\n```csv\nid,name,email\n1,John Doe,john@example.com\n...\n```\n\nNote: Result truncated to 2000 characters. Complete result has 1000 rows and 50000 characters."
}
```

#### Error Response
```json
{
  "content": "EXECUTION RESULT of [execute_database_sql]:\nDatabase Error: Table 'users' doesn't exist"
}
```

---

## 💻 Bash Command Tool (execute_bash)

### Description
Executes system commands safely with timeout protection and output management.

### Workflow Diagram

```mermaid
graph TD
    A[Tool Call: execute_bash] --> B[Parse Parameters]
    B --> C[Validate Command]
    C --> D{Set Working Directory}
    D -->|Specified| E[Change to Work Dir]
    D -->|Default| F[Use Current Dir]
    
    E --> G[Setup Subprocess]
    F --> G
    
    G --> H[Set Timeout Protection]
    H --> I[Execute Command]
    
    I --> J{Command Execution}
    J -->|Success| K[Capture stdout]
    J -->|Error| L[Capture stderr]
    J -->|Timeout| M[Kill Process]
    
    K --> N[Get Return Code]
    L --> N
    M --> O[Timeout Error Message]
    
    N --> P{Output Size Check}
    P -->|< 2000 chars| Q[Return Full Output]
    P -->|> 2000 chars| R[Truncate Output]
    
    O --> S[Format Error Response]
    Q --> T[Format Success Response]
    R --> U[Add Truncation Notice]
    U --> T
    
    S --> V[Return Response]
    T --> V
    V --> W[End]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `command` | string | ✅ | - | The bash command to execute |
| `work_dir` | string | ❌ | current dir | Working directory for command execution |
| `timeout` | integer | ❌ | 30 | Command timeout in seconds |

### Usage Examples

#### File Operations
```json
{
  "function": "execute_bash",
  "parameters": {
    "command": "ls -la",
    "work_dir": "/home/user/project"
  }
}
```

#### System Information
```json
{
  "function": "execute_bash",
  "parameters": {
    "command": "df -h && free -m"
  }
}
```

#### Package Management
```json
{
  "function": "execute_bash",
  "parameters": {
    "command": "pip install pandas",
    "timeout": 120
  }
}
```

### Features

#### 🛡️ Security
- **Timeout Protection**: 30-second default timeout
- **Working Directory**: Isolated execution environment
- **Error Capture**: Captures both stdout and stderr

#### 📝 Output Management
- **Smart Truncation**: Limits output to 2000 characters
- **Full Logging**: Complete command and result logging
- **Return Code**: Tracks command success/failure

### Return Format

#### Successful Command
```json
{
  "content": "EXECUTION RESULT of [execute_bash]:\ntotal 48\ndrwxr-xr-x 12 user user 4096 Jan 15 10:30 .\ndrwxr-xr-x  3 user user 4096 Jan 15 10:25 ..\n-rw-r--r--  1 user user  220 Jan 15 10:25 .bashrc"
}
```

#### Command Error
```json
{
  "content": "EXECUTION RESULT of [execute_bash]:\nError: ls: cannot access '/nonexistent': No such file or directory"
}
```

#### Timeout Error
```json
{
  "content": "EXECUTION RESULT of [execute_bash]:\nCommand timed out after 30 seconds"
}
```

---

## ❄️ Snowflake SQL Tool (execute_snowflake_sql)

### Description
Specialized tool for Snowflake database operations with optimized connection handling.

### Workflow Diagram

```mermaid
graph TD
    A[Tool Call: execute_snowflake_sql] --> B[Parse Parameters]
    B --> C[Load Snowflake Credentials]
    C --> D[Validate Credentials]
    D --> E{Connection Exists?}
    
    E -->|Yes| F[Reuse Connection]
    E -->|No| G[Create New Connection]
    
    G --> H[Set Connection Parameters]
    H --> I[Authenticate with Snowflake]
    I --> J{Auth Success?}
    J -->|No| K[Auth Error]
    J -->|Yes| L[Set Warehouse/Database/Schema]
    
    F --> M[Execute SQL Query]
    L --> M
    
    M --> N{Query Execution}
    N -->|Success| O[Fetch Results]
    N -->|Error| P[Capture SQL Error]
    N -->|Timeout| Q[Timeout Error]
    
    O --> R[Convert to CSV Format]
    R --> S{Result Size Check}
    S -->|< 2000 chars| T[Return Full Result]
    S -->|> 2000 chars| U[Truncate at Line Boundary]
    U --> V[Add Truncation Notice]
    
    K --> W[Format Auth Error]
    P --> X[Format SQL Error]
    Q --> Y[Format Timeout Error]
    
    T --> Z[Return Response]
    V --> Z
    W --> Z
    X --> Z
    Y --> Z
    
    Z --> AA[Cleanup Resources]
    AA --> BB[End]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sql` | string | ✅ | - | The SQL query to execute |
| `timeout` | integer | ❌ | 60 | Query timeout in seconds |

### Configuration

**Snowflake Credentials** (`credentials/snowflake_credential.json`):
```json
{
  "account": "your-account.snowflakecomputing.com",
  "user": "username",
  "password": "password",
  "warehouse": "COMPUTE_WH",
  "database": "DATABASE_NAME",
  "schema": "SCHEMA_NAME",
  "role": "ROLE_NAME"
}
```

### Usage Examples

#### Data Warehouse Query
```json
{
  "function": "execute_snowflake_sql",
  "parameters": {
    "sql": "SELECT * FROM SALES_DATA WHERE DATE >= '2024-01-01' LIMIT 100"
  }
}
```

#### Analytics Query
```json
{
  "function": "execute_snowflake_sql",
  "parameters": {
    "sql": "SELECT REGION, SUM(REVENUE) FROM SALES GROUP BY REGION ORDER BY SUM(REVENUE) DESC"
  }
}
```

### Features

#### 🏢 Enterprise Features
- **Dedicated Connection**: Optimized for Snowflake
- **Warehouse Management**: Automatic warehouse handling
- **Role-based Access**: Supports Snowflake role system

#### ⚡ Performance
- **Connection Timeout**: Configurable login and network timeouts
- **Result Streaming**: Efficient handling of large datasets
- **Auto-commit**: Automatic transaction management

---

## 🏁 Termination Tool (terminate)

### Description
Signals task completion and provides final results to the user.

### Workflow Diagram

```mermaid
graph TD
    A[Tool Call: terminate] --> B[Parse Parameters]
    B --> C[Validate Answer Parameter]
    C --> D[Check Task Completion Status]
    D --> E[Format Final Response]
    E --> F[Log Task Completion]
    F --> G[Return Final Answer]
    G --> H[Signal Agent Termination]
    H --> I[Cleanup Resources]
    I --> J[End Agent Execution]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `answer` | string | ✅ | - | The final answer or result |
| `task_completed` | string | ❌ | "false" | Task completion status |

### Usage Examples

#### Task Completion
```json
{
  "function": "terminate",
  "parameters": {
    "answer": "Analysis complete. Found 1,234 records matching the criteria. The average revenue per customer is $456.78.",
    "task_completed": "true"
  }
}
```

#### Alternative Alias
```json
{
  "function": "finish",
  "parameters": {
    "answer": "Database schema analysis completed successfully."
  }
}
```

### Features

#### 🎯 Task Management
- **Clean Termination**: Properly ends agent execution
- **Result Delivery**: Provides final answer to user
- **Alias Support**: Available as both `terminate` and `finish`

### Return Format

```json
{
  "content": "EXECUTION RESULT of [terminate]:\nAnalysis complete. Found 1,234 records matching the criteria. The average revenue per customer is $456.78."
}
```

---