# 🛠️ 工具文档

本文档提供了 Spider Agent Universal 系统中所有可用工具的详细信息。

## 概述

Spider Agent Universal 系统包含四个核心工具，支持全面的数据库操作和系统交互：

1. **execute_database_sql** - 多数据库 SQL 执行
2. **execute_bash** - 系统命令执行
3. **execute_snowflake_sql** - Snowflake 专用操作
4. **terminate** - 任务完成和结果终结

---

## 📊 数据库 SQL 工具 (execute_database_sql)

### 描述
一个支持多种数据库类型的通用数据库工具，具有智能连接管理和结果处理功能。

### 工作流程图

```mermaid
graph TD
    A[工具调用: execute_database_sql] --> B{解析参数}
    B --> C[验证 SQL 查询]
    C --> D{检查数据库类型}
    
    D -->|MySQL| E1[加载 MySQL 凭证]
    D -->|PostgreSQL| E2[加载 PostgreSQL 凭证]
    D -->|SQLite| E3[加载 SQLite 凭证]
    D -->|Snowflake| E4[加载 Snowflake 凭证]
    
    E1 --> F1[创建 MySQL 连接]
    E2 --> F2[创建 PostgreSQL 连接]
    E3 --> F3[创建 SQLite 连接]
    E4 --> F4[创建 Snowflake 连接]
    
    F1 --> G[执行 SQL 查询]
    F2 --> G
    F3 --> G
    F4 --> G
    
    G --> H{查询成功?}
    H -->|是| I[获取结果]
    H -->|否| J[捕获错误]
    
    I --> K[转换为 CSV 格式]
    K --> L{结果大小检查}
    L -->|< 2000 字符| M[返回完整结果]
    L -->|> 2000 字符| N[在行边界截断]
    N --> O[添加截断提示]
    
    J --> P[格式化错误消息]
    M --> Q[返回响应]
    O --> Q
    P --> Q
    
    Q --> R[关闭连接]
    R --> S[结束]
```

### 支持的数据库
- **MySQL** - 使用 mysql-connector-python 完全支持
- **PostgreSQL** - 使用 psycopg2 完全支持
- **SQLite** - 使用 sqlite3 内置支持
- **Snowflake** - 使用 snowflake-connector-python 企业级支持

### 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `sql` | string | ✅ | - | 要执行的 SQL 查询 |
| `db_type` | string | ❌ | "mysql" | 数据库类型 (mysql/postgresql/sqlite/snowflake) |
| `timeout` | integer | ❌ | 60 | 查询超时时间（秒） |

### 使用示例

#### 基本 SELECT 查询
```json
{
  "function": "execute_database_sql",
  "parameters": {
    "sql": "SELECT * FROM users LIMIT 10",
    "db_type": "mysql"
  }
}
```

#### PostgreSQL 查询
```json
{
  "function": "execute_database_sql",
  "parameters": {
    "sql": "SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01'",
    "db_type": "postgresql"
  }
}
```

#### SQLite 查询
```json
{
  "function": "execute_database_sql",
  "parameters": {
    "sql": "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)",
    "db_type": "sqlite"
  }
}
```

### 配置

#### 凭证文件
在 `credentials/` 目录中创建 JSON 文件：

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

### 特性

#### 🔄 连接管理
- **单例模式**: 重用连接以提高性能
- **自动重连**: 优雅处理连接断开
- **类型切换**: 动态切换数据库类型

#### 📊 结果处理
- **CSV 输出**: 结果格式化为 CSV 便于阅读
- **智能截断**: 在行边界限制输出到 2000 字符
- **行计数**: 即使截断也显示总行数
- **错误处理**: 全面的错误消息

#### ⏱️ 性能
- **连接池**: 重用数据库连接
- **超时保护**: 60 秒默认超时
- **内存高效**: 流式处理大结果集

### 返回格式

#### 成功查询
```json
{
  "content": "EXECUTION RESULT of [execute_database_sql]:\nQuery executed successfully\n\n```csv\nid,name,email\n1,John Doe,john@example.com\n2,Jane Smith,jane@example.com\n```"
}
```

