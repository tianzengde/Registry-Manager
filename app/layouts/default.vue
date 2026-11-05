<script setup lang="ts">
const workspace = createWorkspace();
provide("workspace", workspace);
const {
  route,
  runtime,
  user,
  logout,
  section,
  nav,
  title,
  repos,
  repoError,
  status,
  refresh,
  health,
  settings,
  overview,
  logs,
  search,
  filter,
  sort,
  selected,
  detail,
  detailLoading,
  detailError,
  activeTab,
  drawerSearch,
  showConnect,
  showDelete,
  deleting,
  notice,
  copied,
  mobile,
  activitySearch,
  logPage,
  pageError,
  pageBusy,
  password,
  passwordBusy,
  totalTags,
  namespaces,
  visible,
  host,
  tags,
  pullCommand,
  color,
  size,
  date,
  message,
  copy,
  reload,
  openRepo,
  loadDetail,
  loadPage,
  visibilityChange,
  remove,
  changePassword,
  overlayOpen,
} = workspace;
</script>
<template>
  <div class="workspace">
    <header class="app-header" :inert="overlayOpen">
      <NuxtLink to="/" class="brand"
        ><AppIcon name="Boxes" :size="21" /><span
          >Registry Manager</span
        ></NuxtLink
      >
      <nav aria-label="主导航">
        <NuxtLink
          v-for="item in nav"
          :key="item.path"
          :to="item.path"
          :class="{ active: section === item.key }"
          >{{ item.label }}</NuxtLink
        >
      </nav>
      <div class="header-account">
        <span class="connection-status"
          ><span class="live-dot" :class="{ offline: !health?.connected }" />{{
            health?.connected ? "已连接" : "未连接"
          }}</span
        ><span class="account-name">{{ user?.username }}</span
        ><button
          class="icon-btn"
          aria-label="退出登录"
          title="退出登录"
          @click="logout"
        >
          <AppIcon name="LogOut" :size="16" />
        </button>
      </div>
    </header>
    <main class="content" :inert="overlayOpen">
      <div v-if="runtime.public.preview" class="preview-banner">
        模拟数据环境
      </div>
      <div class="page-heading">
        <div class="page-title">
          <h1>{{ title }}</h1>
          <span v-if="section === 'repositories' && !repoError" class="count">{{
            repos.length
          }}</span>
        </div>
        <div class="heading-actions">
          <button
            class="btn"
            :disabled="status === 'pending' || pageBusy"
            @click="section === 'repositories' ? reload() : loadPage()"
          >
            <AppIcon
              name="RefreshCw"
              :size="14"
              :class="{ spin: status === 'pending' }"
            />刷新</button
          ><button class="btn" @click="showConnect = true">
            <AppIcon name="Terminal" :size="15" />Docker 命令
          </button>
        </div>
      </div>
      <div class="endpoint-line">
        <span class="endpoint-label">Registry</span
        ><code>{{ settings?.registry_url || host }}</code
        ><span class="endpoint-state" :class="{ failed: !health?.connected }">{{
          health?.connected ? "连接正常" : "连接失败"
        }}</span>
      </div>
      <div v-if="pageError" class="error-banner" role="alert">
        <AppIcon name="AlertCircle" :size="16" />{{ pageError
        }}<button class="text-btn" @click="loadPage">重试</button>
      </div>
      <slot />
    </main>
    <div v-if="selected" class="overlay" @click.self="selected = null">
      <section
        class="drawer"
        :inert="showDelete"
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
      >
        <header class="drawer-header">
          <span class="repo-icon" :class="color(selected.name)"
            ><AppIcon name="Box" :size="24" /></span
          ><button
            class="icon-btn"
            aria-label="关闭镜像详情"
            @click="selected = null"
          >
            <AppIcon name="X" />
          </button>
        </header>
        <div class="drawer-heading">
          <span class="drawer-caption">仓库详情</span>
          <h2 id="drawer-title">{{ selected.name }}</h2>
          <span class="badge" :class="{ public: selected.is_public }">{{
            selected.is_public ? "公开仓库" : "私有仓库"
          }}</span
          ><span class="muted"> · {{ selected.tags_count }} 个标签</span>
        </div>
        <div class="drawer-tabs">
          <button
            :class="{ active: activeTab === 'tags' }"
            @click="activeTab = 'tags'"
          >
            镜像标签</button
          ><button
            :class="{ active: activeTab === 'manifest' }"
            @click="activeTab = 'manifest'"
          >
            Manifest</button
          ><button
            v-if="user?.is_admin"
            :class="{ active: activeTab === 'settings' }"
            @click="activeTab = 'settings'"
          >
            仓库设置
          </button>
        </div>
        <div class="drawer-body">
          <template v-if="activeTab === 'settings'"
            ><h3>访问权限</h3>
            <p class="muted">公开仓库允许匿名读取；写入始终需要管理员认证。</p>
            <button
              class="btn"
              :disabled="
                selected.name === 'public' ||
                selected.name.startsWith('public/')
              "
              @click="visibilityChange"
            >
              {{ selected.is_public ? "设为私有" : "设为公开" }}
            </button>
            <p
              v-if="
                selected.name.startsWith('public/') ||
                selected.name === 'public'
              "
              class="muted"
            >
              public 命名空间固定公开。
            </p></template
          ><template v-else
            ><div class="search-field drawer-search">
              <AppIcon name="Search" :size="16" /><input
                v-model="drawerSearch"
                placeholder="搜索标签…"
                aria-label="搜索镜像标签"
              />
            </div>
            <div class="tag-list">
              <button
                v-for="tag in tags"
                :key="tag"
                :class="{ active: detail?.reference === tag }"
                @click="loadDetail(tag)"
              >
                <AppIcon name="Tag" :size="14" />{{ tag
                }}<AppIcon
                  v-if="detail?.reference === tag"
                  name="Check"
                  :size="14"
                />
              </button>
            </div>
            <p v-if="!tags.length" class="muted">
              {{
                selected.error
                  ? "标签读取失败，请刷新仓库后重试。"
                  : "没有可显示的标签。"
              }}
            </p>
            <div v-if="detailLoading" class="detail-loading">
              <AppIcon name="RefreshCw" class="spin" />正在读取镜像信息…
            </div>
            <p v-else-if="detailError" class="error" role="alert">
              {{ detailError }}
            </p>
            <template v-else-if="detail">
              <pre v-if="activeTab === 'manifest'" class="manifest-code">{{
                JSON.stringify(detail.manifest, null, 2)
              }}</pre>
              <template v-else
                ><div class="detail-title">
                  <h3>{{ detail.reference }}</h3>
                  <span class="badge public">可拉取</span>
                </div>
                <dl class="image-meta">
                  <div>
                    <dt>平台</dt>
                    <dd>
                      {{
                        detail.platforms?.length
                          ? `${detail.platforms.length} 个平台`
                          : `${detail.os || "未知"}/${detail.architecture || "未知"}`
                      }}
                    </dd>
                  </div>
                  <div>
                    <dt>压缩层大小</dt>
                    <dd>
                      {{
                        detail.platforms?.length
                          ? "多架构索引"
                          : size(detail.size_bytes)
                      }}
                    </dd>
                  </div>
                  <div>
                    <dt>构建时间</dt>
                    <dd>{{ date(detail.created_at) }}</dd>
                  </div>
                  <div>
                    <dt>Digest</dt>
                    <dd class="digest mono">
                      {{ detail.digest || "上游未返回摘要" }}
                    </dd>
                  </div>
                </dl>
                <div v-if="detail.platforms?.length" class="platforms">
                  <span
                    v-for="(platform, i) in detail.platforms"
                    :key="i"
                    class="badge"
                    >{{ platform.os }}/{{ platform.architecture
                    }}{{ platform.variant ? `/${platform.variant}` : "" }}</span
                  >
                </div>
                <h4 class="command-label">拉取镜像</h4>
                <div class="code-block">
                  <code>{{ pullCommand }}</code
                  ><button
                    class="icon-btn"
                    aria-label="复制拉取命令"
                    @click="copy(pullCommand, 'pull')"
                  >
                    <AppIcon
                      :name="copied === 'pull' ? 'Check' : 'Copy'"
                      :size="16"
                    />
                  </button>
                </div>
                <button
                  v-if="
                    user?.is_admin &&
                    settings?.allow_tag_delete &&
                    detail.digest
                  "
                  class="btn danger delete-button"
                  @click="showDelete = true"
                >
                  <AppIcon name="Trash2" :size="16" />删除此 Manifest
                </button></template
              ></template
            ></template
          >
        </div>
      </section>
    </div>
    <div
      v-if="showConnect"
      class="overlay modal-overlay"
      @click.self="showConnect = false"
    >
      <section
        class="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="connect-title"
      >
        <div class="modal-top">
          <span class="repo-icon teal"
            ><AppIcon name="Terminal" :size="24" /></span
          ><button
            class="icon-btn"
            aria-label="关闭连接指南"
            @click="showConnect = false"
          >
            <AppIcon name="X" />
          </button>
        </div>
        <h2 id="connect-title">Docker 客户端配置</h2>
        <p class="muted">在终端中执行以下命令。</p>
        <div
          v-for="(step, i) in [
            { name: '登录镜像仓库', command: `docker login ${host}` },
            {
              name: '为本地镜像添加标签',
              command: `docker tag my-app:latest ${host}/my-app:latest`,
            },
            {
              name: '推送镜像',
              command: `docker push ${host}/my-app:latest`,
            },
          ]"
          :key="i"
          class="connect-step"
        >
          <h4>
            <span>{{ i + 1 }}</span
            >{{ step.name }}
          </h4>
          <div class="code-block">
            <code>{{ step.command }}</code
            ><button
              class="icon-btn"
              :aria-label="`复制${step.name}命令`"
              @click="copy(step.command, `step${i}`)"
            >
              <AppIcon
                :name="copied === `step${i}` ? 'Check' : 'Copy'"
                :size="16"
              />
            </button>
          </div>
        </div>
        <div class="inline-note">
          <AppIcon name="CircleHelp" :size="17" /><span
            >使用你的管理员账号登录。生产环境通过 HTTPS 暴露此服务；本地 HTTP
            连接需要在 Docker 中配置 insecure registries。</span
          >
        </div>
      </section>
    </div>
    <div v-if="showDelete" class="overlay modal-overlay confirm-overlay">
      <section
        class="modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="delete-title"
      >
        <span class="repo-icon red"><AppIcon name="Trash2" :size="24" /></span>
        <h2 id="delete-title">删除这个 Manifest？</h2>
        <p class="muted">{{ selected?.name }}:{{ detail?.reference }}</p>
        <p>
          所有引用同一 Digest
          的标签都可能受影响，删除后无法通过控制台恢复。此操作不会自动释放磁盘空间。
        </p>
        <code class="digest">{{ detail?.digest }}</code>
        <div class="modal-actions">
          <button class="btn" :disabled="deleting" @click="showDelete = false">
            取消</button
          ><button
            class="btn danger-solid"
            :disabled="deleting"
            @click="remove"
          >
            {{ deleting ? "正在删除…" : "确认删除" }}
          </button>
        </div>
      </section>
    </div>
    <div v-if="notice" class="toast" role="status">
      <AppIcon name="AlertCircle" :size="17" />{{ notice
      }}<button class="icon-btn" aria-label="关闭提示" @click="notice = ''">
        <AppIcon name="X" :size="15" />
      </button>
    </div>
  </div>
</template>
