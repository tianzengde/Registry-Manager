import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Main from '@/views/Main.vue'
import Repositories from '@/views/Repositories.vue'
import Dashboard from '@/views/Dashboard.vue'
import Settings from '@/views/Settings.vue'

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
        component: Dashboard
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 检查认证状态
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('authToken')
  const requiresAuth = ['Dashboard', 'Settings'].includes(to.name)
  if (requiresAuth && !isAuthenticated) {
    next({ name: 'Repositories' })
  } else if (to.name === 'Login' && isAuthenticated) {
    next({ name: 'Repositories' })
  } else {
    next()
  }
})

export default router