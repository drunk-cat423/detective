# 推理助手 (Detective Assistant)

一个面向推理小说/剧情游戏爱好者的辅助工具，允许用户在已读内容范围内进行线索整理和推理辅助，严格避免剧透。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Vue Router + @vue-flow/core + Axios + marked |
| 后端 | FastAPI (异步) + Pydantic V2 + SQLAlchemy 2.0 (异步) + MySQL 8.0 |
| AI 模型 | DeepSeek API（deepseek-v4-flash，对话）、SiliconFlow BAAI/bge-m3（向量化） |
| Agent 框架 | LangChain + langchain-openai（ChatOpenAI 兼容客户端）+ 原生 MCP SDK（已禁用） |
| 向量数据库 | Chroma（持久化存储） |
| 重排序 | SiliconFlow BAAI/bge-reranker-v2-m3（Cross-Encoder 精排，API 调用） |
| 开发工具 | PyCharm (后端) + VS Code (前端) + Navicat (数据库) |

## 目录结构

```
detective-assistant/
├── frontend/                # Vue 3 项目
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomePage.vue       # 案件管理首页
│   │   │   └── CaseDetail.vue     # 案件详情（便签墙+连线+时间轴+侧边栏+Agent对话+文档上传+已知信息）
│   │   ├── components/
│   │   │   └── NoteNode.vue       # 自定义便利贴节点
│   │   ├── api/index.ts           # axios 封装 + 所有 API 接口
│   │   ├── stores/                # Pinia 状态管理
│   │   ├── router/index.ts        # 路由配置
│   │   ├── App.vue
│   │   └── main.ts
│   ├── vite.config.ts
│   └── package.json
│
├── backend/                 # FastAPI 项目
│   ├── app/
│   │   ├── main.py                # FastAPI 入口（lifespan 预加载模型）
│   │   ├── config.py              # 环境变量配置（Pydantic Settings）
│   │   ├── database.py            # 异步数据库连接（aiomysql）
│   │   ├── models/                # SQLAlchemy 模型（9 张表）
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── api/                   # 路由模块
│   │   │   ├── cases.py           # 案件 CRUD
│   │   │   ├── notes.py           # 便签 CRUD（含 name 字段）
│   │   │   ├── connections.py     # 连线 CRUD
│   │   │   ├── timeline.py        # 时间线 CRUD + 排序
│   │   │   ├── agent.py           # Agent 对话（普通 + 真流式 SSE）
│   │   │   ├── documents.py       # 文档上传 + 向量化
│   │   │   └── known_infos.py     # 已知信息 CRUD
│   │   └── core/                  # 核心逻辑
│   │       ├── agent.py           # Agent 引擎（DeepSeek + RAG + 工具调用循环）
│   │       ├── vector_store.py    # Chroma 向量库 + Embedding + 重排序
│   │       ├── tools.py           # 本地工具定义与统一执行入口（MCP 已禁用）
│   │       └── skill_loader.py    # 技能系统（YAML frontmatter 插件化）
│   ├── alembic/                   # 数据库迁移
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

## 数据库设计

- MySQL 8.0+
- 字符集 `utf8mb4`
- Alembic 管理迁移

### 9 张表

| 表名 | 说明 | 状态 |
|------|------|------|
| `cases` | 案件 | ✅ |
| `notes` | 便签（线索/嫌疑人） | ✅ |
| `connections` | 连线 | ✅ |
| `documents` | 上传文本（仅存 Chroma，MySQL 表已弃用） | ✅ |
| `known_infos` | 已知信息 | ✅ |
| `agent_messages` | Agent 对话记录 | ✅ |
| `skills` | 技能模板 | ✅ 框架完成 |
| `case_skill_link` | 案件-技能关联 | ✅ |
| `timeline_events` | 时间线事件 | ✅ |

## 核心功能

### 1. 案件管理
- 新建案件、案件列表展示
- 点击案件卡片进入详情页，支持删除案件

### 2. 便签墙（Vue Flow 画布）
- 添加线索/嫌疑人便签，自由拖拽移动
- 嫌疑人便签额外显示 **姓名**（可编辑）
- 便签位置、尺寸、颜色自动保存
- 便签间拖拽连线（上下两个美化 Handle）
- 连线自动保存，删除便签时自动清理关联连线
- 右下角按钮：一键回到画布中心点

### 3. 右侧工具面板
- 可折叠/展开（宽度 380px）
- **编辑** / **对话** / **文档** / **已知信息** 四个 Tab 切换
- 编辑 Tab：修改内容、切换预设颜色（8 种）、修改嫌疑人姓名
- 已知信息 Tab：录入关键信息，供 Agent 推理时调用
- 文档 Tab：支持拖拽或点击上传 `.txt` 文件，显示已上传文档列表

### 4. 文档上传与向量化（RAG）
- 前端：文档 Tab 内提供文件拖拽/选择上传组件，支持 `.txt` 文件（UTF-8 编码）
- 后端：接收文件 → 递归字符分块（优先级：段落→句子→词组）→ 调用 `BAAI/bge-m3` 向量化 → 存入 Chroma 向量库
- 分块策略：`chunk_size=250`, `chunk_overlap=50`（子块做索引，检索时按命中块前后邻居拼上下文窗口）
- 同文件名上传为替换语义（先删旧块再写入），避免重复上传产生脏数据
- 文档信息（文件名、分块数）直接从 Chroma metadata 查询，不再使用 MySQL 表
- **文档删除**：支持在文档 Tab 中删除已上传文档，同步清理 Chroma 中的向量

### 5. RAG 检索（两阶段检索 + 重排序）
- **第一阶段（粗召回）**：Chroma 向量检索，召回 Top-k×2 候选文档
- **第二阶段（精排）**：SiliconFlow BAAI/bge-reranker-v2-m3 Cross-Encoder 重排序，取 Top-k
- **优化策略**：
  - 粗召回量取目标返回量的 2 倍，扩大候选空间保证召回率
  - 重排序失败时自动回退到向量检索，保证服务可用性
  - 模型支持本地路径加载，避免生产环境依赖 HuggingFace 网络

### 6. Agent 对话（真流式输出）
- **真流式 SSE**：`llm.astream()` 逐字输出，非伪流式
- **工具调用循环**：
  - 普通对话最多循环 1 轮，流式对话最多循环 3 轮，自动调用工具获取信息
  - 本地工具：`search_notes`、`get_timeline`、`get_known_infos`、`search_documents`、`load_skill`、`record_finding`
  - 工具调用中间过程对用户不可见，只流式输出最终回答
- **RAG 检索**：自动从已上传文档中检索相关片段，注入 Prompt
- **受限推理**：仅基于当前案件的便签、时间线、已知信息、相关文本片段
- **三层记忆系统**：
  - **MySQL 原始对话**：自动保存，每次对话携带最近 10 轮历史（流式）/ 20 轮（普通）
  - **Chroma 记忆摘要 + 画像**：当总轮数 > 30 时，后台自动将旧对话压缩为摘要存入 `memory_store`，同时更新用户画像和 AI 画像（跨案件持久化）
  - **已知信息（推理记录）**：AI 通过 `record_finding` 工具自动将关键推理结论写入 `known_infos` 表，用户可在已知信息 Tab 中查看和编辑
- **记忆工作流程**：
  1. 用户发消息 → 正常流式回复 → SSE 结束
  2. 后台 `asyncio.create_task(summarize_and_prune)` 触发摘要
  3. 一次 DeepSeek 调用同时产出：对话摘要 + 用户画像更新 + AI 画像更新
  4. 摘要和画像写入 Chroma `memory_store`，旧消息从 MySQL 删除
  5. Per-case 锁防止重复摘要，用户全程无感知
- **Prompt 结构**（固定顺序）：
  `[系统提示词]` → `[技能列表]` → `[AI画像]` → `[用户画像]` → `[相关记忆]` → `[近期对话]` → `[当前输入]`
- **独立会话生命周期**：流式写入使用独立数据库会话，避免异步生命周期问题

### 7. 技能系统（插件化设计）
- 技能以文件夹形式组织，每个技能包含 `SKILL.md`
- YAML frontmatter 定义元数据（名称、描述、版本、所需工具）
- Markdown 正文定义推理工作流/剧本
- 模型通过 `load_skill` 工具按需加载，避免 Prompt 膨胀
- 技能元数据动态注入 System Prompt，让模型知道有哪些技能可用

### 8. 登录鉴权
- 简单密码认证，支持 `.env` 配置开关（`AUTH_ENABLED=true/false`）
- 后端 JWT Token（7 天有效期），前端自动携带并处理 401 跳转
- 独立登录页面，路由守卫自动检查登录状态

### 9. 时间线（可视化时间轴）
- 年-月-日-时-分选择器添加事件，输入自动修正
- 横轴时间轴，圆点标记事件，按时间自动分布（智能间距防重叠）
- 悬停显示详情框，移开消失；点击锁定，可同时锁定多个
- 左右两侧智能对齐，不超出边界
- 圆点下方显示月/日简写

## 环境准备

### 后端

1. 安装 Python 3.10+（推荐 Conda）
2. 进入 `backend/` 目录：

```bash
pip install -r requirements.txt
```

**注意**：需降级 NumPy 至 1.26.4 以兼容 Chroma：

```bash
pip install numpy==1.26.4
```

3. 复制 `.env.example` 为 `.env`，填写配置：

```bash
DATABASE_URL=mysql+aiomysql://用户名:密码@localhost:3306/detective_db
DEEPSEEK_API_KEY=你的DeepSeek_API_KEY
SILICONFLOW_API_KEY=你的硅基流动API_KEY
CHROMA_PERSIST_DIRECTORY=./chroma_data
SECRET_KEY=任意随机字符串
```

4. 启动：

```bash
uvicorn app.main:app --reload --port 8001
```

5. Swagger 文档：`http://127.0.0.1:8001/docs`

