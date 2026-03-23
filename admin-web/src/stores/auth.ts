import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '../types/auth'
import apiClient from '../utils/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('admin_token'))
  const userStr = localStorage.getItem('admin_user')
  const user = ref<UserInfo | null>(userStr ? JSON.parse(userStr) : null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(loginForm: any) {
    const res: any = await apiClient.post('/admin/login/', loginForm)
    token.value = res.token
    user.value = res.user
    
    localStorage.setItem('admin_token', res.token)
    localStorage.setItem('admin_user', JSON.stringify(res.user))
    
    return res
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
  }

  function restoreSession() {
    const savedToken = localStorage.getItem('admin_token')
    const savedUser = localStorage.getItem('admin_user')
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
    }
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    logout,
    restoreSession
  }
})
