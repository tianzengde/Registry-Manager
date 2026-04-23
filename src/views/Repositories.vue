<template>
  <div class="repos-page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索仓库..."
        size="large"
        clearable
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <div class="filter-group">
        <el-select v-model="visibilityFilter" placeholder="可见性" clearable size="large" style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="公开" value="public" />
          <el-option label="私有" value="private" />
        </el-select>
      </div>
      
      <el-button size="large" @click="loadRepositories" :loading="loading">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <!-- 仓库列表 -->
    <div v-if="loading" class="loading-grid">
      <el-skeleton v-for="i in 6" :key="i" :rows="3" animated class="skeleton-card" />
    </div>

    <div v-else-if="filteredRepos.length === 0" class="empty-state">
      <el-empty description="没有找到仓库" :image-size="120" />
    </div>

    <div v-else class="repos-grid">
      <div 
        v-for="repo in pagedRepos" 
        :key="repo.name" 
        class="repo-card"
        @click="showRepoDetails(repo)"
      >
        <div class="repo-header">
          <div class="repo-icon">
            <el-icon><Box /></el-icon>
          </div>
          <el-tag 
            :type="repo.is_public ? 'success' : 'info'" 
            size="small"
            effect="light"
          >
            {{ repo.is_public ? '公开' : '私有' }}
          </el-tag>
        </div>
        
        <div class="repo-body">
          <h3 class="repo-name">{{ repo.name }}</h3>
          <div class="repo-meta">
            <span class="meta-item">
              <el-icon><CollectionTag /></el-icon>
              {{ repo.tags_count || 0 }} 标签
            </span>
          </div>
        </div>
        
        <div class="repo-actions" @click.stop>
          <el-button text type="primary" @click="showRepoDetails(repo)">
            查看
          </el-button>
          <el-button 
            v-if="authStore.isAdmin"
            text 
            :type="repo.is_public ? 'warning' : 'success'"
            @click="toggleVisibility(repo)"
          >
            {{ repo.is_public ? '设为私有' : '设为公开' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="filteredRepos.length > pageSize">
      <el-pagination
        layout="prev, pager, next"
        :total="filteredRepos.length"
        :page-size="pageSize"
        v-model:current-page="currentPage"
        background
      />
    </div>

    <!-- 详情抽屉 -->
    <el-drawer 
      v-model="detailVisible" 
      :title="currentRepoName"
      size="640px"
      direction="rtl"
    >
      <template #header>
        <div class="drawer-header">
          <h3>{{ currentRepoName }}</h3>
          <el-tag v-if="repoStats" :type="repoStats.is_public ? 'success' : 'info'" size="small">
            {{ repoStats.is_public ? '公开' : '私有' }}
          </el-tag>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="标签列表" name="tags">
          <div v-if="tagsLoading" class="loading-state">
            <el-skeleton :rows="4" animated />
          </div>
          
          <div v-else-if="currentTags.length === 0" class="empty-state">
            <el-empty description="暂无标签" :image-size="80" />
          </div>
          
          <div v-else class="tags-list">
            <div v-for="tag in pagedTags" :key="tag" class="tag-card">
              <div class="tag-header">
                <span class="tag-name">{{ tag }}</span>
                <div class="tag-actions">
                  <el-button size="small" type="primary" @click="copyPullCommand(tag)">
                    复制命令
                  </el-button>
                  <el-button 
                    v-if="authStore.isAdmin"
                    size="small" 
                    type="danger"
                    @click="deleteTag(tag)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
              
              <div class="tag-info">
                <div class="info-row">
                  <span class="info-label">Digest</span>
                  <span class="info-value mono">{{ tagMeta[tag]?.digest || '—' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">大小</span>
                  <span class="info-value">{{ formatBytes(tagMeta[tag]?.size_bytes) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">架构</span>
                  <span class="info-value">{{ tagMeta[tag]?.architecture || '—' }} / {{ tagMeta[tag]?.os || '—' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">拉取次数</span>
                  <span class="info-value highlight">{{ tagMeta[tag]?.pull_count ?? 0 }} 次</span>
                </div>
              </div>
            </div>
            
            <div class="pagination-wrapper" v-if="currentTags.length > tagPageSize">
              <el-pagination
                layout="prev, pager, next"
                :total="currentTags.length"
                :page-size="tagPageSize"
                v-model:current-page="tagPage"
                small
              />
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane v-if="authStore.isAdmin" label="统计信息" name="stats">
          <div class="stats-grid" v-if="repoStats">
            <div class="stat-item">
              <span class="stat-value">{{ repoStats.tag_count }}</span>
              <span class="stat-label">标签数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ formatBytes(repoStats.size_bytes) }}</span>
              <span class="stat-label">总大小</span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Box, CollectionTag } from '@element-plus/icons-vue'
import api from '@/utils/api'

const authStore = useAuthStore()

const searchQuery = ref('')
const visibilityFilter = ref('')
const loading = ref(false)
const repositories = ref([])

const currentPage = ref(1)
const pageSize = ref(12)

const detailVisible = ref(false)
const currentRepoName = ref('')
const currentTags = ref([])
const tagsLoading = ref(false)
const tagPage = ref(1)
const tagPageSize = ref(5)
const activeTab = ref('tags')
const repoStats = ref(null)
const tagMeta = ref({})

const filteredRepos = computed(() => {
  let result = repositories.value
  
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter(r => r.name.toLowerCase().includes(q))
  }
  
  if (visibilityFilter.value) {
    result = result.filter(r => 
      visibilityFilter.value === 'public' ? r.is_public : !r.is_public
    )
  }
  
  return result
})

const pagedRepos = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRepos.value.slice(start, start + pageSize.value)
})

const pagedTags = computed(() => {
  const start = (tagPage.value - 1) * tagPageSize.value
  return currentTags.value.slice(start, start + tagPageSize.value)
})

const loadRepositories = async () => {
  loading.value = true
  try {
    const resp = await api.get('/repositories/')
    repositories.value = Array.isArray(resp.data) ? resp.data : []
  } catch {
    ElMessage.error('加载仓库失败')
  } finally {
    loading.value = false
  }
}

const showRepoDetails = async (repo) => {
  currentRepoName.value = repo.name
  activeTab.value = 'tags'
  detailVisible.value = true
  await loadTags(repo.name)
  if (authStore.isAdmin) loadRepoStats(repo.name)
}

const loadTags = async (repoName) => {
  tagsLoading.value = true
  currentTags.value = []
  tagMeta.value = {}
  try {
    const resp = await api.get(`/repositories/${encodeURIComponent(repoName)}/tags`)
    currentTags.value = resp.data.tags || []
    tagPage.value = 1
    
    await Promise.allSettled(
      currentTags.value.map(tag =>
        api.get(`/repositories/${encodeURIComponent(repoName)}/manifests/${encodeURIComponent(tag)}`)
          .then(r => { tagMeta.value[tag] = r.data })
          .catch(() => { tagMeta.value[tag] = {} })
      )
    )
  } catch {
    ElMessage.error('加载标签失败')
  } finally {
    tagsLoading.value = false
  }
}

const loadRepoStats = async (repoName) => {
  try {
    const resp = await api.get(`/repositories/${encodeURIComponent(repoName)}/stats`)
    repoStats.value = resp.data
  } catch {
    repoStats.value = null
  }
}

const toggleVisibility = async (repo) => {
  try {
    await api.put(`/repositories/${encodeURIComponent(repo.name)}`, {
      is_public: !repo.is_public
    })
    repo.is_public = !repo.is_public
    ElMessage.success(`已设为${repo.is_public ? '公开' : '私有'}`)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const deleteTag = async (tag) => {
  try {
    await ElMessageBox.confirm(`确定删除标签 "${tag}"？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/images/${encodeURIComponent(currentRepoName.value)}/tags/${encodeURIComponent(tag)}`)
    ElMessage.success('删除成功')
    await loadTags(currentRepoName.value)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const copyPullCommand = (tag) => {
  const cmd = tagMeta.value[tag]?.pull_command
    || `docker pull ${window.location.host}/${currentRepoName.value}:${tag}`
  navigator.clipboard.writeText(cmd).then(() => {
    ElMessage.success('已复制')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return '—'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  loadRepositories()
})
</script>

<style scoped>
.repos-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 搜索栏 */
.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  flex: 1;
  max-width: 400px;
}

:deep(.search-input .el-input__wrapper) {
  border-radius: 10px;
}

.filter-group .el-select {
  border-radius: 10px;
}

/* 仓库网格 */
.repos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.repo-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  border: 1px solid transparent;
}

.repo-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #e2e8f0;
}

.repo-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.repo-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #10b981;
}

.repo-icon .el-icon {
  font-size: 22px;
}

.repo-body {
  margin-bottom: 16px;
}

.repo-name {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  word-break: break-all;
}

.repo-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #64748b;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.repo-actions {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

/* 加载状态 */
.loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.skeleton-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

/* 抽屉 */
.drawer-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.drawer-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.tags-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tag-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
}

.tag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.tag-name {
  font-family: monospace;
  font-weight: 600;
  font-size: 15px;
  color: #1e293b;
}

.tag-actions {
  display: flex;
  gap: 8px;
}

.tag-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.info-label {
  color: #64748b;
}

.info-value {
  color: #1e293b;
  font-weight: 500;
}

.info-value.highlight {
  color: #10b981;
}

.info-value.mono {
  font-family: monospace;
  font-size: 12px;
  word-break: break-all;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  background: #f8fafc;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: #10b981;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.loading-state {
  padding: 24px;
}
</style>