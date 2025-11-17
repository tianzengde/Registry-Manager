<template>
  <div class="repositories-page">
    <div class="page-header">
      <h1>{{ authStore.isAuthenticated ? '仓库管理' : '公开仓库' }}</h1>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索仓库"
          clearable
          style="width: 300px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-button v-if="!authStore.isAuthenticated" type="primary" @click="openLogin">
          登录
        </el-button>
      </div>
    </div>

    <el-card class="repos-card">
      <template #header>
        <div class="card-header">
          <span>仓库列表</span>
          <span class="total-count">共 {{ filteredRepositories.length }} 个仓库</span>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="filteredRepositories.length === 0" class="empty-state">
        <el-empty description="暂无仓库数据" />
      </div>

      <div v-else class="repos-tree">
        <el-tree
          :data="repoTreeFiltered"
          :props="treeProps"
          node-key="id"
          highlight-current
          @node-click="handleNodeClick"
        >
          <template #default="{ data }">
            <span class="tree-node">
              <el-icon v-if="data.isLeaf ? data.under_public : true" class="public-icon"><Unlock /></el-icon>
              <el-icon v-else class="private-icon"><Lock /></el-icon>
              <span class="label">{{ data.label }}</span>
              <el-tag v-if="data.isLeaf" :type="(data.under_public ? 'success' : 'info')" size="small" class="ml-8">
                {{ data.under_public ? '公开' : '私有' }}
              </el-tag>
            </span>
          </template>
        </el-tree>
        <div class="pagination-bottom">
          <el-pagination
            layout="prev, pager, next"
            :total="filteredRepositories.length"
            :page-size="repoPageSize"
            v-model:current-page="repoPage"
          />
        </div>
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" :title="currentRepo?.name + ' - 标签列表'" width="600px">
      <div v-if="tagsLoading" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      
      <div v-else-if="currentTags.length === 0" class="empty-state">
        <el-empty description="该仓库暂无标签" />
      </div>
      
      <div v-else class="tags-list">
        <div v-for="tag in pagedTags" :key="tag" class="tag-item">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="标签">{{ tag }}</el-descriptions-item>
            <el-descriptions-item label="大小">{{ formatBytes(tagMeta[tag]?.size_bytes) }}</el-descriptions-item>
            <el-descriptions-item label="推送时间">{{ formatTime(tagMeta[tag]?.push_time) }}</el-descriptions-item>
            <el-descriptions-item label="最后拉取">{{ formatTime(tagMeta[tag]?.last_pull_time) }}</el-descriptions-item>
            <el-descriptions-item label="Digest" :span="2">{{ tagMeta[tag]?.digest || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="累计拉取" :span="2">{{ tagMeta[tag]?.pull_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="操作" :span="2">
              <el-button size="small" @click="copyPullCommand(currentRepo.name, tag)">复制拉取命令</el-button>
              <el-button
                v-if="authStore.isAuthenticated"
                size="small"
                type="danger"
                @click="deleteTag(currentRepo.name, tag)"
                class="ml-8"
              >删除标签</el-button>

            </el-descriptions-item>
          </el-descriptions>
        </div>
        <div class="pagination-bottom">
          <el-pagination
            layout="prev, pager, next"
            :total="currentTags.length"
            :page-size="pageSize"
            v-model:current-page="currentPage"
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
  Unlock,
  Lock
} from '@element-plus/icons-vue'
import api from '@/utils/api'

const authStore = useAuthStore()
const ui = useUiStore()
const searchQuery = ref('')
const loading = ref(false)
const repositories = ref([])
const detailVisible = ref(false)
const currentRepo = ref(null)
const currentTags = ref([])
const tagsLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)

const filteredRepositories = computed(() => {
  if (!searchQuery.value) return repositories.value
  
  return repositories.value.filter(repo =>
    repo.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const repoPage = ref(1)
const repoPageSize = ref(20)
const pagedRepositories = computed(() => {
  const list = filteredRepositories.value
  const start = (repoPage.value - 1) * repoPageSize.value
  return list.slice(start, start + repoPageSize.value)
})

const treeProps = { children: 'children', label: 'label' }

const repoTree = computed(() => {
  const root = {}
  for (const repo of pagedRepositories.value) {
    const parts = repo.name.split('/')
    let cursor = root
    let pathAcc = []
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      pathAcc.push(part)
      const key = pathAcc.join('/')
      cursor.children = cursor.children || {}
      if (!cursor.children[part]) {
        cursor.children[part] = {
          id: key,
          label: part,
          children: {},
        }
      }
      if (i === parts.length - 1) {
        // leaf
        cursor.children[part].isLeaf = true
        cursor.children[part].fullName = repo.name
        cursor.children[part].under_public = repo.under_public
        cursor.children[part].tags_count = repo.tags_count
      }
      cursor = cursor.children[part]
    }
  }
  const toArray = (node) => {
    if (!node.children) return []
    return Object.values(node.children).map(n => ({
      ...n,
      children: toArray(n)
    }))
  }
  return toArray(root)
})

const repoTreeFiltered = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return repoTree.value
  const filterNodes = (nodes) => {
    const res = []
    for (const n of nodes) {
      const match = (n.isLeaf && (n.fullName || '').toLowerCase().includes(q)) || (!n.isLeaf && n.label.toLowerCase().includes(q))
      const children = filterNodes(n.children || [])
      if (match || children.length) {
        res.push({ ...n, children })
      }
    }
    return res
  }
  return filterNodes(repoTree.value)
})

const handleNodeClick = (data) => {
  if (data.isLeaf) {
    showRepoDetails({ name: data.fullName, under_public: data.under_public })
  }
}

const loadRepositories = async () => {
  loading.value = true
  try {
    const response = await api.get('/repositories/')
    const data = response.data
    const list = Array.isArray(data) ? data : (data?.repositories || [])
    repositories.value = list.map(r => ({
      ...r,
      under_public: r.under_public ?? r.is_public ?? false,
      tags_count: r.tags_count ?? 0
    }))
  } catch (error) {
    ElMessage.error('加载仓库列表失败')
    console.error('加载仓库失败:', error)
  } finally {
    loading.value = false
  }
}

const loadTags = async (repoName) => {
  currentRepo.value = { name: repoName }
  tagsLoading.value = true
  detailVisible.value = true
  
  try {
    const response = await api.get(`/repositories/${encodeURIComponent(repoName)}/tags`)
    currentTags.value = response.data.tags || []
    currentPage.value = 1
    // 加载每个标签的元数据
    tagMeta.value = {}
    for (const tag of currentTags.value) {
      try {
        const metaResp = await api.get(`/repositories/${encodeURIComponent(repoName)}/manifests/${encodeURIComponent(tag)}`)
        tagMeta.value[tag] = metaResp.data
      } catch (e) {
        tagMeta.value[tag] = {}
      }
    }
  } catch (error) {
    ElMessage.error('加载标签失败')
    console.error('加载标签失败:', error)
    currentTags.value = []
  } finally {
    tagsLoading.value = false
  }
}

const pagedTags = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return currentTags.value.slice(start, start + pageSize.value)
})

