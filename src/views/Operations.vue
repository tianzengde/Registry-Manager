<template>
  <div class="operations-page">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索操作记录..."
          clearable
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="filters.action" placeholder="操作类型" clearable style="width: 140px">
          <el-option label="全部" value="" />
          <el-option label="创建" value="create" />
          <el-option label="删除" value="delete" />
          <el-option label="更新" value="update" />
          <el-option label="拉取" value="pull" />
          <el-option label="推送" value="push" />
        </el-select>
        
        <el-date-picker
          v-model="filters.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 260px"
        />
      </div>
      
      <el-button @click="loadOperations" :loading="loading">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <!-- 操作列表 -->
    <div class="operations-card">
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="6" animated />
      </div>
      
      <div v-else-if="filteredOperations.length === 0" class="empty-state">
        <el-empty description="暂无操作记录" :image-size="100" />
      </div>
      
      <div v-else class="operations-list">
        <div 
          v-for="op in pagedOperations" 
          :key="op.id" 
          class="operation-item"
        >
          <div class="op-icon" :class="getActionClass(op.action)">
            <el-icon>
              <component :is="getActionIcon(op.action)" />
            </el-icon>
          </div>
          
          <div class="op-content">
            <div class="op-header">
              <span class="op-action" :class="getActionClass(op.action)">
                {{ getActionLabel(op.action) }}
              </span>
              <span class="op-target">{{ op.target }}</span>
            </div>
            <div class="op-details">
              <span class="op-user">
                <el-icon><User /></el-icon>
                {{ op.username || '系统' }}
              </span>
              <span class="op-time">
                <el-icon><Clock /></el-icon>
                {{ formatTime(op.created_at) }}
              </span>
            </div>
          </div>
          
          <div class="op-status">
            <el-tag 
              :type="op.status === 'success' ? 'success' : 'danger'" 
              size="small"
              effect="light"
            >
              {{ op.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="filteredOperations.length > pageSize">
        <el-pagination
          layout="total, prev, pager, next"
          :total="filteredOperations.length"
          :page-size="pageSize"
          v-model:current-page="currentPage"
          background
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Search, Refresh, User, Clock,
  Plus, Delete, Edit, Download, Upload
} from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const operations = ref([])

const filters = reactive({
  keyword: '',
  action: '',
  dateRange: null
})

const currentPage = ref(1)
const pageSize = ref(20)

const filteredOperations = computed(() => {
  let result = operations.value
  
  if (filters.keyword.trim()) {
    const q = filters.keyword.trim().toLowerCase()
    result = result.filter(op => 
      op.target?.toLowerCase().includes(q) ||
      op.username?.toLowerCase().includes(q)
    )
  }
  
  if (filters.action) {
    result = result.filter(op => op.action === filters.action)
  }
  
  if (filters.dateRange && filters.dateRange.length === 2) {
    const [start, end] = filters.dateRange
    result = result.filter(op => {
      const date = op.created_at?.split('T')[0]
      return date >= start && date <= end
    })
  }
  
  return result
})

const pagedOperations = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredOperations.value.slice(start, start + pageSize.value)
})

const loadOperations = async () => {
  loading.value = true
  try {
    const resp = await api.get('/logs/operations')
    operations.value = resp.data?.items ?? []
  } catch {
    ElMessage.error('加载操作记录失败')
  } finally {
    loading.value = false
  }
}

const getActionIcon = (action) => {
  const icons = {
    create: Plus,
    delete: Delete,
    update: Edit,
    pull: Download,
    push: Upload
  }
  return icons[action] || Edit
}

const getActionLabel = (action) => {
  const labels = {
    create: '创建',
    delete: '删除',
    update: '更新',
    pull: '拉取',
    push: '推送'
  }
  return labels[action] || action
}

const getActionClass = (action) => {
  const classes = {
    create: 'action-create',
    delete: 'action-delete',
    update: 'action-update',
    pull: 'action-pull',
    push: 'action-push'
  }
  return classes[action] || ''
}

const formatTime = (time) => {
  if (!time) return '—'
  try {
    return new Date(time).toLocaleString('zh-CN')
  } catch {
    return time
  }
}

onMounted(() => {
  loadOperations()
})
</script>

<style scoped>
.operations-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
}

.search-input {
  max-width: 320px;
}

.operations-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.operations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.operation-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  transition: background 0.2s ease;
}

.operation-item:hover {
  background: #f1f5f9;
}

.op-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.op-icon .el-icon {
  font-size: 20px;
  color: #fff;
}

.op-icon.action-create { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.op-icon.action-delete { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
.op-icon.action-update { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
.op-icon.action-pull { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
.op-icon.action-push { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); }

.op-content {
  flex: 1;
  min-width: 0;
}

.op-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.op-action {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

.op-action.action-create { color: #059669; background: #d1fae5; }
.op-action.action-delete { color: #dc2626; background: #fee2e2; }
.op-action.action-update { color: #d97706; background: #fef3c7; }
.op-action.action-pull { color: #2563eb; background: #dbeafe; }
.op-action.action-push { color: #7c3aed; background: #ede9fe; }

.op-target {
  font-family: monospace;
  font-size: 14px;
  color: #1e293b;
  word-break: break-all;
}

.op-details {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #64748b;
}

.op-user, .op-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.op-status {
  flex-shrink: 0;
}

.loading-state, .empty-state {
  padding: 40px 0;
  text-align: center;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    flex-direction: column;
  }
  
  .search-input {
    max-width: 100%;
  }
  
  .operation-item {
    flex-direction: column;
  }
  
  .op-details {
    flex-direction: column;
    gap: 8px;
  }
}
</style>