# 🚀 LangChain-RAG-FastAPI-Service (v2.0.0)

## 📋 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [三种运行模式](#三种运行模式)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API 文档](#api-文档)
- [配置说明](#配置说明)
- [部署指南](#部署指南)
- [开发指南](#开发指南)
- [故障排除](#故障排除)
- [联系方式](#联系方式)

## 项目简介

这是一个基于 **FastAPI + LangChain** 构建的企业级 **RAG（检索增强生成）** 智能对话系统，支持本地大模型推理和多种向量数据库。系统采用微服务架构，具备会话持久化、限流熔断、JWT认证和模块化设计等特性，实现全链路离线闭环。

## 核心特性

- **智能问答** 💬：基于 RAG 技术，结合文档检索和大语言模型，提供精准的问答体验
- **会话持久化** 💾：使用 MySQL 存储会话历史，支持长期保存和回溯
- **多语言支持** 🌐：前端集成 i18n，支持中英文界面切换
- **微服务架构** 🏗️：完整的用户认证、限流熔断、全局日志
- **三种运行模式** 🎮：向量模式、LLM模式、完整模式，按需启动
- **高性能** ⚡：基于 FastAPI、vLLM、ChromaDB/Milvus
- **本地推理** 🖥️：支持 vLLM 部署本地开源大模型，摆脱在线 API 依赖
- **两阶段检索** 🔍：向量粗筛 + Cross-Encoder 重排序，提升检索准确率

## 三种运行模式

| 模式 | 描述 | 所需服务 | 适用场景 |
|------|------|----------|----------|
| **模式1** | 向量模式 | FastAPI + ChromaDB + MySQL | 仅需文档检索，不需要LLM推理 |
| **模式2** | LLM模式 | FastAPI + MySQL | 需要AI对话，不需要文档上传 |
| **模式3** | 完整模式 | FastAPI + vLLM + Milvus + Redis + Celery + MySQL | 完整功能，包含文档上传、向量化、RAG检索、LLM推理 |

## 技术架构

```mermaid
flowchart TD
    subgraph "前端层"
        A["用户界面
        (Vue 3)"] -->|发送查询| B["API请求
        (Axios)"]
        C["会话管理
        (Pinia)"] -->|状态管理| B
        D["用户认证
        (Vue Router)"] -->|路由守卫| B
    end

    subgraph "API路由层"
        B -->|REST API| E["聊天路由
        (FastAPI)"]
        E -->|认证| F["认证中间件
        (JWT)"]
        E -->|限流| G["限流控制
        (Redis)"]
        E -->|熔断| H["熔断降级
        (Circuit Breaker)"]
    end

    subgraph "业务服务层"
        E -->|代理查询| I["ChatService
        (Python)"]
        I -->|会话管理| J["SessionManager
        (MySQL)"]
        I -->|RAG检索| K["RagService
        (LangChain)"]
        I -->|向量存储| L["VectorStoreService
        (ChromaDB/Milvus)"]
        I -->|智能代理| M["Agent
        (LangChain)"]
        I -->|文档重排序| N["ReorderService
        (Qwen3-Reranker)"]
    end

    subgraph "数据存储层"
        J -->|存储会话| O["MySQL数据库"]
        L -->|向量存储| P["ChromaDB/Milvus"]
        L -->|文件存储| Q["文件系统"]
        G -->|缓存| R["Redis缓存"]
    end

    subgraph "AI模型服务"
        M -->|LLM调用| S["vLLM (Qwen3-7B)"]
        M -->|LLM调用| T["DashScope API"]
        M -->|LLM调用| U["Ollama Local"]
        K -->|嵌入模型| V["nomic-embed-text
        (Ollama)"]
        N -->|重排序| W["Qwen3-Reranker-0.6B"]
    end

    subgraph "异步任务"
        X["Celery Worker"] -->|文档处理| K
    end
```

## 快速开始

### 环境要求

#### 后端环境
- Python 3.11+
- MySQL 8.0+
- Redis (可选，用于限流熔断)
- Milvus (可选，模式3)
- Ollama (可选，本地嵌入模型)

#### 前端环境
- Node.js 16+
- npm 或 pnpm

### 克隆项目

```bash
git clone https://github.com/huasheng6543/LangChain-RAG-FastAPI-Service-master.git
cd LangChain-RAG-FastAPI-Service-master
```

### 安装依赖

#### 后端依赖
```bash
cd backend

# 创建虚拟环境 (Windows)
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd front

# 安装依赖
npm install
```

### 环境配置

在 `backend` 目录下创建 `.env` 文件：

```env
# DashScope API Key (模式2/3使用)
DASHSCOPE_API_KEY=your_dashscope_api_key

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=chatbot

# Redis配置 (模式3)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# 安全配置
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# vLLM配置 (模式2/3)
VLLM_MODEL_PATH=models/Qwen3-7B-Instruct-AWQ
VLLM_HOST=0.0.0.0
VLLM_PORT=8003

# Reranker模型配置
RERANKER_MODEL_PATH=models/Qwen3-Reranker-0.6B

# Ollama配置
DEEPSEEK_BASE_URL=http://localhost:11434

# LangSmith配置 (可选)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=my-fastapi-langchain-project
```

### 启动服务

#### 一键启动（推荐）

```bash
# Windows
start.bat 1  # 模式1：向量模式
start.bat 2  # 模式2：LLM模式
start.bat 3  # 模式3：完整模式

# Linux/Mac
bash start.sh 1
bash start.sh 2
bash start.sh 3
```

#### 手动启动

```bash
# 模式1：向量模式
cd backend
venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8002

# 模式2：LLM模式
cd backend
venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8002

# 模式3：完整模式 (需要先启动Milvus和Redis)
cd backend
venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

#### 启动前端服务
```bash
cd front
npm run dev
```
前端将在 `http://localhost:3000` 运行。

#### 启动依赖服务

```bash
# MySQL
net start mysql

# Redis
net start redis

# Ollama (本地模型)
ollama serve

# Milvus (模式3，使用Docker)
docker-compose up -d milvus
```

### 下载模型（模式3）

```bash
cd backend
venv\Scripts\activate
python download_models.py
```

下载完成后，模型将保存在 `backend/models/` 目录。

## 技术栈

### 后端技术
| 技术 | 用途 |
|------|------|
| **FastAPI** ⚡ | 高性能异步 Web 框架 |
| **LangChain** 🦜 | 大语言模型应用开发框架 |
| **SQLAlchemy** 🗄️ | ORM 数据库操作 |
| **ChromaDB** 📚 | 轻量级向量数据库（模式1） |
| **Milvus** 🚀 | 分布式向量数据库（模式3） |
| **vLLM** ⚡ | 高性能 LLM 推理引擎 |
| **MySQL** 🗄️ | 关系型数据库 |
| **Redis** ⚡ | 缓存和限流 |
| **Celery** 🧵 | 异步任务处理 |
| **JWT** 🔑 | 用户认证 |
| **DashScope API** 🔑 | 阿里云大模型服务 |
| **Ollama** 🐑 | 本地模型运行 |

### 前端技术
| 技术 | 用途 |
|------|------|
| **Vue 3** 🖼️ | 现代化前端框架 |
| **Vite** ⚡ | 极速构建工具 |
| **Vue Router** 🛣️ | 路由管理 |
| **Pinia** 📦 | 状态管理 |
| **Vant** 🎨 | 移动端 UI 组件库 |
| **i18n** 🌍 | 国际化支持 |

## 项目结构

```
├── backend/                  # FastAPI 后端服务
│   ├── app/                  # 应用代码
│   │   ├── agent/            # 智能代理模块
│   │   ├── config/           # 配置文件目录
│   │   ├── core/             # 核心组件 (限流、熔断、权限)
│   │   ├── db/               # 数据库配置
│   │   ├── llm/              # LLM 适配器
│   │   ├── models/           # 数据模型定义
│   │   ├── rag/              # RAG 核心功能
│   │   ├── router/           # API 路由定义
│   │   ├── tasks/            # Celery 异步任务
│   │   └── utils/            # 工具函数
│   ├── models/               # 本地模型目录
│   ├── main.py               # 应用入口文件
│   ├── start_server.py       # 启动脚本
│   ├── requirements.txt      # 后端依赖列表
│   └── download_models.py    # 模型下载脚本
├── front/                    # Vue 前端项目
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 可复用组件
│   │   ├── store/            # Pinia 状态管理
│   │   ├── router/           # 路由配置
│   │   └── utils/            # 工具函数
│   ├── public/               # 静态资源
│   ├── package.json          # 前端依赖配置
│   └── vite.config.js        # Vite 配置
├── docker-compose.yml        # Docker 部署配置
├── start.bat                 # Windows 一键启动脚本
├── start.sh                  # Linux/Mac 一键启动脚本
├── stop.bat                  # Windows 停止脚本
├── stop.sh                   # Linux/Mac 停止脚本
└── README.md                 # 项目说明文档
```

## API 文档

### FastAPI 后端 API
- **交互式文档**: http://localhost:8002/docs
- **Redoc 文档**: http://localhost:8002/redoc

### 核心接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取当前用户 |
| `/api/chat/stream` | POST | 流式聊天 |
| `/api/chat/query` | POST | 非流式聊天 |
| `/api/vector/add` | POST | 添加文档向量 |
| `/api/vector/search` | POST | 向量检索 |
| `/api/vector/clean` | DELETE | 清空向量库 |

## 配置说明

### 运行模式配置

在 `backend/.env` 文件中配置运行模式：

```env
# 运行模式: 1=向量模式, 2=LLM模式, 3=完整模式
RUN_MODE=2
```

### 向量数据库配置

在 `backend/app/config/rag.yaml` 中配置：

```yaml
# 聊天模型配置
chat_model_name: qwen3-max

# 文本嵌入模型配置
text_embedding_model_name: text-embedding-v4

# 向量数据库配置
vector_db: chromadb

# 文档切分配置
chunk_size: 200
chunk_overlap: 20
```

## 部署指南

### 使用 Docker

```bash
# 启动全部服务
docker-compose up -d

# 启动特定服务
docker-compose up -d fastapi redis milvus
```

### 生产环境部署

1. **安装依赖**: 参考快速开始
2. **配置环境变量**: 创建 `.env` 文件
3. **启动服务**: 使用 `start.bat` 或 `start.sh`
4. **配置反向代理**: 使用 Nginx 或 Caddy

## 开发指南

### 代码结构说明
- **backend/app/rag/**：RAG 核心功能，包括向量存储和检索
- **backend/app/agent/**：智能代理，处理用户请求和对话逻辑
- **backend/app/core/**：核心组件，限流、熔断、权限控制
- **backend/app/llm/**：LLM 适配器，支持多种模型
- **backend/app/router/**：API 路由定义
- **front/src/views/**：前端页面组件
- **front/src/components/**：可复用的前端组件

### 开发流程
1. **添加新功能**
   - 在对应的模块中添加代码
   - 运行测试确保功能正常
   - 更新相关文档
2. **调试技巧**
   - 使用 FastAPI 的自动重载功能：`uvicorn main:app --reload`
   - 使用 Vue 的热更新功能：`npm run dev`

## 故障排除

### 常见问题

1. **服务启动失败**
   - 检查端口是否被占用
   - 检查 MySQL/Redis 服务是否启动
   - 检查 `.env` 文件配置是否正确

2. **前端连接后端失败**
   - 检查后端服务是否在运行
   - 检查 Vite 代理配置 (`vite.config.js`)
   - 检查浏览器控制台错误信息

3. **模型加载失败**
   - 检查模型文件是否下载完成
   - 检查模型路径配置是否正确
   - 检查 vLLM 是否正确安装

4. **401 认证错误**
   - 检查 JWT Token 是否过期
   - 检查登录状态是否正常
   - 重新登录获取新 Token

## 联系方式

如有任何问题或建议，请随时联系我们。😊

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！
