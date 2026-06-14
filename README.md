# 推理助手 (Detective Assistant)

一个面向推理小说/剧情游戏爱好者的辅助工具，允许用户在已读内容范围内进行线索整理和推理辅助，严格避免剧透。

---

## 技术栈

| 层级       | 技术                                                         |
| ---------- | ------------------------------------------------------------ |
| 前端       | Vue 3 + Vite + TypeScript + Pinia + Vue Router + @vue-flow/core + Axios + marked |
| 后端       | FastAPI (异步) + Pydantic V2 + SQLAlchemy 2.0 (异步) + MySQL 8.0 |
| AI 模型    | 阿里云百炼 Qwen3-Max（对话）、text-embedding-v4（向量化）       |
| Agent 框架 | LangChain（仅用于消息格式与流式）+ DashScope 原生 Embedding  +MCP 原生客户端   |
| 向量数据库 | Chroma（持久化存储，单例 embeddings）                          |
| 开发工具   | PyCharm (后端) + VS Code (前端) + Navicat (数据库)            |

---

## 目录结构

```
detective-assistant/
├── frontend/                # Vue 3 项目
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomePage.vue       # 案件管理首页
│   │   │   └── CaseDetail.vue     # 案件详情（便签墙+连线+时间轴+侧边栏+Agent对话+文档上传）
│   │   ├── components/
│   │   │   └── NoteNode.vue       # 自定义便利贴节点
│   │   ├── api/index.ts           # axios 封装 + 所有 API 接口（含文档上传）
│   │   ├── router/index.ts        # 路由配置
│   │   ├── stores/                # Pinia（待用）
│   │   ├── App.vue
│   │   └── main.ts
│   ├── vite.config.ts
│   └── package.json
│
├── backend/                 # FastAPI 项目
│   ├── app/
│   │   ├── main.py                # FastAPI 入口（已注册文档路由）
│   │   ├── config.py              # 环境变量配置（含 DASHSCOPE_API_KEY）
│   │   ├── database.py            # 异步数据库连接
│   │   ├── models/                # SQLAlchemy 模型（9 张表）
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── api/                   # 路由模块
│   │   │   ├── cases.py           # 案件 CRUD
│   │   │   ├── notes.py           # 便签 CRUD（含 name 字段）
│   │   │   ├── connections.py     # 连线 CRUD
│   │   │   ├── timeline.py        # 时间线 CRUD + 排序
│   │   │   ├── agent.py           # Agent 对话（普通 + 流式 SSE）
│   │   │   └── documents.py       # 文档上传 + 向量化（新增）
│   │   └── core/                  # 核心逻辑
│   │       ├── agent.py           # Agent 引擎（Qwen3-Max + RAG + 智能历史截断）
│   │       └── vector_store.py    # Chroma 向量库操作（text-embedding-v4）
│   ├── alembic/                   # 数据库迁移（版本 836f23434fd6）
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## 数据库要求

- MySQL 8.0+
- 需要创建空数据库 `detective_db`（字符集 `utf8mb4`）
- Alembic 迁移版本号为 `836f23434fd6`

### 数据库表（9 张）

| 表名             | 说明                 | 状态                                  |
| ---------------- | -------------------- | ------------------------------------- |
| `cases`          | 案件                 | ✅                                     |
| `notes`          | 便签（线索/嫌疑人）  | ✅ 增加 `name` 字段                    |
| `connections`    | 连线                 | ✅                                     |
| `documents`      | 上传文本             | ✅ **已启用**（上传 + 向量化）          |
| `known_infos`    | 已知信息             | ✅ 表已建，录入功能待前端接入          |
| `agent_messages` | Agent 对话记录       | ✅                                     |
| `skills`         | 技能模板             | ✅ 待接入                              |
| `case_skill_link`| 案件-技能关联        | ✅ 待接入                              |
| `timeline_events`| 时间线事件           | ✅                                     |

---

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
   ```
   DATABASE_URL=mysql+aiomysql://用户名:密码@localhost:3306/detective_db
   DASHSCOPE_API_KEY=你的阿里云百炼API_KEY
   CHROMA_PERSIST_DIRECTORY=./chroma_data
   SECRET_KEY=任意随机字符串
   ```
4. 启动：
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. Swagger 文档：`http://127.0.0.1:8000/docs`

### 前端

1. 安装 Node.js 18+
2. 进入 `frontend/` 目录：
   ```bash
   npm install
   npm run dev
   ```
3. 访问：`http://localhost:5173`

---

## 已完成功能

### 案件管理
- 新建案件、案件列表展示
- 点击案件卡片进入详情页，支持删除案件

### 便签墙（Vue Flow 画布）
- 添加线索/嫌疑人便签，自由拖拽移动
- 嫌疑人便签额外显示**姓名**（可编辑）
- 便签位置、尺寸、颜色自动保存
- 便签间拖拽连线（上下两个美化 Handle）
- 连线自动保存，删除便签时自动清理关联连线
- 右下角按钮：一键回到画布中心点

### 右侧工具面板
- 可折叠/展开（宽度 380px）
- **编辑**与**对话**与**文档**三个 Tab 切换
- 编辑 Tab：修改内容、切换预设颜色（8 种）、修改嫌疑人姓名
- 保存/删除便签
- 文档 Tab（新增）：支持拖拽或点击上传 `.txt` 文件，显示已上传文档列表

