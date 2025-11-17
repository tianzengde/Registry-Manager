<template>
  <div class="main-layout">
    <aside class="sidebar" v-if="authStore.isAuthenticated">
      <div class="brand">
        <el-icon><Menu /></el-icon>
        <span>Registry Manager</span>
      </div>
      
      <el-menu
        :default-active="$route.name"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="Repositories" :route="{ name: 'Repositories' }">
          <el-icon><Folder /></el-icon>
          <span>仓库管理</span>
        </el-menu-item>
        
        <el-menu-item index="Dashboard" :route="{ name: 'Dashboard' }">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        
        <el-menu-item index="Settings" :route="{ name: 'Settings' }">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
      
      <div class="user-info">
        <el-button v-if="!authStore.isAuthenticated" type="primary" @click="loginVisible = true">
          登录
        </el-button>
        <el-dropdown v-else>
          <span class="user-name">
            <el-icon><User /></el-icon>
            {{ authStore.user?.username }}
          </span>
          
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
    </aside>
    
    <header class="topbar" v-if="authStore.isAuthenticated">
      <div class="spacer"></div>
      <div class="topbar-actions">
        <el-dropdown v-if="authStore.isAuthenticated">
          <span class="user-name">
            <el-icon><User /></el-icon>
            {{ authStore.user?.username }}
          </span>
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
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <el-dialog v-model="ui.loginVisible" title="登录" width="400px">
      <el-form :model="loginForm" @submit.prevent="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model="loginForm.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="loginForm.password" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loginLoading">登录</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import {
  Menu,
  Folder,
  DataAnalysis,
  Setting,
  User,
  SwitchButton
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const ui = useUiStore()

const loginLoading = ref(false)
const loginForm = ref({ username: '', password: '' })

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/main/repos')
}

const handleLogin = async () => {
  loginLoading.value = true
  try {
    const result = await authStore.login(loginForm.value)
    if (result.success) {
      ElMessage.success('登录成功')
      ui.hideLogin()
      router.push('/main/repos')
    } else {
      ElMessage.error(result.error)
    }
  } catch (e) {
    ElMessage.error('登录失败')
  } finally {
    loginLoading.value = false
  }
}

const openLogin = () => ui.showLogin()
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
}

.sidebar {
  width: 240px;
  background-color: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
}

.brand {
  padding: 20px 16px;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}

.user-info {
  padding: 16px;
  border-top: 1px solid var(--el-border-color-light);
}

.user-name {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.topbar {
  position: sticky;
  top: 0;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid var(--el-border-color-light);
  background-color: var(--el-bg-color);
  z-index: 10;
}

.topbar .spacer { flex: 1; }
.topbar-actions { display: flex; align-items: center; gap: 12px; }

@media (max-width: 768px) {
  .sidebar {
    width: 60px;
  }
  
  .brand span {
    display: none;
  }
  
  .sidebar-menu span {
    display: none;
  }
  
  .user-name span {
    display: none;
  }
}
</style>