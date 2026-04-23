<template>
  <div class="settings-page">
    <!-- 密码修改 -->
    <div class="settings-card">
      <div class="card-header">
        <div class="card-icon">
          <el-icon><Key /></el-icon>
        </div>
        <div class="card-title">
          <h3>修改密码</h3>
          <p>更新您的登录密码</p>
        </div>
      </div>
      
      <el-form
        :model="passwordForm"
        :rules="passwordRules"
        ref="passwordFormRef"
        label-position="top"
        class="settings-form"
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
          <el-button type="primary" :loading="passwordLoading" @click="handlePasswordChange">
            更新密码
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 仓库可见性 -->
    <div class="settings-card" v-if="authStore.isAdmin">
      <div class="card-header">
        <div class="card-icon">
          <el-icon><Unlock /></el-icon>
        </div>
        <div class="card-title">
          <h3>仓库可见性</h3>
          <p>设置仓库的公开或私有状态</p>
        </div>
      </div>
      
      <el-form label-position="top" class="settings-form" @submit.prevent="handleUpdateVisibility">
        <el-form-item label="选择仓库">
          <el-select 
            v-model="repoForm.name" 
            placeholder="请选择仓库" 
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="repo in repositories"
              :key="repo.name"
              :label="repo.name"
              :value="repo.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="可见性">
          <el-radio-group v-model="repoForm.is_public">
            <el-radio :label="true">
              <el-icon><Unlock /></el-icon>
              公开
            </el-radio>
            <el-radio :label="false">
              <el-icon><Lock /></el-icon>
              私有
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleUpdateVisibility">
            更新设置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 快捷操作 -->
    <div class="settings-card danger-zone">
      <div class="card-header">
        <div class="card-icon danger">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="card-title">
          <h3>危险操作</h3>
          <p>以下操作不可恢复，请谨慎操作</p>
        </div>
      </div>
      
      <div class="danger-actions">
        <div class="danger-item">
          <div class="danger-info">
            <h4>清除缓存</h4>
            <p>清除浏览器本地存储的数据</p>
          </div>
          <el-button type="warning" plain @click="handleClearCache">
            清除
          </el-button>
        </div>
        
        <div class="danger-item">
          <div class="danger-info">
            <h4>强制退出</h4>
            <p>退出当前账号并清除所有会话</p>
          </div>
          <el-button type="danger" plain @click="handleForceLogout">
            退出
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Key, Unlock, Lock, Warning } from '@element-plus/icons-vue'
import api from '@/utils/api'

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
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  passwordLoading.value = true
  try {
    await api.post('/auth/password', {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password
    })
    
    ElMessage.success('密码更新成功，请重新登录')
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    
    setTimeout(() => {
      authStore.logout()
      router.push('/login')
    }, 1500)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    passwordLoading.value = false
  }
}

// 仓库可见性
const repositories = ref([])
const repoForm = reactive({ name: '', is_public: true })

const loadRepositories = async () => {
  try {
    const resp = await api.get('/repositories/')
    repositories.value = Array.isArray(resp.data) ? resp.data : []
    if (!repoForm.name && repositories.value.length) {
      repoForm.name = repositories.value[0].name
      repoForm.is_public = repositories.value[0].is_public
    }
  } catch {}
}

watch(() => repoForm.name, (name) => {
  const repo = repositories.value.find(r => r.name === name)
  if (repo) repoForm.is_public = repo.is_public
})

const handleUpdateVisibility = async () => {
  if (!repoForm.name.trim()) {
    ElMessage.error('请选择仓库')
    return
  }
  try {
    const resp = await api.put(`/repositories/${encodeURIComponent(repoForm.name)}`, { 
      is_public: repoForm.is_public 
    })
    ElMessage.success(`已更新：${resp.data.is_public ? '公开' : '私有'}`)
    const idx = repositories.value.findIndex(r => r.name === resp.data.name)
    if (idx >= 0) repositories.value[idx].is_public = resp.data.is_public
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  }
}

const handleClearCache = async () => {
  try {
    await ElMessageBox.confirm('确定清除本地缓存？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    localStorage.clear()
    sessionStorage.clear()
    ElMessage.success('缓存已清除')
    setTimeout(() => router.go(0), 1000)
  } catch (e) {
    if (e !== 'cancel') ElMessage.info('已取消')
  }
}

const handleForceLogout = async () => {
  try {
    await ElMessageBox.confirm('确定强制退出所有设备？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.post('/auth/force-logout')
    ElMessage.success('已强制退出')
    setTimeout(() => {
      authStore.logout()
      router.push('/login')
    }, 1000)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

onMounted(() => {
  if (authStore.isAdmin) loadRepositories()
})
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 800px;
}

.settings-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f1f5f9;
}

.card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #10b981;
}

.card-icon .el-icon {
  font-size: 22px;
}

.card-icon.danger {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%);
  color: #ef4444;
}

.card-title h3 {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.card-title p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.settings-form {
  max-width: 400px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #1e293b;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
}

:deep(.el-radio-group) {
  display: flex;
  gap: 24px;
}

:deep(.el-radio) {
  display: flex;
  align-items: center;
  gap: 6px;
}

:deep(.el-radio .el-icon) {
  font-size: 16px;
}

/* 危险区域 */
.danger-zone {
  border: 1px solid #fecaca;
}

.danger-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.danger-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fef2f2;
  border-radius: 10px;
}

.danger-info h4 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.danger-info p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

@media (max-width: 768px) {
  .settings-card {
    padding: 20px;
  }
  
  .settings-form {
    max-width: 100%;
  }
  
  .danger-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>