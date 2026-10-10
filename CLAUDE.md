# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

推理助手 (Detective Assistant) — 面向推理小说/剧情游戏爱好者的辅助工具。用户可在已读内容范围内整理线索、连线推理、与 AI Agent 对话，严格避免剧透。前端使用 Vue 3 + TypeScript + Vite + Vue Router，以自写 DOM + SVG 调查墙、CSS 3D、Canvas 2D 与原生交互/动画 API 实现档案和纸张界面。后端使用 FastAPI + SQLAlchemy 2.0 异步 + Chroma，DeepSeek API（对话）、SiliconFlow BAAI/bge-m3（向量化）、SiliconFlow BAAI/bge-reranker-v2-m3（重排序，经 API 调用）。

## 常用命令

### 后端（`backend/`）

**当前 Windows 工作区的 Python 环境**：`D:\personal project\.local\detective-venv`。基础 CPython 3.10.20 位于同一工作区的 `.local\python-runtimes\cpython-3.10.20-windows-x86_64-none`，不依赖 F 盘的 Conda `detective` 环境。其他机器使用自己的项目虚拟环境；本机完整说明见仓库外的 `../LOCAL-DEVELOPMENT.md`。

```powershell
Set-Location 'D:\personal project\detective\backend'
$detectivePython = 'D:\personal project\.local\detective-venv\Scripts\python.exe'

# 启动开发服务器
& $detectivePython -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# 数据库迁移（先配置并确认 .env 指向开发/测试数据库）
& $detectivePython -m alembic revision --autogenerate -m "描述"
& $detectivePython -m alembic upgrade head

# Swagger 文档
# 访问 http://127.0.0.1:8001/docs
```

### 前端（`frontend/`）

Node.js 要求为 `^20.19.0 || >=22.12.0`，当前本机使用 24.15.0。开发服务器通过 Vite 将 `/api` 代理到 `127.0.0.1:8001`。

```bash
npm ci             # 按 package-lock.json 安装
npm run dev        # 开发服务器 → http://localhost:5173
npm run build      # 生产构建（含 vue-tsc 类型检查）
```

### 环境变量（`backend/.env`）

必须配置的变量：`DATABASE_URL`（MySQL）、`DEEPSEEK_API_KEY`（对话模型）、`SILICONFLOW_API_KEY`（Embedding + 重排共用）。可选：`CHROMA_PERSIST_DIRECTORY`。

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
  SpatialHome.vue       ← 当前首页：CSS 3D 档案袋、连续翻阅、案件索引
  CaseDetail.vue        ← 案件详情（主容器，组装所有子组件）

components/
  canvas/
    NoteCanvas.vue      ← 自写 DOM + SVG 调查墙、二维视口与指针交互
    ThreadEdge.vue      ← SVG 线绳、备注与双击命中区域
    CardEditorOverlay.vue ← 独立纸张编辑面板
  NoteNode.vue          ← DOM 卡片、图钉、纸张材质与搜索高亮
  sidebar/
    SidePanel.vue       ← 右侧可折叠面板容器
    ChatTab.vue         ← Agent 对话界面（流式 SSE）
    DocsTab.vue         ← 文档上传
    InfoTab.vue         ← 已知信息管理
  timeline/
    TimelineBar.vue     ← 顶部时间线开关条
    TimelinePanel.vue   ← 时间轴展开内容

composables/            ← 按功能拆分的组合式 API（Vue 3 逻辑复用模式）
  useNotes.ts           ← 卡片/连线数据与 CRUD；不负责视口渲染
  useChat.ts            ← 流式对话（fetch + ReadableStream 解析 SSE）
  useTimeline.ts        ← 时间线事件管理
  useDocuments.ts       ← 文档上传
  useKnownInfo.ts       ← 已知信息

utils/
  boardGeometry.ts      ← 卡片尺寸、确定性的图钉位置与连线锚点
  linenTexture.ts       ← Canvas 2D 生成并缓存亚麻布纹理
