<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
          </svg>
        </div>
        <span class="brand-text">Registry</span>
      </div>

      <nav class="sidebar-nav">
        <router-link 
          v-for="item in navItems" 
          :key="item.route"
          :to="item.route"
          class="nav-item"
          :class="{ active: $route.name === item.route }"
        >
          <component :is="item.icon" class="nav-icon" />
          <span class="nav-text">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-card" v-if="authStore.user">
          <div class="user-avatar">
            {{ authStore.user.username?.charAt(0).toUpperCase() }}
          </div>
          <div class="user-info">
            <div class="user-name">{{ authStore.user.username }}</div>
            <div class="user-role">{{ authStore.user.is_admin ? '管理员' : '用户' }}</div>
          </div>
          <el-dropdown trigger="click">
            <el-button text class="more-btn">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="topbar">
        <div class="page-title">
          <h1>{{ currentPageTitle }}</h1>
        </div>
        <div class="topbar-actions">
          <el-button text @click="refreshData" :loading="refreshing">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </header>
      
      <div class="content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Folder,
  DataAnalysis,
  Setting,
  Operation,
  Refresh,
  SwitchButton,
  MoreFilled
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)
const refreshing = ref(false)

const navItems = [
  { route: 'Repositories', label: '仓库', icon: Folder },
  { route: 'Dashboard', label: '仪表盘', icon: DataAnalysis },
  { route: 'Operations', label: '操作日志', icon: Operation },
  { route: 'Settings', label: '设置', icon: Setting },
]

const currentPageTitle = computed(() => {
  const titles = {
    Repositories: '仓库管理',
    Dashboard: '仪表盘',
    Operations: '操作日志',
    Settings: '设置'
  }
  return titles[route.name] || 'Registry Manager'
})

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const refreshData = async () => {
  refreshing.value = true
  setTimeout(() => {
    refreshing.value = false
    ElMessage.success('已刷新')
  }, 800)
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    await authStore.checkAuth()
  }
})
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 72px;
}

.brand {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-icon svg {
  width: 20px;
  height: 20px;
  color: #fff;
}

.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.5px;
}

.sidebar.collapsed .brand-text {
  display: none;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  color: #64748b;
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  color: #10b981;
}

.nav-item.active .nav-icon {
  color: #10b981;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
}

.sidebar.collapsed .nav-text {
  display: none;
}

/* 用户卡片 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e2e8f0;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 10px;
  background: #f8fafc;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 12px;
  color: #10b981;
}

.sidebar.collapsed .user-info,
.sidebar.collapsed .more-btn {
  display: none;
}

.more-btn {
  padding: 4px;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: 72px;
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.page-title h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.5px;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-actions .el-button {
  width: 40px;
  height: 40px;
  border-radius: 10px;
}

.content-wrapper {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 72px;
  }
  
  .brand-text,
  .nav-text,
  .user-info {
    display: none;
  }
  
  .content-wrapper {
    padding: 16px;
  }
  
  .topbar {
    padding: 0 16px;
    height: 60px;
  }
  
  .page-title h1 {
    font-size: 18px;
  }
}
</style>