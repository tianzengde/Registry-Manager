<script setup lang="ts">
const {
  repos,
  health,
  filter,
  search,
  sort,
  status,
  repoError,
  visible,
  color,
  openRepo,
  reload,
  showConnect,
} = useWorkspace();
</script>
<template>
  <section class="panel repos-panel">
    <div class="toolbar">
      <div class="filter-tabs">
        <button
          v-for="tab in [
            { id: 'all', name: '全部' },
            { id: 'private', name: '私有' },
            { id: 'public', name: '公开' },
          ]"
          :key="tab.id"
          :class="{ active: filter === tab.id }"
          @click="filter = tab.id"
        >
          {{ tab.name }}
        </button>
      </div>
      <div class="toolbar-inputs">
        <div class="search-field">
          <AppIcon name="Search" :size="16" /><input
            v-model="search"
            aria-label="搜索仓库"
            placeholder="搜索仓库名称…"
          /><kbd>/</kbd>
        </div>
        <select v-model="sort" aria-label="排序方式">
          <option value="name">名称排序</option>
          <option value="tags">标签最多</option>
        </select>
      </div>
    </div>
    <div v-if="repoError" class="empty-state">
      <span class="empty-icon"><AppIcon name="Server" :size="30" /></span>
      <h3>暂时无法连接 Registry</h3>
      <p>
        {{
          (repoError.data as any)?.statusMessage ||
          "请检查 Registry 服务地址、凭证和网络连接。"
        }}
      </p>
      <button class="btn" @click="reload">重新连接</button>
    </div>
    <div v-else-if="status === 'pending' && !repos.length" class="empty-state">
      <AppIcon name="RefreshCw" class="spin" />
      <p>正在同步镜像仓库…</p>
    </div>
    <div v-else-if="!visible.length" class="empty-state">
      <span class="empty-icon"><AppIcon name="Boxes" :size="30" /></span>
      <h3>
        {{ search || filter !== "all" ? "没有匹配的仓库" : "仓库为空" }}
      </h3>
      <p>
        {{
          search || filter !== "all"
            ? "试试其他关键词，或切换仓库可见性筛选。"
            : "使用 Docker 推送镜像，仓库会自动出现在这里。"
        }}
      </p>
      <button
        v-if="!search && filter === 'all'"
        class="btn primary"
        @click="showConnect = true"
      >
        查看推送命令<AppIcon name="ArrowRight" :size="16" />
      </button>
    </div>
    <div v-else class="table-wrap">
      <table class="repo-table">
        <thead>
          <tr>
            <th>仓库名称</th>
            <th>可见性</th>
            <th>标签</th>
            <th>标签预览</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="repo in visible"
            :key="repo.name"
            tabindex="0"
            role="button"
            :aria-label="`查看 ${repo.name}`"
            @click="openRepo(repo)"
            @keydown.enter="openRepo(repo)"
          >
            <td>
              <div class="repo-name">
                <span class="repo-icon" :class="color(repo.name)"
                  ><AppIcon name="Box" :size="22" /></span
                ><span
                  ><b>{{ repo.name }}</b
                  ><small v-if="repo.error">标签读取失败</small></span
                >
              </div>
            </td>
            <td>
              <span class="badge" :class="repo.is_public ? 'public' : ''"
                ><AppIcon
                  :name="repo.is_public ? 'Globe2' : 'LockKeyhole'"
                  :size="12"
                />{{ repo.is_public ? "公开" : "私有" }}</span
              >
            </td>
            <td>
              <span class="tag-number"
                >{{ repo.error ? "读取失败" : repo.tags_count
                }}<span v-if="!repo.error"> tags</span></span
              >
            </td>
            <td>
              <div class="tag-preview">
                <code v-for="tag in repo.tags.slice(0, 3)" :key="tag">{{
                  tag
                }}</code
                ><span v-if="repo.tags.length > 3"
                  >+{{ repo.tags.length - 3 }}</span
                >
              </div>
            </td>
            <td>
              <AppIcon name="ArrowUpRight" :size="17" class="row-arrow" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="table-footer">
      <span
        >共 {{ visible.length }} 个仓库<span
          v-if="visible.length !== repos.length"
        >
          / {{ repos.length }} 个总仓库</span
        ></span
      ><span><AppIcon name="ShieldCheck" :size="13" />Registry API v2</span>
    </div>
  </section>
</template>
