好的，基于当前项目实际进度，我来写一份完整的 README：

```markdown
# 推理助手 (Detective Assistant)

一个面向推理小说/剧情游戏爱好者的辅助工具，允许用户在已读内容范围内进行线索整理和推理辅助，严格避免剧透。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Vue Router + @vue-flow/core + Axios |
| 后端 | FastAPI (异步) + Pydantic V2 + SQLAlchemy 2.0 (异步) + MySQL 8.0 |
| Agent | 待接入（LangChain 预留，模型方案待定） |
| 向量库 | Chroma（待接入） |
| 开发工具 | PyCharm (后端) + VS Code (前端) + Navicat (数据库) |

---

## 目录结构

```
detective-assistant/
├── frontend/                # Vue 3 项目 (VS Code 打开)
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomePage.vue       # 案件管理首页
│   │   │   └── CaseDetail.vue     # 案件详情（便签墙+连线+时间线+侧边栏）
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
│   │   │   └── timeline.py        # 时间线 CRUD + 排序
│   │   └── core/                  # 工具函数（待扩展）
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
- 启动后端后，Alembic 迁移版本号为 `836f23434fd6`
- 如遇表结构问题，可执行 `alembic upgrade head` 或手动建表

---

## 环境准备

### 后端

1. 安装 Python 3.10+（推荐使用 Conda 环境）
2. 进入 `backend/` 目录，安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 复制 `.env.example` 为 `.env`，填写 MySQL 连接信息：
   ```
   DATABASE_URL=mysql+aiomysql://用户名:密码@localhost:3306/detective_db
   CHROMA_PERSIST_DIRECTORY=./chroma_data
   SECRET_KEY=任意随机字符串
   ```
4. 启动后端：
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. Swagger 文档：`http://127.0.0.1:8000/docs`

### 前端

1. 安装 Node.js 18+
2. 进入 `frontend/` 目录，安装依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
4. 访问：`http://localhost:5173`

---

## 已完成功能

### 案件管理
- 新建案件、案件列表展示
- 点击案件卡片进入详情页

### 便签墙（Vue Flow 画布）
- 添加线索/嫌疑人便签，自由拖拽移动
- 便签位置和尺寸自动保存到数据库
- 便签之间可拖拽连线（支持上下两个方向的 Handle）
- 连线自动保存，删除便签时自动清理关联连线
- 右下角 🏠 按钮：一键回到画布中心点

### 右侧工具面板
- 可折叠/展开
- 选中便签后编辑内容、切换预设颜色（8 种）
- 保存/删除便签

### 时间线（标签模式）
- 顶部可展开/折叠的时间线面板
- 手动添加事件（时间描述 + 事件内容）
- 事件以标签形式展示
- 支持上下移动排序
- 支持删除事件

### 后端 API
- 案件 CRUD
- 便签 CRUD（含位置、尺寸、颜色）
- 连线 CRUD
- 时间线 CRUD + 排序移动
- CORS 跨域已配置
- 异步数据库操作

### 数据库表（9 张，已建）
- `cases` — 案件
- `notes` — 便签（线索/嫌疑人）
- `connections` — 连线
- `documents` — 上传文本（待接入）
- `known_infos` — 已知信息（待接入）
- `agent_messages` — Agent 对话记录（待接入）
- `skills` — 技能模板（待接入）
- `case_skill_link` — 案件-技能关联（待接入）
- `timeline_events` — 时间线事件

---

## 待实现功能

1. **Agent 对话**（侧边栏聊天界面 + LangChain 受限推理）
2. **文件上传 / 已知信息**（文本上传、向量化、全文搜索）
3. **技能管理**（预置推理技能 + 用户自定义技能）
4. **连线备注编辑**（双击连线标签编辑）
5. **UI 美化**（整体视觉优化）
6. **时间线增强**（改为可视化时间轴，年-月-日-时-分选择器）

---

## 已知注意事项

1. **端口占用问题**：如 8000 端口被僵尸进程占用，可用 `netstat -ano | findstr :8000` 检查，必要时换端口启动（如 `--port 8001`），前端 `api/index.ts` 中的 `baseURL` 同步修改。
2. **Python 缓存**：修改 Model 后如遇 500 错误，删除 `backend/app/` 下所有 `__pycache__` 文件夹后重启。
3. **数据库迁移**：修改 SQLAlchemy 模型后执行 `alembic revision --autogenerate -m "描述"` 和 `alembic upgrade head`。
4. **Vue Flow 类型问题**：`nodeTypes` 使用 `Record<string, any>` 断言绕过严格类型检查；`nodes`/`edges` 声明为 `any[]`；父组件中禁用 `useVueFlow()`，改用 `v-model` + 数组直接操作。
5. **连线必须保留 Handle 信息**：`sourceHandle` 和 `targetHandle` 必须传入边对象。
6. **删除便签需先删连线**：后端 `delete_note` 已自动清理关联连线。

---

## 快速启动清单

1. 确保 MySQL 运行，数据库 `detective_db` 已创建
2. `cd backend && uvicorn app.main:app --reload --port 8000`
3. `cd frontend && npm run dev`
4. 浏览器打开 `http://localhost:5173`
```

---

这份 README 可以直接粘贴到你的项目中。把它和代码一起推送到 GitHub，新对话拿到链接后就能快速了解项目全貌并继续开发。