const deleteTag = async (repoName, tag) => {
  try {
    await api.delete(`/images/${encodeURIComponent(repoName)}/tags/${encodeURIComponent(tag)}`)
    ElMessage.success('删除标签已提交')
    await loadTags(repoName)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}



const tagMeta = ref({})
const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return '未知'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
const formatTime = (t) => {
  if (!t) return '未知'
  try {
    const d = new Date(t)
    return d.toLocaleString()
  } catch {
    return String(t)
  }
}

const showRepoDetails = (repo) => {
  currentRepo.value = repo
  loadTags(repo.name)
}

const copyPullCommand = (repoName, tag) => {
  const command = `docker pull ${window.location.hostname}/${repoName}:${tag}`
  navigator.clipboard.writeText(command).then(() => {
    ElMessage.success('已复制拉取命令')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const handleSearch = () => {
  // 搜索功能已通过computed属性实现
}

const openLogin = () => ui.showLogin()

onMounted(() => {
  loadRepositories()
})
</script>

<style scoped>
.repositories-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-header h1 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.repos-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-count {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.repos-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.repo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.repo-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: var(--el-box-shadow-light);
}

.repo-info {
  flex: 1;
}

.repo-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 8px;
}

.public-icon {
  color: var(--el-color-success);
}

.private-icon {
  color: var(--el-color-info);
}

.repo-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tag-count {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.repo-actions {
  display: flex;
  gap: 8px;
}

.tags-list {
  max-height: 400px;
  overflow-y: auto;
}

.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  margin-bottom: 8px;
}

.tag-name {
  font-family: monospace;
  font-weight: 500;
}

.loading-container {
  padding: 20px 0;
}

.empty-state {
  padding: 40px 0;
}

.pagination-bottom {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}

.ml-8 { margin-left: 8px; }

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    flex-direction: column;
  }
  
  .header-actions .el-input {
    width: 100% !important;
  }
  
  .repo-item {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .repo-actions {
    justify-content: flex-end;
  }
}
.tree-node .label {
  font-size: 24px;
  font-weight: 600;
}
</style>