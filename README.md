# SH-MindStation | 校园心理知识图谱与预警中枢

<p align="center">
  <img src="https://img.shields.io/badge/Backend-Django%204.2-green?style=for-the-badge&logo=django" alt="Backend">
  <img src="https://img.shields.io/badge/Frontend-Vue%203%20%2B%20Vite-blue?style=for-the-badge&logo=vue.js" alt="Frontend">
  <img src="https://img.shields.io/badge/Database-MySQL%20%2B%20Neo4j-orange?style=for-the-badge&logo=neo4j" alt="Database">
  <img src="https://img.shields.io/badge/AI-LLM%20%2B%20RAG-red?style=for-the-badge&logo=openai" alt="AI">
  <img src="https://img.shields.io/badge/Task-Celery-blueviolet?style=for-the-badge&logo=celery" alt="Celery">
</p>

## 🌟 项目简介

**SH-MindStation** 是一款专为校园心理健康设计的辅助诊断与知识管理系统。它通过深度集成 **知识图谱 (Knowledge Graph)** 与 **大语言模型 (LLM)**，为学生提供即时的 AI 心理咨询支持，为心理老师提供直观的图谱管理与高危预警协同中枢。

> [!IMPORTANT]
> **Production-Ready**: 本项目已完成深度工程化改造，具备高可维护性、标准化 API 协议及完善的异步任务处理能力。

---

## 🛠️ 核心模块与功能

### 1. 🤖 AI 智能咨询 (User-End)
- **对话流控制**: 集成意图识别模型，支持从闲聊到心理咨询模式的平滑切换。
- **RAG 检索增强**: 结合向量数据库与知识图谱的混合检索方式，确保 AI 生成内容的专业性与事实准确性。
- **历史记录持久化**: 支持分页加载、重复过滤及上下文记忆恢复。

### 2. 📊 心理知识图谱 (Admin-End)
- **多维可视化**: 基于 AntV G6 的交互式图谱编辑器，支持实体关联的动态增删改查。
- **关联分析**: 自动挖掘心理症状、成因及干预方案之间的复杂联系。
- **知识精度优化**: 剔除非心理学相关的冗余数据，确保图谱数据的纯净度。

### 3. 📝 交互式心理测评 (Assessment)
- **异步分析体系**: 基于 Celery 的分布式任务队列，实现 SCL-90 等复杂量表的自动算分与报告生成。
- **趋势可视化**: 实时跟踪用户历史测评数据，形成动态心理健康画像。

### 4. ⚠️ 心理健康预警 (Security)
- **高危检测**: 自动筛选包含自伤、社交障碍等风险模式的对话及测评结果。
- **审计中心**: 标准化的系统日志审计，确保每项操作可溯源。

---

## 🚀 工程化优化亮点 (Recent Updates)

本项目近期经历了核心架构与代码质量的全面重构：

- **[Architectural] 统一分页协议**: 全面采用标准化的 `PageNumberPagination`，极大简化了前端对接复杂度并提升了性能。
- **[RAG] 向量同步引擎**: 开发了专门的向量索引同步与稠密图生成脚本 (`scripts/rebuild_dense_graph_v6.py`)，提升搜索召回率。
- **[Stability] 异常防御性设计**: 实现 Fail-Fast 校验机制，修复了大量异步任务中的 DNS 与连接超时问题。
- **[Cleanness] 领域精炼**: 对知识库进行了清洗，通过实体归类脚本自动分离非核心科普文章，提升逻辑检索效率。
- **[Security] 零信任认证**: 管理端与小程序端统一采用安全加固的鉴权逻辑，支持环境变量一键配置。

---

## 📦 技术大图

| 维度 | 技术选型 |
| :--- | :--- |
| **后端框架** | Python 3.10+ / Django 4.2 / Django REST Framework |
| **异步任务** | Celery / Redis |
| **图数据库** | Neo4j 5.x (Cypher 查询优化) |
| **关系数据库** | MySQL 8.0 (ACID 事务保障) |
| **管理端前端** | Vue 3 (Setup) / Vite / TypeScript / Element Plus |
| **终端小程序** | UniApp / Pinia (Auth & Store) |

---

## 🚦 快速启动

### 1. 环境准备
- Node.js >= 18
- Python >= 3.10
- Neo4j, MySQL, Redis 服务可用

### 2. 后端部署
```bash
cd backend
# 建议使用虚拟环境
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# 启动异步任务
celery -A backend_project worker -l info -P eventlet
```

### 3. 管理端部署
```bash
cd admin-web
npm install
npm run dev
```

### 4. 小程序部署
使用 **HBuilderX** 打开 `wx_app` 目录，编译运行至微信开发者工具。

---

## 🔎 常用脚本工具
位于 `backend/scripts/` 目录下：
- `sync_vector_index.py`: 手动触发图谱向量同步。
- `rebuild_dense_graph_v6.py`: 重构稠密连接子图以优化检索。
- `verify/`: 包含文章数据、日志审计等模块的自动化校验工具。

---
*Powered by SH MindStation Team. All Rights Reserved.*
