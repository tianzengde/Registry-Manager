<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="stat in statsCards" :key="stat.label">
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <component :is="stat.icon" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="dashboard-grid">
      <!-- 热门拉取 -->
      <div class="dashboard-card">
        <div class="card-header">
          <h3>热门拉取</h3>
          <el-input-number v-model="topN" :min="1" :max="10" size="small" @change="loadTopPulled" />
        </div>
        
        <div v-if="topLoading" class="loading-skeleton">
          <el-skeleton :rows="4" animated />
        </div>
        
        <div v-else-if="topPulled.length === 0" class="empty-state">
          <el-empty description="暂无数据" :image-size="80" />
        </div>
        
        <div v-else class="top-list">
          <div v-for="(item, index) in topPulled" :key="item.name" class="top-item">
            <div class="rank" :class="index < 3 ? `rank-${index + 1}` : ''">{{ index + 1 }}</div>
            <div class="repo-name">{{ item.name }}</div>
            <div class="pull-count">{{ item.pull_count }} 次</div>
          </div>
        </div>
      </div>

      <!-- 趋势分析 -->
      <div class="dashboard-card">
        <div class="card-header">
          <h3>仓库趋势</h3>
          <el-input
            v-model="trendRepoName"
            placeholder="输入仓库名..."
            clearable
            size="small"
            style="width: 180px"
            @change="loadTrends"
          />
        </div>
        
        <div v-if="trendsLoading" class="loading-skeleton">
          <el-skeleton :rows="3" animated />
        </div>
        
        <div v-else-if="!trendData" class="empty-state">
          <el-empty description="输入仓库名查看趋势" :image-size="80" />
        </div>
        
        <div v-else class="trend-stats">
          <div class="trend-stat">
            <span class="trend-value">{{ trendData.total_pulls }}</span>
            <span class="trend-label">总拉取</span>
          </div>
          <div class="trend-stat">
            <span class="trend-value">{{ trendData.tags_count }}</span>
            <span class="trend-label">标签数</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Box, Timer, Lock, Unlock } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const overviewData = ref(null)
const topLoading = ref(false)
const topPulled = ref([])
const topN = ref(5)
const trendsLoading = ref(false)
const trendData = ref(null)
const trendRepoName = ref('')

const statsCards = computed(() => [
  { 
    label: '总仓库', 
    value: overviewData.value?.total_repositories || 0, 
    icon: Box,
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
  },
  { 
    label: '总标签', 
    value: overviewData.value?.total_tags || 0, 
    icon: Timer,
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
  },
  { 
    label: '公开仓库', 
    value: overviewData.value?.public_repositories || 0, 
    icon: Unlock,
    gradient: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)'
  },
  { 
    label: '私有仓库', 
    value: overviewData.value?.private_repositories || 0, 
    icon: Lock,
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
  },
])

const loadDashboardData = async () => {
  loading.value = true
  try {
    await Promise.all([loadOverview(), loadTopPulled()])
  } catch (error) {
    ElMessage.error('加载数据失败')
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
    }
  } catch (error) {
    console.error('加载概览失败:', error)
  }

  try {
    const resp = await api.get('/repositories/')
    const repos = Array.isArray(resp.data) ? resp.data : []
    overviewData.value = {
      ...(overviewData.value || {}),
      public_repositories: repos.filter(r => r.is_public).length,
      private_repositories: repos.filter(r => !r.is_public).length,
      total_tags: repos.reduce((sum, r) => sum + (r.tags_count || 0), 0),
    }
  } catch (e) {}
}

const loadTopPulled = async () => {
  topLoading.value = true
  try {
    const response = await api.get(`/dashboard/top?n=${topN.value}`)
    topPulled.value = (response.data.items || []).map(i => ({ 
      name: i.repository, 
      pull_count: i.pulls 
    }))
  } catch (error) {
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
    trendData.value = {
      total_pulls: (data.last30 || []).reduce((acc, d) => acc + (d.pulls || 0), 0),
      tags_count: data.tags_count || 0
    }
  } catch {
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
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-icon .el-icon {
  font-size: 24px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  margin-top: 4px;
}

/* 仪表盘卡片 */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.dashboard-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
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
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
  transition: background 0.2s ease;
}

.top-item:hover {
  background: #f1f5f9;
}

.rank {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 13px;
  background: #e2e8f0;
  color: #64748b;
}

.rank-1 { background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #fff; }
.rank-2 { background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%); color: #fff; }
.rank-3 { background: linear-gradient(135deg, #d97706 0%, #b45309 100%); color: #fff; }

.repo-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  font-family: monospace;
}

.pull-count {
  font-size: 13px;
  color: #10b981;
  font-weight: 500;
}

.trend-stats {
  display: flex;
  gap: 32px;
}

.trend-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.trend-value {
  font-size: 36px;
  font-weight: 700;
  color: #10b981;
}

.trend-label {
  font-size: 14px;
  color: #64748b;
}

.loading-skeleton {
  padding: 20px 0;
}

.empty-state {
  padding: 40px 0;
}

/* 响应式 */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>