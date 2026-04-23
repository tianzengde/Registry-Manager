import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api, { AuthManager } from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)

  const isAuthenticated = computed(() => AuthManager.isLoggedIn())
  const isAdmin = computed(() => user.value?.is_admin === true)

  // 登录：使用 Basic Auth 凭证验证
  const login = async (credentials) => {
    try {
      // 先设置凭证，然后请求 /auth/me 验证
      AuthManager.setCredentials(credentials.username, credentials.password)

      const response = await api.get('/auth/me')
      user.value = response.data
      return { success: true }
    } catch (error) {
      AuthManager.clearCredentials()
      user.value = null
      return {
        success: false,
        error: error.response?.data?.detail || '用户名或密码错误'
      }
    }
  }

  const logout = () => {
    AuthManager.clearCredentials()
    user.value = null
  }

  // 检查当前认证状态
  const checkAuth = async () => {
    if (!AuthManager.isLoggedIn()) {
      user.value = null
      return false
    }
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  // 获取用户信息
  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      user.value = null
    }
  }

  return {
    user,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    checkAuth,
    fetchUser,
    AuthManager
  }
})