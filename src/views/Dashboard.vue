<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h1>仪表盘</h1>
      <el-button type="primary" @click="loadDashboardData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <div class="dashboard-grid">
      <!-- 概览卡片 -->
      <el-card class="overview-card">
        <template #header>
          <div class="card-header">
            <span>系统概览</span>
          </div>
        </template>
        
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="3" animated />
        </div>
        
        <div v-else class="overview-content">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="总仓库数">
              {{ overviewData?.total_repositories || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="总标签数">
              {{ overviewData?.total_tags || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="公开仓库">
              {{ overviewData?.public_repositories || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="私有仓库">
              {{ overviewData?.private_repositories || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="存储使用">
              {{ formatBytes(overviewData?.total_size || 0) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后更新">
              {{ overviewData?.last_updated || '未知' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>

      <!-- 拉取Top卡片 -->
      <el-card class="top-card">
        <template #header>
          <div class="card-header">
            <span>热门拉取排行</span>
            <el-input-number
              v-model="topN"
              :min="1"
              :max="50"
              size="small"
              @change="loadTopPulled"
            />
          </div>
        </template>
        
        <div v-if="topLoading" class="loading-container">
          <el-skeleton :rows="3" animated />
        </div>
        
        <div v-else-if="topPulled.length === 0" class="empty-state">
          <el-empty description="暂无拉取数据" />
        </div>
        
        <div v-else class="top-list">
          <div v-for="(item, index) in topPulled" :key="item.name" class="top-item">
            <div class="rank">#{{ index + 1 }}</div>
            <div class="repo-info">
              <div class="repo-name">{{ item.name }}</div>
              <div class="pull-count">{{ item.pull_count }} 次拉取</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 趋势分析卡片 -->
      <el-card class="trends-card">
        <template #header>
          <div class="card-header">
            <span>仓库趋势分析</span>
            <el-input
              v-model="trendRepoName"
              placeholder="输入仓库名称"
              clearable
              @change="loadTrends"
              style="width: 200px"
            />
          </div>
        </template>
        
        <div v-if="trendsLoading" class="loading-container">
          <el-skeleton :rows="3" animated />
        </div>
        
        <div v-else-if="!trendData" class="empty-state">
          <el-empty description="请输入仓库名称查看趋势" />
        </div>
        
        <div v-else class="trend-content">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="仓库名称">
              {{ trendData.repository }}
            </el-descriptions-item>
            <el-descriptions-item label="总拉取次数">
              {{ trendData.total_pulls || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="最近活跃">
              {{ trendData.last_activity || '未知' }}
            </el-descriptions-item>
            <el-descriptions-item label="标签数量">
              {{ trendData.tags_count || 0 }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const overviewData = ref(null)
const topLoading = ref(false)
const topPulled = ref([])
const topN = ref(5)
const trendsLoading = ref(false)
const trendData = ref(null)
const trendRepoName = ref('')

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const loadDashboardData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadOverview(),
      loadOverviewAggregates(),
      loadTopPulled()
    ])
  } catch (error) {
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

const loadOverview = async () => {
  try {
    const response = await api.get('/dashboard/overview')
    const data = response.data || {}
    overviewData.value = {
      total_repositories: data.repository_count ?? 0,
      total_tags: 0,
      public_repositories: 0,
      private_repositories: 0,
      total_size: 0,
      last_updated: new Date().toLocaleString()
    }
  } catch (error) {
    console.error('加载概览数据失败:', error)
  }
}

const loadOverviewAggregates = async () => {
  try {
    const resp = await api.get('/repositories/')
    const data = resp.data
    const repos = Array.isArray(data) ? data : (data?.repositories || [])
    let publicCount = 0
    let privateCount = 0
    let totalTags = 0
    let totalSize = 0
    const stats = await Promise.all(repos.map(r => api.get(`/repositories/${encodeURIComponent(r.name)}/stats`).then(s => s.data).catch(() => null)))
    for (let i = 0; i < repos.length; i++) {
      const r = repos[i]
      const isPublic = (r.is_public ?? r.under_public ?? false)
      if (isPublic) publicCount++
      else privateCount++
      const st = stats[i]
      if (st) {
        totalTags += st.tag_count || 0
        totalSize += st.size_bytes || 0
      }
    }
    overviewData.value = {
      ...(overviewData.value || {}),
      total_repositories: overviewData.value?.total_repositories ?? repos.length,
      public_repositories: publicCount,
      private_repositories: privateCount,
      total_tags: totalTags,
      total_size: totalSize
    }
  } catch (e) {
  }
}

const loadTopPulled = async () => {
  topLoading.value = true
  try {
    const response = await api.get(`/dashboard/top?n=${topN.value}`)
    const items = response.data.items || []
    topPulled.value = items.map(i => ({ name: i.repository, pull_count: i.pulls }))
  } catch (error) {
    console.error('加载Top数据失败:', error)
    topPulled.value = []
  } finally {
    topLoading.value = false
  }
}

const loadTrends = async () => {
  if (!trendRepoName.value.trim()) {
    trendData.value = null
    return
  }
  
  trendsLoading.value = true
  try {
    const response = await api.get(`/dashboard/trends/${encodeURIComponent(trendRepoName.value)}`)
    const data = response.data || {}
    const sumPulls = (data.last30 || []).reduce((acc, d) => acc + (d.pulls || 0), 0)
    trendData.value = {
      repository: data.name || trendRepoName.value,
      total_pulls: sumPulls,
      last_activity: '未知',
      tags_count: 0
    }
  } catch (error) {
    console.error('加载趋势数据失败:', error)
    trendData.value = null
  } finally {
    trendsLoading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.overview-content {
  padding: 12px 0;
}

.top-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
}

.rank {
  font-weight: bold;
  color: var(--el-color-primary);
  min-width: 30px;
}

.repo-info {
  flex: 1;
}

.repo-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.pull-count {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.trend-content {
  padding: 12px 0;
}

.loading-container {
  padding: 20px 0;
}

.empty-state {
  padding: 40px 0;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}
</style>