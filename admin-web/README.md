# SH-MindStation Admin Web

## 项目简介
校园心理知识图谱管理中心前端，基于 Vue 3 + Vite + TypeScript + Element Plus 构建。

## 启动说明

### 环境依赖
- Node.js >= 18
- npm or pnpm

### 环境变量配置
项目使用 Vite 环境变量体系，根目录下需配置以下文件：
- `.env.development`: 开发环境配置
- `.env.production`: 生产环境配置
- `.env.example`: 环境变量模板

主要变量：
- `VITE_API_BASE_URL`: 后端 API 基础路径 (如 `http://127.0.0.1:8000/api/`)

### 安装与运行
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 类型检查
npm run type-check

# 构建生产产物
npm run build
```

## 工程规范
- 类型定义：`src/types/`
- 状态管理：`src/stores/` (Pinia)
- 公共组件：`src/components/common/`
- 业务逻辑分层：复杂逻辑提取到 `src/hooks/`