### 前端

1. 安装 Node.js 18+
2. 进入 `frontend/` 目录：

```bash
npm install
npm run dev
```

3. 访问：`http://localhost:5173`

## 快速启动清单

1. 确保 MySQL 运行，数据库 `detective_db` 已创建
2. `.env` 已配置 `DEEPSEEK_API_KEY` 和 `SILICONFLOW_API_KEY`
3. `cd backend && uvicorn app.main:app --reload --port 8001`
4. `cd frontend && npm run dev`
5. 浏览器打开 `http://localhost:5173`
6. 创建案件 → 进入详情 → 切换至"文档"Tab 上传 `.txt` 文件 → 在"对话"Tab 提问基于文档内容的问题

## 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/cases/` | 案件列表/创建 |
| GET/POST | `/cases/{id}/notes` | 便签列表/创建 |
| PUT/DEL | `/cases/{id}/notes/{note_id}` | 更新/删除便签 |
| GET/POST | `/cases/{id}/connections` | 连线列表/创建 |
| PUT/DEL | `/cases/{id}/connections/{conn_id}` | 更新/删除连线 |
| GET/POST | `/cases/{id}/timeline/` | 时间线列表/创建 |
| PUT | `/cases/{id}/timeline/{event_id}/move` | 移动排序 |
| PUT/DEL | `/cases/{id}/timeline/{event_id}` | 更新/删除事件 |
| POST | `/cases/{id}/agent/chat` | Agent 普通对话 |
| POST | `/cases/{id}/agent/chat/stream` | Agent 真流式对话（SSE） |
| GET | `/cases/{id}/agent/history` | 对话历史 |
| DELETE | `/cases/{id}/agent/history` | 清空历史 |
| POST | `/cases/{id}/documents/upload` | 上传文档 |
| GET | `/cases/{id}/documents/` | 获取文档列表 |
| DELETE | `/cases/{id}/documents/{filename}` | 删除文档 |
| GET/POST | `/cases/{id}/known-infos` | 已知信息列表/创建 |
| PUT/DEL | `/cases/{id}/known-infos/{info_id}` | 更新/删除已知信息 |

