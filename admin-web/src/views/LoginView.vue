<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="48" color="#0891b2"><Connection /></el-icon>
        <h2>MindStation Admin</h2>
        <p class="subtitle">校园心理知识图谱管理中心</p>
      </div>

      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="管理员账号"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            size="large"
            :loading="loading"
            @click="handleLogin"
          >
            登录控制台
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>系统环境: Django 5.0 + Neo4j</p>
        <p>建议使用 Chrome 或 Edge 极速模式访问</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = reactive<FormRules>({
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await authStore.login({
          username: loginForm.username,
          password: loginForm.password
        })
        
        ElMessage.success('欢迎回来，' + (res.user.real_name || '管理员'))
        router.push('/dashboard')
      } catch (e: any) {
        // Axios 拦截器已经弹出了对应的错误提示
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #134e4a 0%, #0f172a 100%);
}

.login-card {
  width: 400px;
  background: white;
  border-radius: 12px;
  padding: 40px 40px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 15px 0 5px;
  font-size: 24px;
  color: #1e293b;
}

.subtitle {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

.login-btn {
  width: 100%;
  border-radius: 6px;
  background-color: #0891b2;
  border-color: #0891b2;
}

.login-btn:hover {
  background-color: #06b6d4;
  border-color: #06b6d4;
}

.login-footer {
  margin-top: 30px;
  text-align: center;
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.6;
}

.login-footer p {
  margin: 0;
}
</style>
