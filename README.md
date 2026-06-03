# 推理助手 (Detective Assistant)

一个面向推理小说/剧情游戏爱好者的辅助工具，允许用户在已读内容范围内进行线索整理和推理辅助，严格避免剧透。

---

## 技术栈

| 层级       | 技术                                                         |
| ---------- | ------------------------------------------------------------ |
| 前端       | Vue 3 + Vite + TypeScript + Pinia + Vue Router + @vue-flow/core + Axios + marked |
| 后端       | FastAPI (异步) + Pydantic V2 + SQLAlchemy 2.0 (异步) + MySQL 8.0 |
| AI 模型    | 阿里云百炼 Qwen3-Max（兼容 OpenAI API）                       |
| Agent 框架 | LangChain + LangChain-OpenAI                                  |
| 向量数据库 | Chroma（Embedding: text-embedding-v3）                        |
| 开发工具   | PyCharm (后端) + VS Code (前端) + Navicat (数据库)            |

---

## 目录结构

```
detective-assistant/
├── frontend/                # Vue 3 项目 (VS Code 打开)
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomePage.vue       # 案件管理首页
│   │   │   └── CaseDetail.vue     # 案件详情（便签墙+连线+时间轴+侧边栏+Agent对话）
│   │   ├── components/
│   │   │   └── NoteNode.vue       # 自定义便利贴节点（支持显示嫌疑人名字）
│   │   ├── router/index.ts        # 路由配置
│   │   ├── api/index.ts           # axios 封装 + 所有 API 接口
│   │   ├── stores/                # Pinia（待用）
│   │   ├── App.vue
│   │   └── main.ts
│   ├── vite.config.ts
│   └── package.json
│
├── backend/                 # FastAPI 项目 (PyCharm 打开)
│   ├── app/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # 环境变量配置（含 DASHSCOPE_API_KEY）
│   │   ├── database.py            # 异步数据库连接
│   │   ├── models/                # SQLAlchemy 模型（9 张表，notes 增加 name 字段）
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── api/                   # 路由模块
│   │   │   ├── cases.py           # 案件 CRUD
│   │   │   ├── notes.py           # 便签 CRUD（含 name 字段处理）
│   │   │   ├── connections.py     # 连线 CRUD
│   │   │   ├── timeline.py        # 时间线 CRUD + 排序
│   │   │   └── agent.py           # Agent 对话（普通 + 流式 SSE）
│   │   └── core/                  # 核心逻辑
│   │       ├── agent.py           # Agent 引擎（Qwen3-Max + RAG + 智能历史截断）
│   │       └── vector_store.py    # Chroma 向量库操作（单例 embeddings，异常处理）
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
| `notes`          | 便签（线索/嫌疑人）  | ✅ 增加 `name` 字段（varchar 100）     |
| `connections`    | 连线                 | ✅                                     |
| `documents`      | 上传文本             | ✅ 表已建，上传功能待前端接入          |
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
- 点击案件卡片进入详情页

### 便签墙（Vue Flow 画布）
- 添加线索/嫌疑人便签，自由拖拽移动
- 嫌疑人便签额外显示**姓名**（加粗，可编辑）
- 便签位置、尺寸、颜色自动保存
- 便签间拖拽连线（上下两个美化 Handle）
- 连线自动保存，删除便签时自动清理关联连线
- 右下角按钮：一键回到画布中心点

### 右侧工具面板
- 可折叠/展开（宽度 380px，折叠后 40px）
- **编辑**与**对话**两个 Tab 切换
- 编辑 Tab：修改内容、切换预设颜色（8 种）、修改嫌疑人姓名
- 保存/删除便签

### 时间线（可视化时间轴）
- 年-月-日-时-分选择器添加事件，输入自动修正（如 41 日→31 日）
- 横轴时间轴，圆点标记事件，按时间自动分布（智能间距防重叠）
- 悬停显示详情框，移开消失；点击锁定，可同时锁定多个
- × 关闭详情，删除事件按钮（红色）
- 左右两侧智能对齐，不超出边界
- 圆点下方显示月/日简写

### Agent 对话（完整实现）
- **流式输出**：SSE 格式，打字机效果，Markdown 实时渲染
- **RAG 检索**：Chroma 向量库 + text-embedding-v3，基于提问从已上传文档中检索相关片段
- **受限推理**：仅基于当前案件的便签、时间线、已知信息、相关文本片段
- **对话历史**：自动保存，每次对话携带最近 10 轮历史（智能成对截取）
- **独立会话生命周期**：流式写入使用独立数据库会话，避免外层清理导致异常
- 用户/AI 气泡左右分布，预留头像位置（可自定义图片）
- 调用阿里云百炼 Qwen3-Max 模型

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
| POST     | `/cases/{id}/agent/chat/stream`          | **Agent 流式对话（SSE）** |
| GET      | `/cases/{id}/agent/history`              | 对话历史                 |
| DELETE   | `/cases/{id}/agent/history`              | 清空历史                 |

---

## 待实现功能

1. **文件上传** — 前端上传 .txt，自动分块 + 向量化存入 Chroma，触发 RAG
2. **已知信息录入** — 手动输入汇总信息
3. **连线备注编辑** — 双击连线或选中后在面板编辑 label
4. **技能管理** — 预置推理技能（动机分析、时间线梳理等）+ 用户自定义
5. **UI 美化** — 整体视觉优化、头像替换为实际图片
6. **性能优化** — 大规模文档下的向量检索优化、历史消息分页加载

---

## 已知注意事项

1. **端口占用**：如 8000 被僵尸进程占用，用 `netstat -ano | findstr :8000` 检查，换端口启动（如 `--port 8001`），前端同步修改 `api/index.ts` 的 `baseURL`。
2. **Python 缓存**：修改 Model 后需删除 `__pycache__` 文件夹并重启。
3. **NumPy 版本**：必须固定为 1.26.4，否则 Chroma 报错 `np.float_` 不存在。
4. **数据库迁移**：修改 SQLAlchemy 模型后执行 `alembic revision --autogenerate -m "描述"` 和 `alembic upgrade head`。
5. **Vue Flow 使用**：父组件中禁用 `useVueFlow()`，改用 `v-model` + 数组直接操作；`nodeTypes` 用 `Record<string, any>` 断言。
6. **连线 Handle**：必须保留 `sourceHandle` 和 `targetHandle`，否则多方向连线会消失。
7. **时间轴排序**：必须用 `parseEventTime` 数值比较，不能直接用字符串排序（否则“1月10日”会排在“1月1日”前）。
8. **嫌疑人姓名**：涉及 `NoteCreate`、`NoteUpdate`、`NoteOut` 三个 Schema 及数据库列，缺一不可；刷新后名字丢失通常因为 `NoteUpdate` 遗漏了 `name` 字段。
9. **流式对话会话安全**：`agent_chat_stream` 内部用独立 `async_session()` 保存助手消息，避免外层会话提前关闭导致写入失败。

---

## 快速启动清单

1. 确保 MySQL 运行，数据库 `detective_db` 已创建
2. `.env` 已配置 `DASHSCOPE_API_KEY`
3. `cd backend && uvicorn app.main:app --reload --port 8001`
4. `cd frontend && npm run dev`
5. 浏览器打开 `http://localhost:5173`