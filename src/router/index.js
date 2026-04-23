import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { AuthManager } from '@/utils/api'
import api from '@/utils/api'
import Login from '@/views/Login.vue'
import Main from '@/views/Main.vue'
import Repositories from '@/views/Repositories.vue'
import Dashboard from '@/views/Dashboard.vue'
import Settings from '@/views/Settings.vue'
import Operations from '@/views/Operations.vue'

const routes = [
  {
    path: '/',
    redirect: '/main/repos'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/main',
    name: 'Main',
    component: Main,
    redirect: '/main/repos',
    children: [
      {
        path: 'repos',
        name: 'Repositories',
        component: Repositories
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAdmin: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings,
        meta: { requiresAdmin: false }
      },
      {
        path: 'operations',
        name: 'Operations',
        component: Operations,
        meta: { requiresAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 检查认证状态（使用 Basic Auth）
router.beforeEach(async (to, from, next) => {
  const isAuth = AuthManager.isLoggedIn()

  // 未登录用户访问任何受保护路由 → 登录页
  if (to.path !== '/login' && to.path !== '/' && !isAuth) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 已登录用户访问登录页 → 首页
  if (to.path === '/login' && isAuth) {
    next({ name: 'Repositories' })
    return
  }

  // 需要管理员权限的路由 → 验证 admin
  if (to.meta.requiresAdmin) {
    if (!isAuth) {
      next({ name: 'Login' })
      return
    }
    try {
      const res = await api.get('/auth/me')
      if (!res.data.is_admin) {
        ElMessage.error('需要管理员权限')
        next({ name: 'Repositories' })
      } else {
        next()
      }
    } catch {
      next({ name: 'Login' })
    }
    return
  }

  next()
})

export default router