#### 截断结果
```json
{
  "content": "EXECUTION RESULT of [execute_database_sql]:\nQuery executed successfully\n\n```csv\nid,name,email\n1,John Doe,john@example.com\n...\n```\n\nNote: Result truncated to 2000 characters. Complete result has 1000 rows and 50000 characters."
}
```

#### 错误响应
```json
{
  "content": "EXECUTION RESULT of [execute_database_sql]:\nDatabase Error: Table 'users' doesn't exist"
}
```

---

## 💻 Bash 命令工具 (execute_bash)

### 描述
安全执行系统命令，具有超时保护和输出管理功能。

### 工作流程图

```mermaid
graph TD
    A[工具调用: execute_bash] --> B[解析参数]
    B --> C[验证命令]
    C --> D{设置工作目录}
    D -->|指定| E[切换到工作目录]
    D -->|默认| F[使用当前目录]
    
    E --> G[设置子进程]
    F --> G
    
    G --> H[设置超时保护]
    H --> I[执行命令]
    
    I --> J{命令执行}
    J -->|成功| K[捕获 stdout]
    J -->|错误| L[捕获 stderr]
    J -->|超时| M[终止进程]
    
    K --> N[获取返回码]
    L --> N
    M --> O[超时错误消息]
    
    N --> P{输出大小检查}
    P -->|< 2000 字符| Q[返回完整输出]
    P -->|> 2000 字符| R[截断输出]
    
    O --> S[格式化错误响应]
    Q --> T[格式化成功响应]
    R --> U[添加截断提示]
    U --> T
    
    S --> V[返回响应]
    T --> V
    V --> W[结束]
```

### 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `command` | string | ✅ | - | 要执行的 bash 命令 |
| `work_dir` | string | ❌ | 当前目录 | 命令执行的工作目录 |
| `timeout` | integer | ❌ | 30 | 命令超时时间（秒） |

### 使用示例

#### 文件操作
```json
{
  "function": "execute_bash",
  "parameters": {
    "command": "ls -la",
    "work_dir": "/home/user/project"
  }
}
```

#### 系统信息
```json
{
  "function": "execute_bash",
  "parameters": {
    "command": "df -h && free -m"
  }
}
```

#### 包管理
```json
{
  "function": "execute_bash",
  "parameters": {
    "command": "pip install pandas",
    "timeout": 120
  }
}
```

### 特性

#### 🛡️ 安全性
- **超时保护**: 30 秒默认超时
- **工作目录**: 隔离执行环境
- **错误捕获**: 捕获 stdout 和 stderr

#### 📝 输出管理
- **智能截断**: 限制输出到 2000 字符
- **完整日志**: 完整的命令和结果日志
- **返回码**: 跟踪命令成功/失败

### 返回格式

#### 成功命令
```json
{
  "content": "EXECUTION RESULT of [execute_bash]:\ntotal 48\ndrwxr-xr-x 12 user user 4096 Jan 15 10:30 .\ndrwxr-xr-x  3 user user 4096 Jan 15 10:25 ..\n-rw-r--r--  1 user user  220 Jan 15 10:25 .bashrc"
}
```

#### 命令错误
```json
{
  "content": "EXECUTION RESULT of [execute_bash]:\nError: ls: cannot access '/nonexistent': No such file or directory"
}
```

#### 超时错误
```json
{
  "content": "EXECUTION RESULT of [execute_bash]:\nCommand timed out after 30 seconds"
}
```

---

## ❄️ Snowflake SQL 工具 (execute_snowflake_sql)

### 描述
专门用于 Snowflake 数据库操作的工具，具有优化的连接处理。

### 工作流程图

