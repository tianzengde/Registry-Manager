import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api, { AuthManager } from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)

  const isAuthenticated = computed(() => AuthManager.isLoggedIn())
  const isAdmin = computed(() => user.value?.is_admin === true)

  // 登录：使用 fetch 发送 Basic Auth 请求，避免触发浏览器弹窗
  // 原因：axios 请求收到 401 + WWW-Authenticate 头时，浏览器会弹原生认证框
  const login = async (credentials) => {
    try {
      const token = btoa(`${credentials.username}:${credentials.password}`)
      const response = await fetch('/api/auth/me', {
        headers: {
          Authorization: `Basic ${token}`
        }
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        AuthManager.clearCredentials()
        user.value = null
        return {
          success: false,
          error: err.detail || `登录失败 (${response.status})`
        }
      }

      const userData = await response.json()
      AuthManager.setCredentials(credentials.username, credentials.password)
      user.value = userData
      return { success: true }
    } catch (error) {
      AuthManager.clearCredentials()
      user.value = null
      return {
        success: false,
        error: error.message || '网络错误'
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