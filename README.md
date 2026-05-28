# 推理助手 (Detective Assistant)

一个面向推理小说/剧情游戏爱好者的辅助工具，允许用户在已读内容范围内进行线索整理和推理辅助，严格避免剧透。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Vue Router + @vue-flow/core + Axios |
| 后端 | FastAPI (异步) + Pydantic V2 + SQLAlchemy 2.0 (异步) + MySQL 8.0 |
| AI 模型 | 阿里云百炼 Qwen3-Max（兼容 OpenAI API） |
| Agent 框架 | LangChain + LangChain-OpenAI |
| 向量数据库 | Chroma（Embedding: text-embedding-v3） |
| 开发工具 | PyCharm (后端) + VS Code (前端) + Navicat (数据库) |

---

## 目录结构

```
detective-assistant/
├── frontend/                # Vue 3 项目 (VS Code 打开)
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomePage.vue       # 案件管理首页
│   │   │   └── CaseDetail.vue     # 案件详情（便签墙+连线+时间轴+侧边栏）
│   │   ├── components/
│   │   │   └── NoteNode.vue       # 自定义便利贴节点
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
│   │   ├── config.py              # 环境变量配置
│   │   ├── database.py            # 异步数据库连接
│   │   ├── models/                # SQLAlchemy 模型（9 张表）
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── api/                   # 路由模块
│   │   │   ├── cases.py           # 案件 CRUD
│   │   │   ├── notes.py           # 便签 CRUD
│   │   │   ├── connections.py     # 连线 CRUD
│   │   │   ├── timeline.py        # 时间线 CRUD + 排序
│   │   │   └── agent.py           # Agent 对话（普通+流式）
│   │   └── core/                  # 核心逻辑
│   │       ├── agent.py           # Agent 引擎（Qwen3-Max + RAG）
│   │       └── vector_store.py    # Chroma 向量库操作
│   ├── alembic/                   # 数据库迁移
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

| 表名 | 说明 | 状态 |
|------|------|------|
| `cases` | 案件 | ✅ |
| `notes` | 便签（线索/嫌疑人） | ✅ |
| `connections` | 连线 | ✅ |
| `documents` | 上传文本 | ✅（表已建，上传功能待接入） |
| `known_infos` | 已知信息 | ✅（表已建，录入功能待接入） |
| `agent_messages` | Agent 对话记录 | ✅ |
| `skills` | 技能模板 | ✅（待接入） |
| `case_skill_link` | 案件-技能关联 | ✅（待接入） |
| `timeline_events` | 时间线事件 | ✅ |

---

## 环境准备

### 后端

1. 安装 Python 3.10+（推荐 Conda）
2. 进入 `backend/` 目录：
   ```bash
   pip install -r requirements.txt
   ```
3. 复制 `.env.example` 为 `.env`，填写配置：
   ```
   DATABASE_URL=mysql+aiomysql://用户名:密码@localhost:3306/detective_db
   DASHSCOPE_API_KEY=你的阿里云百炼API_KEY
   CHROMA_PERSIST_DIRECTORY=./chroma_data
   SECRET_KEY=任意随机字符串
   ```
4. **注意**：NumPy 需降级到 1.26.4（兼容 Chroma）：
   ```bash
   pip install numpy==1.26.4
   ```
5. 启动：
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Swagger 文档：`http://127.0.0.1:8000/docs`

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
- 新建案件、案件列表、进入详情页
- 首页展示案件卡片

### 便签墙（Vue Flow 画布）
- 添加线索/嫌疑人便签，自由拖拽移动
- 便签位置和尺寸自动保存
- 便签间拖拽连线（上下两个 Handle）
- 连线自动保存，删除便签时清理关联连线
- 右下角 🏠 回到画布中心点

### 右侧工具面板
- 可折叠/展开
- 编辑便签内容、切换预设颜色（8 种）
- 保存/删除便签

### 时间线（可视化时间轴）
- 年-月-日-时-分选择器添加事件
- 横轴时间轴，圆点标记事件
- 按时间自动分布（智能间距，防重叠）
- 悬停显示详情框，移开消失
- 点击圆点锁定详情框，支持多个同时锁定
- × 关闭详情框，删除事件按钮
- 左右两侧智能对齐
- 日期输入自动修正（如 41 日→31 日）

### Agent 对话（后端已完整实现）
- **流式输出**：SSE 格式，打字机效果
- **RAG 检索**：Chroma 向量库 + text-embedding-v3
- **受限推理**：仅基于当前案件的便签、时间线、已知信息、已上传文本
- **对话历史**：自动保存到数据库，每次对话携带历史
- 调用阿里云百炼 Qwen3-Max 模型

### 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/cases/` | 案件列表/创建 |
| GET/POST | `/cases/{id}/notes` | 便签列表/创建 |
| PUT/DELETE | `/cases/{id}/notes/{note_id}` | 更新/删除便签 |
| GET/POST | `/cases/{id}/connections` | 连线列表/创建 |
| PUT/DELETE | `/cases/{id}/connections/{conn_id}` | 更新/删除连线 |
| GET/POST | `/cases/{id}/timeline/` | 时间线列表/创建 |
| PUT | `/cases/{id}/timeline/{event_id}/move` | 移动排序 |
| PUT/DELETE | `/cases/{id}/timeline/{event_id}` | 更新/删除事件 |
| POST | `/cases/{id}/agent/chat` | Agent 普通对话 |
| POST | `/cases/{id}/agent/chat/stream` | Agent 流式对话 |
| GET | `/cases/{id}/agent/history` | 对话历史 |
| DELETE | `/cases/{id}/agent/history` | 清空历史 |

---

## 待实现功能

1. **前端聊天 UI** — Agent 对话界面集成到侧边栏
2. **文件上传** — 上传已读文本，自动分块 + 向量化
3. **已知信息录入** — 手动输入汇总信息
4. **连线备注编辑** — 双击连线编辑 label
5. **技能管理** — 预置推理技能 + 用户自定义
6. **UI 美化** — 整体视觉优化

---

## 已知注意事项

1. **端口占用**：如 8000 被僵尸进程占用，用 `netstat -ano | findstr :8000` 检查，换端口启动（`--port 8001`），前端同步修改 `api/index.ts` 的 `baseURL`
2. **Python 缓存**：修改 Model 后删除 `__pycache__` 文件夹后重启
3. **NumPy 版本**：需固定为 1.26.4，否则 Chroma 报错
4. **数据库迁移**：修改 SQLAlchemy 模型后执行 `alembic revision --autogenerate -m "描述"` 和 `alembic upgrade head`
5. **Vue Flow**：父组件禁用 `useVueFlow()`，用 `v-model` + 数组操作；`nodeTypes` 用 `Record<string, any>` 断言
6. **连线 Handle**：必须保留 `sourceHandle` 和 `targetHandle`
7. **时间轴排序**：所有排序必须用 `parseEventTime` 数值比较，不能用字符串排序

---

## 快速启动清单

1. 确保 MySQL 运行，数据库 `detective_db` 已创建
2. `.env` 已配置 `DASHSCOPE_API_KEY`
3. `cd backend && uvicorn app.main:app --reload --port 8000`
4. `cd frontend && npm run dev`
5. 浏览器打开 `http://localhost:5173`