# 部署指南 (Deployment Guide)

推理助手项目生产部署运维手册。基于实际部署环境编写（阿里云 ECS + Ubuntu 24.04 + venv + supervisor + nginx + MySQL）。

---

## 1. 架构总览

```
用户浏览器
   ↓ 访问 http://<服务器公网IP>
nginx (80 端口)              ← 反向代理 + 前端静态文件服务
   ├── /api/*         → 转发到 127.0.0.1:8001（后端）
   └── 其他路径        → 返回前端编译产物 frontend/dist/
uvicorn (8001)               ← FastAPI 后端，由 supervisor 守护（崩溃自动重启）
   ├── 读取 backend/.env（API 密钥）
   ├── 连接本机 MySQL (3306)
   └── 读写 Chroma 向量库（本地文件 backend/chroma_data/）
```

| 组件 | 职责 | 端口 | 管理方式 |
|---|---|---|---|
| nginx | 反向代理 + 前端静态文件 | 80 | systemd |
| uvicorn | FastAPI 后端进程 | 8001 | supervisor |
| MySQL | 主数据库（案件/便签/对话等） | 3306 | systemd |
| Chroma | 向量数据库（文档分块 + 记忆） | - | 后端进程内嵌，本地文件持久化 |
| venv | 项目专属 Python 环境 | - | `/opt/detective-assistant/backend/venv` |

---

## 2. 环境信息

| 项 | 值 |
|---|---|
| 服务器 | 阿里云 ECS，Ubuntu 24.04 LTS |
| SSH 登录 | `ssh root@<服务器公网IP>`（密码登录） |
| 代码目录 | `/opt/detective-assistant/` |
| GitHub 远程 | `origin`（配置了 gh-proxy 加速镜像） |
| 后端日志 | `/var/log/detective.err.log`（错误）、`/var/log/detective.out.log`（标准输出） |
| supervisor 配置 | `/etc/supervisor/conf.d/detective.conf` |
| nginx 配置 | `/etc/nginx/sites-available/detective` |
| MySQL 数据库 | `detective_db`（本机 3306） |

### 环境变量（`/opt/detective-assistant/backend/.env`）

| 变量 | 说明 | 必填 |
|---|---|---|
| `DATABASE_URL` | MySQL 连接串，如 `mysql+aiomysql://root:xxx@localhost:3306/detective_db` | ✅ |
| `DEEPSEEK_API_KEY` | 对话模型密钥 | ✅ |
| `SILICONFLOW_API_KEY` | 向量化 + 重排共用 | ✅ |
| `CHROMA_PERSIST_DIRECTORY` | Chroma 持久化目录 | 可选 |
| `SECRET_KEY` | JWT 签名密钥 | 可选 |
| `AUTH_ENABLED` | 是否开启登录鉴权 | 可选 |

> ⚠️ **`.env` 已被 gitignore，严禁提交到 git。** 换服务器/重装时如果 `.env` 丢失，密钥全部需要重新配置。

---

## 3. 日常更新部署（核心流程）

> 适用场景：本地代码改完、push 到 GitHub 之后，把新版本上线。

```bash
# ① 登录
ssh root@<服务器公网IP>

# ② 拉取最新代码（管"代码"）
cd /opt/detective-assistant
git pull origin main

# ③ 安装依赖（管"依赖"，幂等，每次跑一遍无害）
cd backend
source venv/bin/activate
pip install -r requirements.txt

# ④ 数据库迁移（管"数据库"，没改表会跳过）
alembic upgrade head

# ⑤ 重启后端（管"进程"，让新代码生效）
supervisorctl restart detective
supervisorctl status detective        # 确认 RUNNING

# ⑥ 验证
curl -s http://127.0.0.1:8001/        # 后端：应输出 {"message":"Detective Assistant Backend v2"}
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/   # 前端：应输出 200
```

**核心心智：git pull 管代码、pip 管依赖、alembic 管数据库、restart 管进程——四件事各管一摊。**

### 前端有改动时（补充步骤）

nginx 服务的是**编译产物 `frontend/dist/`**，`git pull` 不会自动重建。前端源码改动后需要重建：

**方式 A**（服务器装了 Node.js 时）：
```bash
cd /opt/detective-assistant/frontend
npm install && npm run build
```

