# WHI 数据问答助手

基于RAG（检索增强生成）技术的WHI（Women's Health Initiative）数据集智能问答系统。

## 功能特点

- 🔍 智能检索WHI数据集相关信息
- 💬 自然语言问答交互
- 📊 详细的答案分析和置信度评分
- 🎯 快速示例问题引导
- 📱 响应式设计，支持多设备访问

## 技术栈

- **前端**: Shiny for Python
- **后端**: Python + FastAPI
- **AI模型**: 通义千问 (Qwen)
- **向量数据库**: FAISS
- **部署**: Vercel

## 本地运行

1. 克隆项目
```bash
git clone <your-repo-url>
cd WHI
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建 `.env` 文件并添加：