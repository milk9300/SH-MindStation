import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw, RouteLocationNormalized, NavigationGuardNext } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue')
  },
  {
    path: '/entity',
    name: 'Entity',
    component: () => import('../views/EntityEditor.vue')
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('../views/AlertsView.vue')
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: () => import('../views/SessionsView.vue')
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/UsersView.vue')
  },
  {
    path: '/audit',
    name: 'Audit',
    component: () => import('../views/SysAuditView.vue')
  },
  {
    path: '/articles',
    name: 'Articles',
    component: () => import('../views/ArticlesView.vue')
  },
  {
    path: '/articles/:id',
    name: 'ArticleDetail',
    component: () => import('../views/ArticleDetailView.vue'),
    props: true
  },
  {
    path: '/articles/new',
    name: 'ArticleCreate',
    component: () => import('../views/ArticleDetailView.vue')
  },

  {
    path: '/scales',
    name: 'Scales',
    component: () => import('../views/ScalesView.vue')
  },
  {
    path: '/crisis-keywords',
    name: 'CrisisKeywords',
    component: () => import('../views/CrisisKeywordsView.vue')
  },
  {
    path: '/risk-levels',
    name: 'RiskLevels',
    component: () => import('../views/RiskLevelsView.vue')
  },
  {
    path: '/emergency-plans',
    name: 'EmergencyPlans',
    component: () => import('../views/EmergencyPlansView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

import { useAuthStore } from '../stores/auth'

// 全局路由守卫：未登录直接拦截并重定向到登录页
router.beforeEach((to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const authStore = useAuthStore()
  if (to.path !== '/login' && !authStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