**方式 B**（服务器无 Node，在本地构建后上传）：
```bash
# 本地
cd frontend
npm run build
scp -r dist root@<服务器公网IP>:/opt/detective-assistant/frontend/
```

> 判断服务器有没有 Node：`node -v && npm -v`。

---

## 4. 故障排查（三板斧）

按顺序查，90% 的问题能定位：

```bash
# ① 进程还活着吗？
supervisorctl status detective

# ② 后端报错日志（最重要的排错入口）
tail -n 50 /var/log/detective.err.log
tail -n 50 /var/log/detective.out.log

# ③ 连通性
curl -s http://127.0.0.1:8001/        # 后端
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/   # 前端
```

### 常见问题速查

| 现象 | 可能原因 | 处理 |
|---|---|---|
| status 显示 `FATAL` / `EXITED` | 后端启动即崩溃（依赖缺失、.env 问题、DB 连不上） | 看 `detective.err.log` 具体报错 |
| 改了代码重启后没生效 | 忘记 restart / supervisor 没重启 | `supervisorctl restart detective` |
| `git pull` 报 `local changes would be overwritten` | 服务器上有未提交的本地改动 | 删掉 `__pycache__` 再试：`find backend/app -type d -name __pycache__ -exec rm -rf {} +` |
| 前端改了不显示 | dist 没重建 | 见上文"前端有改动时" |
| API 返回 401 | 鉴权过期 / AUTH_ENABLED 变化 | 检查 `.env` 的 `AUTH_ENABLED` 和 `SECRET_KEY` |

---

## 5. 回滚

```bash
cd /opt/detective-assistant
git log --oneline -10                  # 找到要回退到的上一个好版本
git reset --hard <上一个好提交哈希>     # 注意：--hard 会丢弃该目录下所有未提交改动
supervisorctl restart detective
```

> ⚠️ `git reset --hard` 会覆盖本地未提交改动（不含 `.env`，它被 gitignore）。回滚后 `pip install` 一般无需重跑，但若回退版本引入过依赖变化，重跑一遍更稳。

---

## 6. 备份与恢复

```bash
# MySQL 备份
mysqldump -u root -p detective_db > /root/backups/detective_$(date +%Y%m%d).sql

# Chroma 向量库备份（本地目录，直接拷贝）
cp -r /opt/detective-assistant/backend/chroma_data /root/backups/chroma_data_$(date +%Y%m%d)

# .env 备份（最重要，密钥不可再生）
cp /opt/detective-assistant/backend/.env /root/backups/
```

恢复：MySQL 用 `mysql -u root -p detective_db < backup.sql`；Chroma 把备份目录拷回原位即可。

---

## 7. 运维纪律（重要教训）

1. **改源码走 git，别在服务器上直接改文件。** 直接改服务器文件 = "服务器漂移（server drift）"，下次部署会被冲掉、且无法回溯。正确闭环：**改源码 → 提交 git → 构建 → 部署**。
2. **重大改动先 push GitHub 再部署。** 部署的必须是可追溯的版本，出问题能 `git reset` 回滚。
3. **密钥只进 `.env`，绝不进 git。** 换环境时密钥需要手动重新配置。
4. **服务器 git 远程用了 gh-proxy 加速**，换新服务器时同样配置可加速拉取。
5. **建议配置 SSH 密钥免密登录**（替代每次输密码），并在 `.ssh/config` 里固化 Host 配置。

---

## 8. 运维速查表

| 操作 | 命令 |
|---|---|
| 登录 | `ssh root@<服务器公网IP>` |
| 看后端进程 | `supervisorctl status detective` |
| 重启后端 | `supervisorctl restart detective` |
| 看后端错误日志 | `tail -f /var/log/detective.err.log` |
| 拉最新代码 | `cd /opt/detective-assistant && git pull origin main` |
| 装依赖 | `cd backend && source venv/bin/activate && pip install -r requirements.txt` |
| 数据库迁移 | `cd backend && source venv/bin/activate && alembic upgrade head` |
| 后端健康检查 | `curl -s http://127.0.0.1:8001/` |
| 前端健康检查 | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/` |
| 看 nginx 配置 | `nginx -t` |
| 看 MySQL 状态 | `systemctl status mysql` |
| 前端重建 | `cd frontend && npm run build`（或本地构建后 scp dist） |
