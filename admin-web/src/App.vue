<template>
  <el-container class="admin-layout" v-if="route.path !== '/login'">
    <el-aside width="240px" class="aside-menu">
      <div class="logo">
        <el-icon :size="24" color="#22d3ee"><Connection /></el-icon>
        <span>MindStation Admin</span>
      </div>
      <el-menu
        :default-active="route.path"
        class="el-menu-vertical"
        background-color="#134e4a"
        text-color="#f0fdfa"
        active-text-color="#22d3ee"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>整体数据大盘</span>
        </el-menu-item>
        <el-menu-item index="/entity">
          <el-icon><DataBoard /></el-icon>
          <span>图谱编辑器</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Warning /></el-icon>
          <span>高危预警处理</span>
        </el-menu-item>
        <el-menu-item index="/sessions">
          <el-icon><ChatDotRound /></el-icon>
          <span>咨询会话审计</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><UserFilled /></el-icon>
          <span>学生心理档案</span>
        </el-menu-item>
        <el-menu-item index="/audit">
          <el-icon><Odometer /></el-icon>
          <span>系统操作审计</span>
        </el-menu-item>

        <el-sub-menu index="knowledge">
          <template #title>
            <el-icon><Collection /></el-icon>
            <span>知识内容管理</span>
          </template>
          <el-menu-item index="/articles">科普文章管理</el-menu-item>
          <el-menu-item index="/scales">测评量表配置</el-menu-item>
        </el-sub-menu>
      </el-menu>

    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <div class="header-left">
          <h2>{{ currentRouteName }}</h2>
        </div>
        <div class="header-right" v-if="adminUser">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="el-dropdown-link" style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
              <el-avatar size="small" style="background-color: #0891b2">{{ adminUser.real_name?.[0] || 'A' }}</el-avatar>
              {{ adminUser.real_name || 'Admin' }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="admin-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
  
  <router-view v-else />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Connection, DataBoard, Warning, ChatDotRound, Odometer, UserFilled, Collection } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const adminUserStr = localStorage.getItem('admin_user')
const adminUser = ref(adminUserStr ? JSON.parse(adminUserStr) : null)

const handleCommand = (command: string) => {
  if (command === 'logout') {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    router.push('/login')
  }
}

const currentRouteName = computed(() => {
  const map: Record<string, string> = {
    '/dashboard': '系统整体数据大盘',
    '/entity': '知识图谱实体编辑器',
    '/alerts': '高危预警工单中心',
    '/sessions': '咨询会话审计日志',
    '/users': '学生心理健康档案',
    '/audit': '系统操作审计日志',
    '/articles': '科普文章内容管理',
    '/scales': '心理测评量表配置'
  }

  return map[route.path] || 'MindStation Dashboard'
})
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.aside-menu {
  background-color: #134e4a;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 0 var(--space-md);
  color: white;
  font-family: 'Figtree', sans-serif;
  font-size: 18px;
  font-weight: 700;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
}

.admin-header {
  height: 60px;
  background-color: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-lg);
  box-shadow: var(--shadow-sm);
}

.header-left h2 {
  font-size: 18px;
  margin: 0;
  color: var(--color-text);
}

.admin-main {
  background-color: var(--color-background);
  padding: var(--space-lg);
  overflow-y: auto;
}

/* Page Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
