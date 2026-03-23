# SH-MindStation Mini-Program

## 项目简介
基于 UniApp 构建的微信小程序/H5 客户端，为学生提供 AI 心理助手、心理文章阅读及自助测评服务。

## 技术栈
- **Framework**: UniApp (Vue 3)
- **State Management**: Pinia
- **UI Design**: 自定义高保登设计系统（含多级导航与安全区适配）

## 开发环境
- **IDE**: HBuilderX 或 VS Code (配合 UniApp 插件)
- **Node.js**: >= 18

## 运行与编译
1. 使用 HBuilderX 导入项目。
2. 配置 `utils/config.js` 中的 API 地址。
3. 点击菜单栏 -> 运行 -> 运行到微信开发者工具（或浏览器）。

## 核心功能
- **Chat**: 支持 RAG 的 AI 对话交互。
- **Scales**: 专业心理量表测评。
- **Profile**: 个人信息与头像上传。