```mermaid
graph TD
    A[工具调用: execute_snowflake_sql] --> B[解析参数]
    B --> C[加载 Snowflake 凭证]
    C --> D[验证凭证]
    D --> E{连接存在?}
    
    E -->|是| F[重用连接]
    E -->|否| G[创建新连接]
    
    G --> H[设置连接参数]
    H --> I[Snowflake 身份验证]
    I --> J{认证成功?}
    J -->|否| K[认证错误]
    J -->|是| L[设置仓库/数据库/模式]
    
    F --> M[执行 SQL 查询]
    L --> M
    
    M --> N{查询执行}
    N -->|成功| O[获取结果]
    N -->|错误| P[捕获 SQL 错误]
    N -->|超时| Q[超时错误]
    
    O --> R[转换为 CSV 格式]
    R --> S{结果大小检查}
    S -->|< 2000 字符| T[返回完整结果]
    S -->|> 2000 字符| U[在行边界截断]
    U --> V[添加截断提示]
    
    K --> W[格式化认证错误]
    P --> X[格式化 SQL 错误]
    Q --> Y[格式化超时错误]
    
    T --> Z[返回响应]
    V --> Z
    W --> Z
    X --> Z
    Y --> Z
    
    Z --> AA[清理资源]
    AA --> BB[结束]
```

### 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `sql` | string | ✅ | - | 要执行的 SQL 查询 |
| `timeout` | integer | ❌ | 60 | 查询超时时间（秒） |

### 配置

**Snowflake 凭证** (`credentials/snowflake_credential.json`):
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

### 使用示例

#### 数据仓库查询
```json
{
  "function": "execute_snowflake_sql",
  "parameters": {
    "sql": "SELECT * FROM SALES_DATA WHERE DATE >= '2024-01-01' LIMIT 100"
  }
}
```

#### 分析查询
```json
{
  "function": "execute_snowflake_sql",
  "parameters": {
    "sql": "SELECT REGION, SUM(REVENUE) FROM SALES GROUP BY REGION ORDER BY SUM(REVENUE) DESC"
  }
}
```

### 特性

#### 🏢 企业级功能
- **专用连接**: 针对 Snowflake 优化
- **仓库管理**: 自动仓库处理
- **基于角色的访问**: 支持 Snowflake 角色系统

#### ⚡ 性能
- **连接超时**: 可配置的登录和网络超时
- **结果流**: 高效处理大数据集
- **自动提交**: 自动事务管理

---

## 🏁 终止工具 (terminate)

### 描述
标志任务完成并向用户提供最终结果。

### 工作流程图

```mermaid
graph TD
    A[工具调用: terminate] --> B[解析参数]
    B --> C[验证答案参数]
    C --> D[检查任务完成状态]
    D --> E[格式化最终响应]
    E --> F[记录任务完成]
    F --> G[返回最终答案]
    G --> H[发送代理终止信号]
    H --> I[清理资源]
    I --> J[结束代理执行]
```

### 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `answer` | string | ✅ | - | 最终答案或结果 |
| `task_completed` | string | ❌ | "false" | 任务完成状态 |

### 使用示例

#### 任务完成
```json
{
  "function": "terminate",
  "parameters": {
    "answer": "分析完成。找到 1,234 条符合条件的记录。每位客户的平均收入为 $456.78。",
    "task_completed": "true"
  }
}
```

#### 替代别名
```json
{
  "function": "finish",
  "parameters": {
    "answer": "数据库架构分析成功完成。"
  }
}
```

### 特性

#### 🎯 任务管理
- **清洁终止**: 正确结束代理执行
- **结果交付**: 向用户提供最终答案
- **别名支持**: 可用作 `terminate` 和 `finish`

### 返回格式

```json
{
  "content": "EXECUTION RESULT of [terminate]:\n分析完成。找到 1,234 条符合条件的记录。每位客户的平均收入为 $456.78。"
}
```

---

## 🔄 系统级工作流程

### 整体工具执行流程

```mermaid
graph TD
    A[客户端请求] --> B[HTTP 服务器接收请求]
    B --> C[从 JSON 解析工具调用]
    C --> D[工具注册表查找]
    D --> E{找到工具?}
    
    E -->|否| F[返回工具未找到错误]
    E -->|是| G[验证参数]
    
    G --> H{参数有效?}
    H -->|否| I[返回参数错误]
    H -->|是| J[执行工具函数]
    
    J --> K[数据库工具?]
    J --> L[Bash 工具?]
    J --> M[Snowflake 工具?]
    J --> N[终止工具?]
    
    K --> O[数据库工作流程]
    L --> P[Bash 工作流程]
    M --> Q[Snowflake 工作流程]
    N --> R[终止工作流程]
    
    O --> S[收集结果]
    P --> S
    Q --> S
    R --> T[结束代理会话]
    
    S --> U[格式化响应]
    U --> V[应用输出限制]
    V --> W[返回 HTTP 响应]
    
    F --> W
    I --> W
    T --> X[会话已终止]
    W --> Y[客户端接收响应]
```

