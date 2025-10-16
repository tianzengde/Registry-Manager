# Docker Registry Manager

一个功能完整的 Docker Registry 前端管理系统，支持细粒度的权限控制和现代化的 Web 界面。

## ✨ 主要特性

- 🔐 **用户认证系统** - JWT 令牌认证，支持管理员和普通用户角色
- 🎯 **细粒度权限控制** - 控制用户对仓库的 Pull/Push/Delete 权限
- 🌐 **公开/私有仓库** - 灵活设置仓库的访问级别
- 📦 **镜像管理** - 浏览镜像标签、查看详细信息（架构、大小、层信息等）
- 📋 **一键复制拉取命令** - 根据访问地址自动生成拉取命令
- 👥 **用户管理** - 管理员可创建、编辑、禁用用户
- 🎨 **现代化 UI** - 清爽简洁的界面设计，响应式布局
- 🐳 **Docker 集成** - 无缝集成 Docker Registry 3.0

## 🏗️ 技术栈

### 后端
- **FastAPI** - 高性能 Web 框架
- **Tortoise ORM** - 异步 ORM
- **SQLite** - 轻量级数据库
- **JWT** - 安全的身份认证
- **uv** - 快速的 Python 包管理器

### 前端
- **原生 HTML/CSS/JavaScript** - 无构建工具，简单直接
- **现代 CSS** - 使用 CSS Grid/Flexbox
- **Fetch API** - 异步数据请求

## 📋 系统要求

- Docker & Docker Compose
- Python 3.12+ (本地开发)
- uv (本地开发)

## 🚀 快速开始

### 使用 Docker Compose (推荐)

1. **克隆项目**
```bash
git clone <repository-url>
cd registry-fe
```

2. **启动所有服务**
```bash
docker-compose up -d
```

3. **访问系统**
- 管理界面: http://localhost:30080
- Registry API: http://localhost:30080/v2/

4. **默认登录凭据**
- 用户名: `admin`
- 密码: `admin123`

### 本地开发

1. **安装 uv**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **安装依赖**
```bash
uv sync
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件设置你的配置
```

4. **启动开发服务器**
```bash
uv run python main.py
```

或使用 uvicorn 的热重载模式：
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. **访问应用**
- http://localhost:8000

## 📖 使用指南

### 管理员功能

1. **用户管理**
   - 创建新用户
   - 设置用户状态（激活/禁用）
   - 删除用户（除 admin 外）

2. **仓库管理**
   - 创建仓库记录
   - 设置仓库为公开或私有
   - 查看所有仓库

3. **权限管理**
   - 为用户分配仓库权限
   - 设置 Pull/Push/Delete 权限
   - 撤销用户权限

4. **镜像管理**
   - 查看所有镜像详情
   - 删除镜像（功能预留）

### 普通用户功能

1. **查看权限内的仓库**
   - 查看有权限的仓库列表
   - 访问公开仓库

2. **浏览镜像**
   - 查看镜像标签
   - 查看镜像详细信息
   - 复制拉取命令

3. **个人信息**
   - 查看自己的权限信息

### 权限说明

- **公开仓库**: 所有登录用户可以 Pull
- **私有仓库**: 需要显式授权
- **Pull 权限**: 可以拉取镜像
- **Push 权限**: 可以推送镜像
- **Delete 权限**: 可以删除镜像（仅管理员）

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | JWT 密钥 | 需要修改 |
| `DEBUG` | 调试模式 | false |
| `DATABASE_URL` | 数据库连接 | sqlite://db.sqlite3 |
| `REGISTRY_URL` | Registry 地址 | http://docker-registry:5000 |
| `REGISTRY_USERNAME` | Registry 用户名 | admin |
| `REGISTRY_PASSWORD` | Registry 密码 | 123456 |
| `HOST` | 监听地址 | 0.0.0.0 |
| `PORT` | 监听端口 | 8000 |

### Docker Registry 配置

编辑 `docker-compose.yaml` 中的环境变量来修改 Registry 的认证信息：

```yaml
environment:
  - HTPASSWD_USERNAME=admin
  - HTPASSWD_PASSWORD=123456
```

## 📂 项目结构

```
registry-fe/
├── app/
│   ├── api/                 # API 路由
│   │   ├── auth.py         # 认证接口
│   │   ├── users.py        # 用户管理
│   │   ├── repositories.py # 仓库管理
│   │   ├── images.py       # 镜像管理
│   │   ├── permissions.py  # 权限管理
│   │   └── pages.py        # 页面路由
│   ├── core/               # 核心模块
│   │   ├── config.py       # 配置
│   │   ├── database.py     # 数据库
│   │   └── security.py     # 安全认证
│   ├── models/             # 数据模型
│   │   ├── user.py         # 用户模型
│   │   ├── repository.py   # 仓库模型
│   │   └── permission.py   # 权限模型
│   ├── schemas/            # Pydantic 模型
│   ├── services/           # 业务逻辑
│   │   ├── auth.py         # 认证服务
│   │   ├── registry.py     # Registry API 服务
│   │   └── permission.py   # 权限服务
│   ├── static/             # 静态文件
│   │   ├── css/           # 样式文件
│   │   └── js/            # JavaScript
│   ├── templates/          # HTML 模板
│   └── utils/              # 工具函数
├── main.py                 # 应用入口
├── pyproject.toml          # 项目配置
├── Dockerfile              # Docker 镜像
├── docker-compose.yaml     # Docker Compose 配置
├── nginx.conf              # Nginx 配置
└── README.md              # 项目文档
```

## 🔒 安全建议

1. **修改默认密码**
   - 修改管理员密码
   - 修改 Registry 认证密码
   - 修改 SECRET_KEY

2. **使用 HTTPS**
   - 配置 SSL 证书
   - 取消注释 nginx.conf 中的 HTTPS 配置

3. **访问控制**
   - 使用防火墙限制访问
   - 配置反向代理

4. **定期备份**
   - 备份 SQLite 数据库
   - 备份 Registry 数据目录

## 🛠️ API 文档

启动服务后访问自动生成的 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐛 故障排除

### Registry 连接失败

检查 Registry 服务是否正常运行：
```bash
docker-compose ps
docker-compose logs registry
```

### 数据库错误

删除数据库重新初始化：
```bash
rm db.sqlite3
docker-compose restart registry-frontend
```

### 权限问题

确保 Docker 有权限创建和写入挂载的目录：
```bash
chmod -R 755 data auth
```

## 📝 开发说明

### 添加新的 API 端点

1. 在 `app/api/` 中创建新的路由文件
2. 在 `app/api/__init__.py` 中注册路由
3. 必要时创建对应的 Schema 和 Service

### 添加新的页面

1. 在 `app/templates/` 中创建 HTML 模板
2. 在 `app/api/pages.py` 中添加路由
3. 添加必要的 CSS 和 JavaScript

### 数据库迁移

项目使用 Tortoise ORM，支持数据库迁移：

```bash
# 初始化迁移
uv run aerich init -t app.core.database.TORTOISE_ORM

# 生成迁移文件
uv run aerich migrate

# 应用迁移
uv run aerich upgrade
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Tortoise ORM](https://tortoise.github.io/)
- [Docker Registry](https://docs.docker.com/registry/)
- [uv](https://github.com/astral-sh/uv)

## 📮 联系方式

如有问题或建议，请提交 Issue 或联系开发者。

---

Made with ❤️ for Docker Registry Management

