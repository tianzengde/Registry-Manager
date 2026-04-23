import axios from 'axios'

// Basic Auth 凭证管理器
// 统一认证：Web 前端和 Docker Client 共用同一套用户名/密码
const AuthManager = {
  getCredentials() {
    const username = localStorage.getItem('auth_username')
    const password = localStorage.getItem('auth_password')
    if (!username || !password) return null
    return { username, password }
  },

  setCredentials(username, password) {
    localStorage.setItem('auth_username', username)
    localStorage.setItem('auth_password', password)
  },

  clearCredentials() {
    localStorage.removeItem('auth_username')
    localStorage.removeItem('auth_password')
  },

  getAuthHeader() {
    const creds = this.getCredentials()
    if (!creds) return null
    const token = btoa(`${creds.username}:${creds.password}`)
    return `Basic ${token}`
  },

  isLoggedIn() {
    return !!this.getCredentials()
  }
}

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器 - 自动附加 Basic Auth 凭证
api.interceptors.request.use(
  (config) => {
    const authHeader = AuthManager.getAuthHeader()
    if (authHeader) {
      config.headers.Authorization = authHeader
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理 401 和错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      AuthManager.clearCredentials()
      // 只在非 login 页面时跳转
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export { AuthManager }
export default api