styles/spatial-home.css ← 首页档案袋的 CSS 3D、材质与响应式布局
theme.css               ← 全局字体、颜色与减少动态效果设置
```

**关键设计决策：**

- **CaseDetail 是数据枢纽**：所有 composable 在 `CaseDetail.vue` 中初始化并向下通过 props 传递给子组件。子组件通过 `v-model` 和事件向上通信。
- **当前状态管理**：路由页面使用 Vue 的 ref / computed 和 composables。`main.ts` 只注册 Vue Router；Pinia 依赖与旧 store 已移除。
- **调查墙的渲染边界**：`NoteCanvas.vue` 使用绝对定位的 DOM 卡片和 SVG `ThreadEdge`，没有挂载 Vue Flow。视口由 `{ x, y, zoom }` 驱动 CSS `translate3d(x, y, 0) scale(zoom)`；卡片与关联线共用二维坐标，不存在 WebGL 三维相机。
- **图钉和线绳**：`nodePinAnchor()` 根据卡片位置、尺寸与 `pinPercent()` 求锚点。SVG 曲线按距离计算下垂，并叠加阴影和高光。点击源图钉、再点击目标卡片建立连接，双击红线编辑备注。连接按 source / target 节点 ID 去重，禁止自连接；后端请求仍使用 from_note_id / to_note_id，Handle 字段已移除。
- **输入与持久化**：Pointer Events 处理卡片拖动和背景平移，WheelEvent 处理围绕鼠标位置的缩放。拖动按 zoom 将屏幕增量换算到世界坐标，结束时通知 `useNotes.onNodesChange()` 保存位置。放置材料也须调用 `screenToWorld()`；修改节点尺寸或图钉位置应同步维护 `boardGeometry.ts`。
- **旧实现清理状态**：Vue Flow 依赖、视口引用、居中兼容回调、默认连线样式、空的 edge-change 回调和 Handle 字段均已移除。未接入路由的旧首页与旧编辑 Tab 已删除。居中按钮与首次加载适配全部卡片仍由 `NoteCanvas.vue` 的 goToCenter / fitView 和节点数量 watcher 处理。
- **流式对话在前端直接 fetch**：`useChat.ts` 不使用 axios，而是用原生 `fetch` + `ReadableStream` 逐块解析 SSE，每收到一个 chunk 追加到 `assistantMsg.content`。

### 前端视觉效果与实现位置

| 效果 | 实现技术 | 维护位置（相对 frontend/src） |
|------|----------|-----------------------------|
| 首页档案袋的透视排列、侧向倾斜、封面翻动与内页抽出 | CSS perspective / rotateX / rotateY / rotateZ、分层 DOM、阴影与噪声 | `views/SpatialHome.vue`、`styles/spatial-home.css` |
| 连续拖动翻阅与松手吸附 | Pointer Events、指针捕获、分数位置 position 驱动 CSS 变量 | `views/SpatialHome.vue` |
| 进入案件和新建/管理弹窗的纸张动效 | 原生 Element.animate（Web Animations API）与 dialog.showModal | `views/SpatialHome.vue` |
| 调查墙的拖动、缩放与平滑居中 | 自写二维视口、CSS transform / transition、DOMMatrixReadOnly、requestAnimationFrame | `components/canvas/NoteCanvas.vue` |
| 红线的下垂、阴影、高光和宽命中区域 | SVG 三次贝塞尔曲线及多层 path；下垂为几何模拟，无物理引擎 | `components/canvas/ThreadEdge.vue` |
| 亚麻布底纹的纤维、布结、染色与针孔 | CanvasRenderingContext2D 绘制，导出 WebP/PNG 图片并缓存 | `utils/linenTexture.ts` |
| 撕边纸、备忘、票据、剪报、人物档案及图钉材质 | CSS clip-path、渐变、阴影和滤镜 | `components/NoteNode.vue`、`components/canvas/CardEditorOverlay.vue` |
| 卡片从原位置放大为编辑面板 | 读取 DOM 边界，计算起点偏移/缩放，Vue Transition + CSS 过渡 | `views/CaseDetail.vue` |
| 档案侧栏分页、时间线与浮动事件卡片 | Vue Transition、CSS 过渡、Vue Teleport 与 SVG 线绳 | `components/sidebar/SidePanel.vue`、`components/timeline/TimelinePanel.vue` |

当前立体表现为 CSS 3D 与二维材质模拟，未使用 Three.js / WebGL / 3D 引擎。Canvas 只生成背景纹理，不绘制调查墙的交互卡片。修改动效时应保留 `prefers-reduced-motion` 分支；首页的键盘翻阅/激活应保留跳过动画的处理，减少不必要的位移。

### RAG 检索链路

1. 文档上传 → `RecursiveCharacterTextSplitter` 分块（`chunk_size=250, chunk_overlap=50`，子块做索引）→ SiliconFlow `BAAI/bge-m3` 向量化 → 存入 Chroma（同文件名替换语义，先删旧块再写入）
2. 检索 → Chroma 向量粗召回 `k*2` 条候选（扩大候选空间保证召回率）→ Cross-Encoder 重排序取 Top-k → 按命中块的前后邻居（`WINDOW_RADIUS=1`）拼上下文窗口，旧数据大块自动降级为单块（`CHILD_SIZE_THRESHOLD=500`）
3. 重排序失败自动降级到向量检索结果

### 技能系统

技能以文件夹形式存放在 `backend/skills/`，每个技能一个 `SKILL.md`（YAML frontmatter + Markdown 正文）。`skill_loader.py` 扫描目录提取元数据注入 System Prompt，模型通过 `load_skill` 工具按需加载正文，避免 Prompt 膨胀。技能元数据有缓存，服务启动后只在首次请求时扫描一次。

## 稳定性原则

**对 GitHub 或全局有影响的操作必须三思而后行。** 包括但不限于：
- 修改 `.gitignore`、提交/推送代码
- 安装全局依赖、修改环境变量
- 修改数据库迁移、删除文件等不可逆操作
- 安装或卸载全局 skill、修改用户级配置

执行前先思考：这个操作会影响什么？是否可逆？会不会影响项目稳定性？不确定时先问用户确认。

## 注意事项

- **后端依赖**：异步 SQLAlchemy 使用 `sqlalchemy[asyncio]` 安装，确保包含 greenlet；文件上传显式依赖 python-multipart。两者均在 requirements.txt 声明，避免只在本机补装后遗漏部署环境。
- **NumPy 版本**：固定为 1.26.4。requirements.txt 锁定的 Chroma 0.5.0 不兼容 NumPy 2.x（`np.float_` 被移除）；当前本机独立虚拟环境使用 Chroma 1.5.9 + NumPy 1.26.4，完整依赖快照位于仓库外的 `../.local/requirements-detective.lock.txt`。
- **模型 API**：对话使用 `deepseek-v4-flash`，通过 langchain-openai 兼容的 `ChatOpenAI` 客户端调用（base_url 指向 `https://api.deepseek.com`）。代码中变量名 `BAILIAN_BASE_URL` 是历史遗留，实际已迁移到 DeepSeek。
- **Embedding 模型**：使用 SiliconFlow 平台的 `BAAI/bge-m3`，支持多语言。
- **重排序模型**：经 SiliconFlow Rerank API 调用 `BAAI/bge-reranker-v2-m3`，与 Embedding 共用 `SILICONFLOW_API_KEY`，无需本地加载模型。
- **调查墙数据一致性**：删除卡片时需同步清理前端 edges 数组中的关联连线（后端 CASCADE 删除）；调整纸张材质或旋转时，保持图钉锚点与 SVG 连线端点一致。
- **时间轴排序**：必须用 `parseEventTime` 数值比较，不能直接用字符串排序。事件时间支持年-月-日-时-分。
- **文档上传**：仅支持 UTF-8 编码的 `.txt` 文件。
- **端口**：后端默认 8001，前端默认 5173。后端换端口时修改 `frontend/vite.config.ts` 的代理 target，前端请求地址保持 `/api`；生产环境另同步反向代理配置。
