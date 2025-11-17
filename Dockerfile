# 构建阶段 - Node.js 前端
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件和配置文件
COPY package.json ./
COPY vite.config.js ./
COPY index.html ./
RUN npm install

# 复制前端源代码
COPY src/ ./src/

# 构建前端
RUN npm run build

# 最终阶段 - Python 后端
FROM python:3.12-slim AS base

WORKDIR /app

ENV UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制后端依赖文件
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

# 复制后端源代码
COPY app/ ./app/

# 从前端构建阶段复制构建好的前端文件
COPY --from=frontend-builder /app/frontend/dist ./frontend

# 复制其他必要的文件
COPY data/ ./data/

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]