### 文档上传与向量化（新完成功能）✨
- **前端**：文档 Tab 内提供文件拖拽/选择上传组件，支持 `.txt` 文件（UTF-8 编码）
- **后端**：接收文件 → 按字符分块（500字符，重叠50）→ 调用 `text-embedding-v4` 向量化 → 存入 Chroma 向量库
- 同时记录文档信息到 `documents` 表（文件名、完整内容、分块数量）
- 上传成功后，Agent 对话中的 RAG 检索会自动包含相关文本片段

### 时间线（可视化时间轴）
- 年-月-日-时-分选择器添加事件，输入自动修正
- 横轴时间轴，圆点标记事件，按时间自动分布（智能间距防重叠）
- 悬停显示详情框，移开消失；点击锁定，可同时锁定多个
- × 关闭详情，删除事件按钮（红色）
- 左右两侧智能对齐，不超出边界
- 圆点下方显示月/日简写

### Agent 对话（完整实现）
- **流式输出**：SSE 格式，打字机效果，Markdown 实时渲染
- **RAG 检索**：Chroma 向量库 + text-embedding-v4，基于提问从已上传文档中检索相关片段
- **受限推理**：仅基于当前案件的便签、时间线、已知信息、相关文本片段
- **对话历史**：自动保存，每次对话携带最近 10 轮历史（智能成对截取）
- **独立会话生命周期**：流式写入使用独立数据库会话
- 用户/AI 气泡左右分布，预留头像位置
- 调用阿里云百炼 Qwen3-Max 模型

### 工具调用
- **本地工具调用**: 在tool.py中编写对应的工具,将提取便签信息,提取时间线事件,提取已知信息等功能加入工具模块 避免一次性注入提示词
- **mcp工具调用**: 调用ModelScope社区的必应搜索功能,必要时检索相关资料,但是搜索稳定性较差

### 后端 API

| 方法     | 路径                                     | 说明                     |
| -------- | ---------------------------------------- | ------------------------ |
| GET/POST | `/cases/`                                | 案件列表/创建            |
| GET/POST | `/cases/{id}/notes`                      | 便签列表/创建            |
| PUT/DEL  | `/cases/{id}/notes/{note_id}`            | 更新/删除便签            |
| GET/POST | `/cases/{id}/connections`                | 连线列表/创建            |
| PUT/DEL  | `/cases/{id}/connections/{conn_id}`      | 更新/删除连线            |
| GET/POST | `/cases/{id}/timeline/`                  | 时间线列表/创建          |
| PUT      | `/cases/{id}/timeline/{event_id}/move`   | 移动排序                 |
| PUT/DEL  | `/cases/{id}/timeline/{event_id}`        | 更新/删除事件            |
| POST     | `/cases/{id}/agent/chat`                 | Agent 普通对话           |
| POST     | `/cases/{id}/agent/chat/stream`          | Agent 流式对话（SSE）    |
| GET      | `/cases/{id}/agent/history`              | 对话历史                 |
| DELETE   | `/cases/{id}/agent/history`              | 清空历史                 |
| POST     | `/cases/{id}/documents/upload`           | **上传文档（新）**       |
| GET      | `/cases/{id}/documents/`                 | **获取文档列表（新）**   |

---

## 待实现功能


1. **技能管理** — 预置推理技能（动机分析、时间线梳理等）+ 用户自定义
2. **时间线自动生成** — 利用 Agent 从便签/文档中自动提取时间线事件
3. **UI 美化** — 整体视觉优化、头像替换为实际图片
4. **性能优化** — 大规模文档下的向量检索优化、历史消息分页加载

---

## 已知注意事项

1. **端口占用**：如 8000 被占用，换端口启动（如 `--port 8001`），前端同步修改 `api/index.ts` 的 `baseURL`。
2. **Python 缓存**：修改 Model 后需删除 `__pycache__` 文件夹并重启。
3. **NumPy 版本**：必须固定为 1.26.4，否则 Chroma 报错 `np.float_` 不存在。
4. **数据库迁移**：修改 SQLAlchemy 模型后执行 `alembic revision --autogenerate -m "描述"` 和 `alembic upgrade head`。
5. **Vue Flow 使用**：父组件中禁用 `useVueFlow()`，改用 `v-model` + 数组直接操作。
6. **连线 Handle**：必须保留 `sourceHandle` 和 `targetHandle`，否则多方向连线会消失。
7. **时间轴排序**：必须用 `parseEventTime` 数值比较，不能直接用字符串排序。
8. **嫌疑人姓名**：涉及 `NoteCreate`、`NoteUpdate`、`NoteOut` 三个 Schema 及数据库列，缺一不可。
9. **流式对话会话安全**：`agent_chat_stream` 内部用独立 `async_session()` 保存助手消息。
10. **文档上传**：仅支持 UTF-8 编码的 `.txt` 文件，单次上传大小受 FastAPI 默认限制（16MB）；分块大小为 500 字符，重叠 50 字符，可根据需要调整。
11. **mcp调用** : mcp工具不太稳定,有时输出结果跟提问的内容毫无关系.

---

## 快速启动清单

1. 确保 MySQL 运行，数据库 `detective_db` 已创建
2. `.env` 已配置 `DASHSCOPE_API_KEY`
3. `cd backend && uvicorn app.main:app --reload --port 8001`
4. `cd frontend && npm run dev`
5. 浏览器打开 `http://localhost:5173`
6. 创建案件 → 进入详情 → 切换至“文档”Tab 上传 `.txt` 文件 → 在“对话”Tab 提问基于文档内容的问题

---
