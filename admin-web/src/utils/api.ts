import axios from 'axios'
import { ElMessage } from 'element-plus'

// 初始化 axios 实例
const apiClient = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL as string) || '/api/',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动注入真实的管理员 Auth Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers['Authorization'] = `Token ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    let message = '网络请求遇到错误，请稍后再试'
    if (error.response) {
      if (error.response.status === 401) {
        message = '权限不足或登录已过期，请重新登录'
        // 清除失效的 Token 并跳转到登录页
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_user')
        window.location.href = '/login'
      } else if (error.response.status === 404) {
        message = '请求的资源不存在'
      } else if (error.response.status >= 500) {
        message = '服务器故障 (500 Internal Error)'
      } else {
        message = error.response.data?.error || message
      }
    }
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default apiClient
