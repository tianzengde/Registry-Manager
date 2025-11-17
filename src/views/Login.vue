<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <h2>Registry Manager</h2>
          <p class="subtitle">轻量级私有镜像仓库管理平台</p>
        </div>
      </template>

      <div v-if="!isAuthenticated">
        <p>使用管理员账号登录后可管理仓库与镜像。</p>
        <el-form :model="form" :rules="rules" @submit.prevent="handleLogin">
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              autocomplete="username"
            />
          </el-form-item>
          
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              autocomplete="current-password"
              show-password
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" native-type="submit" :loading="loading">
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-else>
        <p class="welcome">欢迎回来，{{ user?.username }}</p>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="角色">{{ user?.role }}</el-descriptions-item>
          <el-descriptions-item label="上次登录">{{ user?.last_login }}</el-descriptions-item>
        </el-descriptions>
        <el-button @click="handleLogout" class="logout-btn">退出登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const loading = ref(false)
const isAuthenticated = ref(authStore.isAuthenticated)
const user = ref(authStore.user)

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await authStore.login(form)
    if (result.success) {
      ElMessage.success('登录成功')
      router.push('/main/repos')
    } else {
      ElMessage.error(result.error)
    }
  } catch (error) {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

const handleLogout = () => {
  authStore.logout()
  isAuthenticated.value = false
  user.value = null
  ElMessage.success('已退出登录')
}

onMounted(async () => {
  if (authStore.isAuthenticated) {
    const isValid = await authStore.checkAuth()
    if (!isValid) {
      isAuthenticated.value = false
      user.value = null
    }
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-bg-color-page);
  padding: 20px;
}

.login-card {
  width: 400px;
  max-width: 90vw;
}

.login-header {
  text-align: center;
}

.login-header h2 {
  margin: 0 0 8px 0;
  color: var(--el-color-primary);
}

.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.welcome {
  margin-bottom: 20px;
  font-weight: 500;
}

.logout-btn {
  margin-top: 20px;
  width: 100%;
}
</style>