#!/bin/bash
set -e

echo "=== 运行数据库迁移 ==="
alembic upgrade head

echo "=== 启动 FastAPI 服务 ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