## 技术亮点

### 1. 真流式输出 + 工具调用隔离
- 工具调用循环在后台同步完成，用户无感知
- 最终回答通过 `llm.astream()` 真流式输出，逐字渲染
- 避免伪流式的等待延迟，提升用户体验

### 2. 两阶段 RAG 检索（向量 + 重排序）
- 向量检索粗召回保证召回率
- Cross-Encoder 精排保证相关性
- 小数据量自动跳过重排序，失败自动降级

### 3. 技能系统插件化
- YAML + Markdown 定义技能，无需改代码即可扩展推理能力
- 按需加载，避免 Prompt 膨胀
- 技能与工具解耦，技能是"工作流"，工具是"能力"

### 4. 统一工具执行入口
- 所有工具通过 `execute_tool()` 统一分发，调用方无感知
- 工具元数据集中定义在 `LOCAL_TOOLS_META`，包含名称、描述、JSON Schema、Pydantic 校验模型和执行函数
- 架构上预留了 `is_remote` 标记支持远程工具扩展（MCP 目前因稳定性问题已禁用）

### 5. 数据层与运行时层解耦
- 数据库用简单的 `AgentMessage` 存原始数据
- 运行时通过适配器转换成 LangChain 的 `HumanMessage`/`AIMessage`
- 换框架不影响历史数据

