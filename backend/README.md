# SH-MindStation Backend

## 项目简介
基于 Django 4.2 构建的系统后端，负责业务逻辑处理、LLM 接入以及知识图谱检索。

## 技术栈
- **Framework**: Django, Django REST Framework
- **Graph DB**: Neo4j (使用 `neo4j` 官方驱动)
- **Relational DB**: MySQL
- **LLM Context**: 自研意图识别与图谱检索路径算法

## 开发说明
### 虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # 或 venv\Scripts\activate On Windows
pip install -r requirements.txt
```

### 数据库配置
1. 创建 MySQL 数据库。
2. 配置环境变量 (待完善) 或 `settings.py`。
3. 执行迁移: `python manage.py migrate`

### 运行
```bash
python manage.py runserver
```

## 目录结构
- `apps/`: 业务应用模块
    - `repositories/`: 数据存取层（Neo4j/MySQL）
    - `services/`: 业务逻辑层（LLM、图谱算法等）
- `config/`: 项目配置文件
- `scripts/`: 数据导入、验证与测试脚本