### 工具注册过程

```mermaid
graph TD
    A[服务器启动] --> B[初始化工具注册表]
    B --> C[扫描工具目录]
    C --> D[导入工具模块]
    D --> E[为每个模块调用 register_tools()]
    
    E --> F[数据库工具注册]
    E --> G[Bash 工具注册]
    E --> H[Snowflake 工具注册]
    E --> I[终止工具注册]
    
    F --> J[注册 execute_database_sql]
    F --> K[注册 execute_mysql_sql 别名]
    F --> L[注册 execute_postgresql_sql 别名]
    F --> M[注册 execute_sqlite_sql 别名]
    
    G --> N[注册 execute_bash]
    H --> O[注册 execute_snowflake_sql]
    I --> P[注册 terminate]
    I --> Q[注册 finish 别名]
    
    J --> R[工具注册表完成]
    K --> R
    L --> R
    M --> R
    N --> R
    O --> R
    P --> R
    Q --> R
    
    R --> S[服务器准备接受请求]
```

---

## 🔧 工具注册系统

### 自动发现
工具通过每个工具模块中的 `register_tools()` 函数自动发现和注册。

### 注册过程
```python
def register_tools(registry):
    registry.register_tool("execute_database_sql", execute_database_sql)
    registry.register_tool("execute_mysql_sql", lambda sql, **kwargs: execute_database_sql(sql, "mysql", **kwargs))
    registry.register_tool("execute_postgresql_sql", lambda sql, **kwargs: execute_database_sql(sql, "postgresql", **kwargs))
    registry.register_tool("execute_sqlite_sql", lambda sql, **kwargs: execute_database_sql(sql, "sqlite", **kwargs))
```

### 工具别名
许多工具支持别名以保持向后兼容性：
- `execute_mysql_sql` → `execute_database_sql` 使用 `db_type="mysql"`
- `execute_postgresql_sql` → `execute_database_sql` 使用 `db_type="postgresql"`
- `execute_sqlite_sql` → `execute_database_sql` 使用 `db_type="sqlite"`
- `finish` → `terminate`

---

## 🛡️ 安全与防护

### 超时保护
所有工具都实现超时机制以防止挂起操作：
- 数据库查询：60 秒
- Bash 命令：30 秒
- Snowflake 查询：60 秒

### 输出限制
- 最大输出：每次工具调用 2000 字符
- 在行边界智能截断
- 防止内存耗尽

### 错误处理
- 全面的异常捕获
- 详细的错误日志
- 优雅降级

### 资源管理
- 自动连接清理
- 内存高效的结果处理
- 线程池管理

---

## 📈 性能考虑

### 连接池
- 尽可能重用数据库连接
- 连接管理的单例模式
- 类型更改时自动清理

### 内存管理
- 流式结果处理
- 智能截断算法
- 垃圾收集友好

### 并发性
- 线程安全的工具执行
- 异步兼容设计
- 非阻塞 HTTP 响应

---

## 🔍 故障排除

### 常见问题

#### 数据库连接错误
1. 检查凭证文件是否存在且为有效 JSON
2. 验证数据库服务器正在运行且可访问
3. 确认网络连接和防火墙设置

#### 命令执行失败
1. 验证命令语法是否正确
2. 检查工作目录是否存在且可访问
3. 确保有足够的权限执行命令

#### 超时问题
1. 为长时间运行的操作增加超时值
2. 优化查询以获得更好的性能
3. 检查系统资源可用性

### 调试日志
启用调试日志以排除问题：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 健康检查
测试工具可用性：
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_calls": [{"name": "execute_bash", "arguments": {"command": "echo test"}}]}'
```