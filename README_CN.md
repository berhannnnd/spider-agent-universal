# 🕷️ Spider Agent Universal

> 这是从 [Spider2 项目](https://github.com/xlang-ai/Spider2) 中抽象出来的可对话的 Spider Agent，支持多数据库查询和系统命令执行的智能体系统。

[🇨🇳 中文文档](./README_CN.md) | [🇺🇸 English](./README.md)

## 📖 项目简介

Spider Agent Universal 是一个基于客户端-服务器架构的智能体系统，专门用于处理复杂的数据库查询和系统操作任务。它继承了 Spider2 项目的核心能力，并提供了更灵活的对话式交互体验。

### ✨ 主要特性

- 🗄️ **多数据库支持**: MySQL、PostgreSQL、SQLite、Snowflake
- 💻 **系统命令执行**: 安全的 Bash 命令执行环境
- 🔄 **客户端-服务器分离**: 高性能的分布式架构
- 🛡️ **安全保护**: 超时控制、输出限制、错误处理
- 🚀 **高性能**: 连接池管理、异步执行、智能截断

## 🚀 快速开始

### 1. 环境配置

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑 .env 文件，填入您的 API 密钥和配置信息
```

### 2. 数据库凭据配置

在 `credentials/` 目录下创建相应的数据库凭据文件：

```bash
credentials/
├── mysql_credential.json
├── postgresql_credential.json
├── sqlite_credential.json
└── snowflake_credential.json
```

### 3. 启动系统

```bash
# 启动工具服务器
./run_server.sh

# 启动客户端 Agent（新终端窗口）
./run_chat.sh
```

> 💡 提示：可以在 `run_chat.sh` 中修改模型名称

## 🏗️ 系统架构
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   客户端 Agent   │ ──────────────► │   工具服务器     │
│   (llm_agent)   │                │   (serve.py)    │
└─────────────────┘                └─────────────────┘
│                                   │
▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│ 消息处理器       │                │ 工具注册表       │
│(message_processor)│               │(tool_registry)  │
└─────────────────┘                └─────────────────┘
│
▼
┌─────────────────┐
│   工具集合       │
│ • database_tool │
│ • bash_tool     │
│ • snowflake_tool│
│ • terminator_tool│
└─────────────────┘

## 🛠️ 核心工具

### 1. 📊 数据库查询工具 (execute_database_sql)

**功能**: 执行 SQL 查询，支持多种数据库类型

**支持的数据库**:
- MySQL
- PostgreSQL  
- SQLite
- Snowflake

**特性**:
- 连接池管理和复用
- 智能结果截断（2000字符限制）
- CSV 格式输出
- 60秒超时保护

### 2. 💻 系统命令工具 (execute_bash)

**功能**: 安全执行系统 Bash 命令

**特性**:
- 工作目录指定
- 输出捕获（stdout/stderr）
- 30秒超时保护
- 智能输出截断

### 3. ❄️ Snowflake 专用工具 (execute_snowflake_sql)

**功能**: 专门优化的 Snowflake 数据库查询工具

**特性**:
- 专用连接配置
- 优化的超时设置
- 高效的结果处理

### 4. 🏁 任务终止工具 (terminate)

**功能**: 优雅地结束任务并返回最终答案

## 🔧 配置说明

### 环境变量配置 (.env)

```bash
# API 配置
API_HOST=localhost
API_PORT=8000

# 模型配置
MODEL_NAME=your-model-name
API_KEY=your-api-key

# 数据库路径
DATABASES_PATH=./databases
```

### 数据库凭据示例

**MySQL 凭据** (`credentials/mysql_credential.json`):
```json
{
    "host": "localhost",
    "port": 3306,
    "user": "username",
    "password": "password",
    "database": "database_name"
}
```

**Snowflake 凭据** (`credentials/snowflake_credential.json`):
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

## 🛡️ 安全特性

### 超时保护
- 数据库查询：60秒超时
- Bash 命令：30秒超时
- HTTP 请求：30秒超时

### 输出限制
- CSV 结果：2000字符智能截断
- Bash 输出：2000字符智能截断
- 边界截断，避免数据破损

### 错误处理
- 全面的异常捕获
- 详细的错误日志
- 优雅的错误恢复

## 🚀 性能优化

### 连接管理
- 数据库连接池复用
- 全局连接器单例模式
- 自动连接清理

### 异步处理
- 线程池执行（每工具8个worker）
- 异步工具调用
- 非阻塞 HTTP 响应

### 智能截断
- 完整行边界截断
- 避免数据破损
- 保持输出可读性

## 📁 项目结构
spider-agent-universal/
├── agent/                  # 客户端 Agent 代码
│   ├── llm_agent.py       # 主要 Agent 逻辑
│   ├── message_processor.py # 消息处理器
│   └── ...
├── servers/               # 服务器端代码
│   ├── serve.py          # FastAPI 服务器
│   ├── tools/            # 工具实现
│   └── utils/            # 工具注册表
├── prompts/              # 提示词模板
├── credentials/          # 数据库凭据（需自行创建）
├── .env.example         # 环境配置模板
└── requirements.txt     # Python 依赖

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目基于 Spider2 项目开发，请参考原项目的许可证条款。

## 🔗 相关链接

- [Spider2 原项目](https://github.com/xlang-ai/Spider2)
- [Spider2 论文](https://arxiv.org/abs/2411.07763)
- [ICLR 2025 Oral 发表](https://github.com/xlang-ai/Spider2)

---

