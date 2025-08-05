# 🕷️ Spider Agent Universal

> A conversational Spider Agent abstracted from the [Spider2 project](https://github.com/xlang-ai/Spider2), supporting multi-database queries and system command execution in an intelligent agent system.

[🇨🇳 中文文档](./README_CN.md) | [🇺🇸 English](./README.md)

## 📖 Overview

Spider Agent Universal is an intelligent agent system based on client-server architecture, specifically designed for handling complex database queries and system operations. It inherits the core capabilities of the Spider2 project while providing a more flexible conversational interaction experience.

### ✨ Key Features

- 🗄️ **Multi-Database Support**: MySQL, PostgreSQL, SQLite, Snowflake
- 💻 **System Command Execution**: Secure Bash command execution environment
- 🔄 **Client-Server Separation**: High-performance distributed architecture
- 🛡️ **Security Protection**: Timeout control, output limits, error handling
- 🚀 **High Performance**: Connection pooling, async execution, intelligent truncation

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment configuration file
cp .env.example .env

# Edit .env file with your API keys and configuration
```

### 2. Database Credentials Configuration

Create corresponding database credential files in the `credentials/` directory:

```bash
credentials/
├── mysql_credential.json
├── postgresql_credential.json
├── sqlite_credential.json
└── snowflake_credential.json
```

### 3. Start the System

```bash
# Start the tools server
./run_server.sh

# Start the client agent (in a new terminal)
./run_chat.sh
```

> 💡 Tip: You can modify the model name in `run_chat.sh`

## 🏗️ System Architecture
```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   Client Agent  │ ──────────────► │   Tools Server  │
│   (llm_agent)   │                │   (serve.py)    │
└─────────────────┘                └─────────────────┘
│                                   │
▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│ Message Processor│                │ Tool Registry   │
│(message_processor)│               │(tool_registry)  │
└─────────────────┘                └─────────────────┘
│
▼
┌─────────────────┐
│   Tool Suite    │
│ • database_tool │
│ • bash_tool     │
│ • snowflake_tool│
│ • terminator_tool│
└─────────────────┘
```
## 🛠️ Core Tools

### 1. 📊 Database Query Tool (execute_database_sql)

**Function**: Execute SQL queries with support for multiple database types

**Supported Databases**:
- MySQL
- PostgreSQL  
- SQLite
- Snowflake

**Features**:
- Connection pooling and reuse
- Intelligent result truncation (2000 character limit)
- CSV format output
- 60-second timeout protection

### 2. 💻 System Command Tool (execute_bash)

**Function**: Safely execute system Bash commands

**Features**:
- Working directory specification
- Output capture (stdout/stderr)
- 30-second timeout protection
- Intelligent output truncation

### 3. ❄️ Snowflake Specialized Tool (execute_snowflake_sql)

**Function**: Optimized Snowflake database query tool

**Features**:
- Dedicated connection configuration
- Optimized timeout settings
- Efficient result processing

### 4. 🏁 Task Termination Tool (terminate)

**Function**: Gracefully end tasks and return final answers

## 🔧 Configuration

### Environment Variables (.env)

```bash
# API Configuration
API_HOST=localhost
API_PORT=8000

# Model Configuration
MODEL_NAME=your-model-name
API_KEY=your-api-key

# Database Path
DATABASES_PATH=./databases
```

### Database Credentials Examples

**MySQL Credentials** (`credentials/mysql_credential.json`):
```json
{
    "host": "localhost",
    "port": 3306,
    "user": "username",
    "password": "password",
    "database": "database_name"
}
```

**Snowflake Credentials** (`credentials/snowflake_credential.json`):
```json
{
    "account": "your-account",
    "user": "username",
    "password": "password",
    "warehouse": "warehouse_name",
    "database": "database_name",
    "schema": "schema_name"
}
```

## 🛡️ Security Features

### Timeout Protection
- Database queries: 60-second timeout
- Bash commands: 30-second timeout
- HTTP requests: 30-second timeout

### Output Limits
- CSV results: 2000-character intelligent truncation
- Bash output: 2000-character intelligent truncation
- Boundary truncation to avoid data corruption

### Error Handling
- Comprehensive exception catching
- Detailed error logging
- Graceful error recovery

## 🚀 Performance Optimization

### Connection Management
- Database connection pool reuse
- Global connector singleton pattern
- Automatic connection cleanup

### Asynchronous Processing
- Thread pool execution (8 workers per tool)
- Asynchronous tool calls
- Non-blocking HTTP responses

### Intelligent Truncation
- Complete line boundary truncation
- Avoid data corruption
- Maintain output readability

## 📁 Project Structure
```
spider-agent-universal/
├── agent/                  # Client Agent code
│   ├── llm_agent.py       # Main Agent logic
│   ├── message_processor.py # Message processor
│   └── ...
├── servers/               # Server-side code
│   ├── serve.py          # FastAPI server
│   ├── tools/            # Tool implementations
│   └── utils/            # Tool registry
├── prompts/              # Prompt templates
├── credentials/          # Database credentials (create yourself)
├── .env.example         # Environment configuration template
└── requirements.txt     # Python dependencies
```
## 🤝 Contributing

Issues and Pull Requests are welcome to improve this project!

## 📄 License

This project is developed based on the Spider2 project. Please refer to the original project's license terms.

## 🔗 Related Links

- [Spider2 Original Project](https://github.com/xlang-ai/Spider2)
- [Spider2 Paper](https://arxiv.org/abs/2411.07763)
- [ICLR 2025 Oral Publication](https://github.com/xlang-ai/Spider2)

---

## 📚 Documentation

- [🇨🇳 中文详细文档](./docs/README_CN.md) - Complete Chinese documentation
- [🛠️ Tools Documentation](./docs/tools.md) - Detailed tool reference and usage
- [🛠️ 工具详细文档](./docs/tools_CN.md) - 工具详细说明和使用指南
