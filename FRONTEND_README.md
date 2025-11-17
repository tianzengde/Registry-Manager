# Registry Manager Frontend - Vue 3 + Element Plus

## 项目结构

```
frontend/
├── src/
│   ├── components/     # 公共组件
│   ├── views/         # 页面组件
│   │   ├── Login.vue      # 登录页面
│   │   ├── Main.vue      # 主布局
│   │   ├── Repositories.vue # 仓库管理
│   │   ├── Dashboard.vue   # 仪表盘
│   │   └── Settings.vue    # 设置页面
│   ├── router/        # 路由配置
│   ├── stores/        # 状态管理
│   ├── utils/         # 工具函数
│   ├── App.vue        # 根组件
│   └── main.js        # 入口文件
├── package.json       # 项目配置
├── vite.config.js     # Vite配置
└── index.html         # HTML模板
```

## 安装依赖

由于系统中没有npm，需要先安装Node.js和npm：

```bash
# 使用系统包管理器安装Node.js和npm
sudo apt update
sudo apt install -y nodejs npm

# 或者使用Node版本管理器(nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
# 重新打开终端后
nvm install 18
nvm use 18

# 安装项目依赖
npm install
```

## 开发模式运行

```bash
# 启动开发服务器
npm run dev
```

开发服务器将在 http://localhost:3000 运行，并代理API请求到后端服务 (http://localhost:6000)。

## 构建生产版本

```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 功能特性

### ✅ 已实现的功能
- [x] Vue 3 + Composition API
- [x] Element Plus UI组件库
- [x] Vue Router路由管理
- [x] Pinia状态管理
- [x] Axios API请求封装
- [x] 响应式设计（支持移动端）
- [x] 登录认证
- [x] 仓库管理界面
- [x] 仪表盘界面
- [x] 设置页面

### 🔄 迁移进度
- [x] 项目结构和配置文件
- [x] 核心组件重构
- [x] 路由和状态管理
- [ ] 依赖安装和测试
- [ ] 完整功能测试

## API接口

前端通过代理访问后端API：
- 开发环境: http://localhost:3000/api -> http://localhost:6000/api
- 生产环境: 需要配置反向代理

主要API端点：
- `POST /auth/login` - 用户登录
- `GET /auth/me` - 获取当前用户信息
- `POST /auth/change-password` - 修改密码
- `GET /repositories` - 获取仓库列表
- `GET /repositories/{name}/tags` - 获取仓库标签
- `GET /stats/overview` - 获取系统概览
- `GET /stats/top-pulled` - 获取热门拉取排行

## 浏览器支持

- Chrome ≥ 80
- Firefox ≥ 78
- Safari ≥ 13
- Edge ≥ 80

## 注意事项

1. 确保后端服务正在运行（端口6000）
2. 开发时需要配置API代理
3. 生产部署时需要构建静态文件并配置Web服务器