## 已知注意事项

1. **端口占用**：如 8001 被占用，换端口启动，前端同步修改 `api/index.ts` 的 `baseURL`
2. **Python 缓存**：修改 Model 后需删除 `__pycache__` 文件夹并重启
3. **NumPy 版本**：必须固定为 1.26.4，否则 Chroma 报错 `np.float_` 不存在
4. **数据库迁移**：修改 SQLAlchemy 模型后执行 `alembic revision --autogenerate -m "描述"` 和 `alembic upgrade head`
5. **Vue Flow 使用**：父组件中禁用 `useVueFlow()`，改用 `v-model` + 数组直接操作
6. **连线 Handle**：必须保留 `sourceHandle` 和 `targetHandle`，否则多方向连线会消失
7. **时间轴排序**：必须用 `parseEventTime` 数值比较，不能直接用字符串排序
8. **嫌疑人姓名**：涉及 `NoteCreate`、`NoteUpdate`、`NoteOut` 三个 Schema 及数据库列，缺一不可
9. **流式对话会话安全**：`agent_chat_stream` 内部用独立 `async_session()` 保存助手消息
10. **文档上传**：仅支持 UTF-8 编码的 `.txt` 文件，单次上传大小受 FastAPI 默认限制（16MB）
11. **MCP 调用**：MCP 远程工具目前已被禁用（注释掉），因其输出不稳定，与提问内容无关
12. **重排序模型**：经 SiliconFlow Rerank API 调用 `BAAI/bge-reranker-v2-m3`，需配置 `SILICONFLOW_API_KEY`；调用失败时自动降级为向量检索结果

## 后续规划

1. **混合检索** — BM25 + 向量双路召回，RRF 融合排序
2. **时间线自动生成** — 利用 Agent 从便签/文档中自动提取时间线事件
3. **UI 美化** — 整体视觉优化、头像替换为实际图片
4. **Docker 部署** — 镜像预装模型，一键部署
5. **模型服务化** — 重排序拆成独立服务，多实例共用
