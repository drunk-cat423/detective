# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

推理助手 (Detective Assistant) — 面向推理小说/剧情游戏爱好者的辅助工具。用户可在已读内容范围内整理线索、连线推理、与 AI Agent 对话，严格避免剧透。技术栈：Vue 3 + Vite（前端），FastAPI + SQLAlchemy 2.0 异步 + Chroma（后端），DeepSeek API（对话），SiliconFlow BAAI/bge-m3（向量化），BAAI/bge-reranker-base（重排序）。

## 常用命令

### 后端（`backend/`）

**Python 环境**：使用 Conda 环境 `detective`（已有全部依赖，无需重新安装）。

```bash
conda activate detective

# 启动开发服务器
uvicorn app.main:app --reload --port 8001

# 数据库迁移（修改 SQLAlchemy 模型后）
alembic revision --autogenerate -m "描述"
alembic upgrade head

# Swagger 文档
# 访问 http://127.0.0.1:8001/docs
```

### 前端（`frontend/`）

```bash
npm install
npm run dev        # 开发服务器 → http://localhost:5173
npm run build      # 生产构建（含 vue-tsc 类型检查）
```

### 环境变量（`backend/.env`）

必须配置的变量：`DATABASE_URL`（MySQL）、`DEEPSEEK_API_KEY`（对话模型）、`SILICONFLOW_API_KEY`（Embedding 模型）。可选：`RERANKER_MODEL_PATH`（本地重排序模型路径）、`CHROMA_PERSIST_DIRECTORY`、`HF_ENDPOINT`。

## 架构

### 后端分层

```
api/          ← FastAPI 路由层（薄层，只做参数校验、调用 core、存取 DB）
core/         ← 核心逻辑：agent.py（对话引擎）、tools.py（工具定义+执行）、
                vector_store.py（Chroma + Embedding + 重排序）、skill_loader.py（技能系统）
models/       ← SQLAlchemy ORM 模型（9 张表）
schemas/      ← Pydantic 请求/响应模型
```

**关键设计决策：**

- **数据层与运行时层解耦**：对话历史以 `AgentMessage`（纯字典 `{role, content}`）存入 MySQL，运行时的 `chat_with_tools` / `stream_with_tools` 将其转换为 LangChain 的 `HumanMessage`/`AIMessage`。换框架不影响历史数据。
- **工具调用统一入口**：`core/tools.py` 中 `LOCAL_TOOLS_META` 定义所有工具元数据（名称、描述、JSON Schema、Pydantic 校验模型、执行函数、is_remote 标记），`execute_tool()` 统一分发，调用方无需区分本地/远程。MCP 远程工具目前因不稳定已被注释禁用。
- **流式对话的独立会话**：`agent_chat_stream` 端点内部用户消息和助手消息使用与请求注入的 `db` 不同的提交时机——用户消息先提交，生成器内再提交助手消息，避免异步生命周期冲突。
- **Agent 工具调用循环**：`chat_with_tools` 最多循环 1 轮工具调用（`max_iteration=1`），`stream_with_tools` 最多 3 轮。工具调用中间过程对用户不可见，只有最终 AI 回复通过 SSE 流出。如果最后一轮以工具调用结束（`messages[-1]` 不是 `AIMessage`），会再调用一次 LLM 做收口。

### 前端组件树与数据流

```
views/
  HomePage.vue          ← 案件列表首页，通过 caseStore 管理
  CaseDetail.vue        ← 案件详情（主容器，组装所有子组件）

components/
  canvas/NoteCanvas.vue ← Vue Flow 画布（便签节点 + 连线）
  NoteNode.vue          ← 自定义便签节点（Vue Flow 自定义节点）
  sidebar/
    SidePanel.vue       ← 右侧可折叠面板容器
    EditTab.vue         ← 编辑便签内容/颜色/姓名
    ChatTab.vue         ← Agent 对话界面（流式 SSE）
    DocsTab.vue         ← 文档上传
    InfoTab.vue         ← 已知信息管理
  timeline/
    TimelineBar.vue     ← 顶部时间线开关条
    TimelinePanel.vue   ← 时间轴展开内容

composables/            ← 按功能拆分的组合式 API（Vue 3 逻辑复用模式）
  useNotes.ts           ← 便签 + 连线 CRUD + Vue Flow 操作
  useChat.ts            ← 流式对话（fetch + ReadableStream 解析 SSE）
  useTimeline.ts        ← 时间线事件管理
  useDocuments.ts       ← 文档上传
  useKnownInfo.ts       ← 已知信息
```

**关键设计决策：**

- **CaseDetail 是数据枢纽**：所有 composable 在 `CaseDetail.vue` 中初始化并向下通过 props 传递给子组件。子组件通过 `v-model` 和事件向上通信。
- **Vue Flow 使用约束**：父组件中不使用 `useVueFlow()`，改用 `v-model` + 数组直接操作 nodes/edges。连线的 `sourceHandle` 和 `targetHandle` 必须保留，否则多方向连线会消失。
- **流式对话在前端直接 fetch**：`useChat.ts` 不使用 axios，而是用原生 `fetch` + `ReadableStream` 逐块解析 SSE，每收到一个 chunk 追加到 `assistantMsg.content`。

### RAG 检索链路

1. 文档上传 → `RecursiveCharacterTextSplitter` 分块（`chunk_size=1200, chunk_overlap=150`）→ SiliconFlow `BAAI/bge-m3` 向量化 → 存入 Chroma
2. 检索 → Chroma 向量粗召回 `k*2` 条 → 如果候选 > 5 条则走 Cross-Encoder 重排序 → 取 Top-k
3. 候选 ≤ 5 条直接返回；重排序失败自动降级到向量检索结果

### 技能系统

技能以文件夹形式存放在 `backend/skills/`，每个技能一个 `SKILL.md`（YAML frontmatter + Markdown 正文）。`skill_loader.py` 扫描目录提取元数据注入 System Prompt，模型通过 `load_skill` 工具按需加载正文，避免 Prompt 膨胀。技能元数据有缓存，服务启动后只在首次请求时扫描一次。

## 注意事项

- **NumPy 版本**：必须为 1.26.4，Chroma 0.5.0 不兼容 NumPy 2.x 的 `np.float_` 移除。
- **模型 API**：对话使用 `deepseek-v4-flash`，通过 langchain-openai 兼容的 `ChatOpenAI` 客户端调用（base_url 指向 `https://api.deepseek.com`）。代码中变量名 `BAILIAN_BASE_URL` 是历史遗留，实际已迁移到 DeepSeek。
- **Embedding 模型**：使用 SiliconFlow 平台的 `BAAI/bge-m3`，支持多语言。
- **重排序模型**：首次加载需下载约 1.1GB（`sentence-transformers`），建议配置 `RERANKER_MODEL_PATH` 使用本地路径，启动时通过 lifespan 预加载。
- **Vue Flow**：删除便签时需同步清理前端 edges 数组中的关联连线（后端 CASCADE 删除）。
- **时间轴排序**：必须用 `parseEventTime` 数值比较，不能直接用字符串排序。事件时间支持年-月-日-时-分。
- **文档上传**：仅支持 UTF-8 编码的 `.txt` 文件。
- **端口**：后端默认 8001，前端默认 5173。换端口时前端需同步修改 `api/index.ts` 中的 `baseURL`。
