# Registry Manager

一个轻量的 Docker / OCI 镜像仓库管理控制台，提供仓库浏览、标签管理、多架构镜像查看和访问权限管理。适合为自建 Registry 提供统一的 Web 管理界面与 Docker 客户端入口。

## 功能

- **仓库浏览**：搜索仓库、按命名空间展示，筛选公开与私有仓库。
- **镜像详情**：查看标签、Digest、构建时间、压缩层大小和 Manifest 原文。
- **多架构支持**：识别 Docker Manifest List 与 OCI Image Index，展示镜像支持的平台。
- **推拉镜像**：提供 Docker 登录、拉取和推送命令，通过 `/v2/` 代理访问 Registry。
- **访问控制**：支持管理员与成员账号、仓库可见性设置、会话登录和密码修改。
- **操作记录**：查看操作审计及经过代理的镜像推拉统计。
- **镜像删除**：支持按 Manifest Digest 删除，默认关闭。
- **界面适配**：紧凑的仓库表格、镜像详情抽屉和移动端布局。

## 技术栈

使用 Nuxt 4、Vue 3 和 TypeScript 构建，SQLite 保存账号、权限和操作记录。前端、管理 API 与 Registry 代理运行在同一个 Node.js 服务中，镜像内容由 Docker Registry 存储。

## 容器镜像

镜像发布于 GitHub Container Registry，支持 `linux/amd64` 和 `linux/arm64`。

```sh
docker pull ghcr.io/tianzengde/registry-manager:latest
```

## 部署

无需克隆源码或准备 `.env` 文件。只需下载一个 Compose 文件，修改管理员密码后启动：

```sh
curl -fsSLO https://raw.githubusercontent.com/tianzengde/Registry-Manager/main/deploy/docker-compose.yaml
# 修改 docker-compose.yaml 中的 NUXT_ADMIN_INITIAL_PASSWORD
docker compose up -d
```

默认访问端口为 `30080`，登录用户名为 `admin`。数据库使用 Docker 命名卷，镜像存储在部署目录的 `data/registry` 中；更新时保留这些数据。
