<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>设置</h1>
    </div>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>

      <el-form
        :model="passwordForm"
        :rules="passwordRules"
        ref="passwordFormRef"
        label-width="120px"
        @submit.prevent="handlePasswordChange"
      >
        <el-form-item label="当前密码" prop="current_password">
          <el-input
            v-model="passwordForm.current_password"
            type="password"
            placeholder="请输入当前密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="passwordLoading"
          >
            更新密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>仓库可见性设置</span>
        </div>
      </template>

      <el-form :model="repoForm" label-width="140px" @submit.prevent="handleUpdateVisibility">
        <el-form-item label="选择仓库">
          <el-select v-model="repoForm.name" placeholder="请选择仓库" filterable style="width: 360px">
            <el-option
              v-for="repo in repositories"
              :key="repo.name"
              :label="repo.name"
              :value="repo.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="是否公开">
          <el-switch v-model="repoForm.is_public" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit">更新</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const passwordFormRef = ref()
const passwordLoading = ref(false)

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handlePasswordChange = async () => {
  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return
    
    passwordLoading.value = true
    
    const response = await api.post('/auth/change-password', {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password
    })
    
    ElMessage.success('密码更新成功，请重新登录')
    
    // 清空表单
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    
    // 提示重新登录
    setTimeout(() => {
      authStore.logout()
      router.push('/login')
    }, 1500)
    
  } catch (error) {
    const message = error.response?.data?.detail || '密码更新失败'
    ElMessage.error(message)
  } finally {
    passwordLoading.value = false
  }
}

// 仓库可见性设置
const repositories = ref([])
const repoForm = reactive({ name: '', is_public: true })
const loadRepositoriesForSettings = async () => {
  try {
    const response = await api.get('/repositories/')
    const data = response.data
    repositories.value = Array.isArray(data) ? data : (data?.repositories || [])
    if (!repoForm.name && repositories.value.length) {
      repoForm.name = repositories.value[0].name
      repoForm.is_public = repositories.value[0].is_public ?? repositories.value[0].under_public ?? false
    }
  } catch {}
}

watch(() => repoForm.name, (name) => {
  const repo = repositories.value.find(r => r.name === name)
  if (repo) {
    repoForm.is_public = (repo.is_public ?? repo.under_public ?? false)
  }
})

const handleUpdateVisibility = async () => {
  if (!repoForm.name.trim()) {
    ElMessage.error('请选择仓库')
    return
  }
  try {
    const resp = await api.put(`/repositories/${encodeURIComponent(repoForm.name)}`, { is_public: repoForm.is_public })
    ElMessage.success(`已更新：${resp.data.name} -> ${resp.data.is_public ? '公开' : '私有'}`)
const idx = repositories.value.findIndex(r => r.name === resp.data.name)
if (idx >= 0) {
  repositories.value[idx].is_public = resp.data.is_public
  repositories.value[idx].under_public = resp.data.is_public
}
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  }
}

const handleClearCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除本地缓存吗？这将清除所有本地存储的数据。',
      '确认清除缓存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    localStorage.clear()
    sessionStorage.clear()
    
    ElMessage.success('缓存已清除')
    
    // 重新加载页面
    setTimeout(() => {
      router.go(0) // 使用路由重载页面
    }, 1000)
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.info('已取消清除缓存')
    }
  }
}

const handleRefreshAll = async () => {
  try {
    ElMessage.info('正在刷新所有数据...')
    
    // 这里可以添加刷新所有数据的逻辑
    // 例如重新加载用户信息、仓库列表等
    
    setTimeout(() => {
      ElMessage.success('数据刷新完成')
    }, 1000)
    
  } catch (error) {
    ElMessage.error('刷新数据失败')
  }
}

const handleForceLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要强制退出所有设备吗？这将在所有设备上终止当前会话。',
      '确认强制退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用强制退出API
    await api.post('/auth/force-logout')
    
    ElMessage.success('已强制退出所有设备')
    
    // 清除本地存储并跳转到登录页
    setTimeout(() => {
      authStore.logout()
      router.push('/login')
    }, 1000)
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('强制退出失败')
    } else {
      ElMessage.info('已取消强制退出')
    }
  }
}
onMounted(() => {
  loadRepositoriesForSettings()
})
</script>

<style scoped>
.settings-page {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

@media (max-width: 768px) {
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  :deep(.el-form-item__label) {
    width: 100px !important;
  }
  
  :deep(.el-form-item__content) {
    margin-left: 100px !important;
  }
}
</style>