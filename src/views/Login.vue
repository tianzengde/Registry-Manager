<template>
  <div class="login-container">
    <!-- 左侧品牌区 -->
    <div class="brand-side">
      <div class="brand-content">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
          </svg>
        </div>
        <h1>Registry Manager</h1>
        <p>轻量级私有镜像仓库管理平台</p>
        
        <div class="features">
          <div class="feature">
            <el-icon><Check /></el-icon>
            <span>镜像仓库管理</span>
          </div>
          <div class="feature">
            <el-icon><Check /></el-icon>
            <span>标签版本控制</span>
          </div>
          <div class="feature">
            <el-icon><Check /></el-icon>
            <span>访问权限控制</span>
          </div>
          <div class="feature">
            <el-icon><Check /></el-icon>
            <span>操作日志审计</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-side">
      <div class="login-form-wrapper">
        <div v-if="!isAuthenticated" class="login-form">
          <h2>登录</h2>
          <p class="form-desc">使用您的账号登录管理平台</p>
          
          <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名"
                size="large"
                autocomplete="username"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                size="large"
                autocomplete="current-password"
                show-password
                @keyup.enter="handleLogin"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item>
              <el-button 
                type="primary" 
                size="large" 
                :loading="loading" 
                class="login-btn"
                @click="handleLogin"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 已登录状态 -->
        <div v-else class="logged-in">
          <div class="welcome-card">
            <div class="welcome-avatar">
              {{ user?.username?.charAt(0).toUpperCase() }}
            </div>
            <h2>欢迎回来</h2>
            <p class="username">{{ user?.username }}</p>
            <el-tag :type="user?.is_admin ? 'success' : 'info'" size="small">
              {{ user?.is_admin ? '管理员' : '普通用户' }}
            </el-tag>
          </div>
          
          <el-button size="large" class="logout-btn" @click="handleLogout">
            退出登录
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock, Check } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const isAuthenticated = computed(() => authStore.isAuthenticated)
const user = computed(() => authStore.user)

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    const result = await authStore.login(form)
    if (result.success) {
      ElMessage.success('登录成功')
      router.push('/main/repos')
    } else {
      ElMessage.error(result.error)
    }
  } catch {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
}

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await authStore.checkAuth()
  }
})
</script>

<style scoped>
.login-container {
  display: flex;
  min-height: 100vh;
}

/* 左侧品牌区 */
.brand-side {
  flex: 1;
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.brand-content {
  text-align: center;
  color: #fff;
}

.brand-icon {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  backdrop-filter: blur(10px);
}

.brand-icon svg {
  width: 40px;
  height: 40px;
  color: #fff;
}

.brand-content h1 {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.brand-content > p {
  margin: 0 0 48px;
  opacity: 0.9;
  font-size: 16px;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: flex-start;
  max-width: 280px;
  margin: 0 auto;
}

.feature {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.1);
  padding: 12px 20px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  width: 100%;
  font-size: 14px;
  font-weight: 500;
}

.feature .el-icon {
  font-size: 16px;
  color: #86efac;
}

/* 右侧登录区 */
.login-side {
  width: 480px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.login-form-wrapper {
  width: 100%;
  max-width: 360px;
}

.login-form h2 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
}

.form-desc {
  margin: 0 0 32px;
  color: #64748b;
  font-size: 14px;
}

.el-form-item {
  margin-bottom: 20px;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 4px 16px;
}

:deep(.el-input--large .el-input__wrapper) {
  padding: 8px 16px;
}

.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
}

.login-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

/* 已登录状态 */
.logged-in {
  text-align: center;
}

.welcome-card {
  margin-bottom: 24px;
}

.welcome-avatar {
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: #fff;
  font-size: 28px;
  font-weight: 700;
}

.welcome-card h2 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #1e293b;
}

.username {
  margin: 0 0 12px;
  color: #64748b;
}

.logout-btn {
  width: 100%;
  height: 48px;
  border-radius: 10px;
  font-size: 15px;
  border: 1px solid #e2e8f0;
  color: #64748b;
}

.logout-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

/* 响应式 */
@media (max-width: 900px) {
  .brand-side {
    display: none;
  }
  
  .login-side {
    width: 100%;
  }
}
</style>