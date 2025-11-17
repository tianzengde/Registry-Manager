## Registry Manager

轻量级私有 Docker Registry 管理平台。

### 快速开始（开发模式）

1. 安装依赖：
   ```bash
   uv sync
   ```
2. 启动本地服务：
   ```bash
   uv run uvicorn app.main:app --reload
   ```
3. 或通过 Docker Compose 启动完整环境：
   ```bash
   docker compose up --build
   ```

复制 `env.example` 为 `.env` 并根据需要修改配置。

