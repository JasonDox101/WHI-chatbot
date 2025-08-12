# WHI 数据问答助手

<div align="center">

![WHI Logo](https://img.shields.io/badge/WHI-Data%20Assistant-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)

基于RAG（检索增强生成）技术的WHI（Women's Health Initiative）数据集智能问答系统

[快速开始](#快速开始) • [功能特点](#功能特点) • [技术架构](#技术架构) • [使用指南](#使用指南) • [API文档](#api文档)

</div>

## 📋 目录

- [项目简介](#项目简介)
- [功能特点](#功能特点)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [API文档](#api文档)
- [项目结构](#项目结构)


## 🎯 项目简介

### 背景介绍

WHI（Women's Health Initiative）是一项长期、大规模的全国性健康研究，旨在调查影响中年和老年女性健康的主要原因，包括心血管疾病、癌症和骨质疏松症。该研究产生了海量的临床数据和研究报告，对于医学研究和公共卫生具有重要价值。

### 项目目标

本项目旨在构建一个基于RAG（检索增强生成）技术的WHI数据集智能问答系统，通过结合大型语言模型（LLM）的强大理解和生成能力与向量数据库的高效信息检索能力，使用户能够以自然语言的方式快速、准确地获取WHI数据集中的相关信息，从而：

- 🎯 降低数据访问门槛
- 🚀 提升研究效率
- 💡 促进医学研究创新
- 🤝 支持跨学科合作

## ✨ 功能特点

- 🔍 **智能检索**：基于向量相似度的精准信息检索
- 💬 **自然语言交互**：支持中英文问答，理解复杂医学术语
- 📊 **详细分析**：提供答案置信度评分和数据来源追踪
- 🎯 **快速引导**：内置示例问题，帮助用户快速上手
- 📱 **响应式设计**：支持桌面端和移动端访问
- 🔄 **实时更新**：支持数据集动态更新和索引重建
- 🛡️ **安全可靠**：API密钥加密存储，数据传输安全

## 🏗️ 技术架构

### 核心技术栈

- **前端框架**: Shiny for Python - 交互式Web应用
- **后端服务**: Python + FastAPI - 高性能API服务
- **AI模型**: 通义千问 (Qwen) - 大语言模型
- **向量数据库**: FAISS - 高效相似度检索
- **部署平台**: Vercel - 云端部署

### 系统架构图


```plaintext
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户界面       │    │   后端API      │    │   AI服务        │
│  (Shiny UI)     │◄──►│  (FastAPI)      │◄──►│  (Qwen LLM)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
│
▼
┌─────────────────┐
│   向量数据库    │
│   (FAISS)       │
└─────────────────┘
```

### RAG问答流程

1. **用户提问** → 用户通过前端界面输入自然语言问题
2. **问题预处理** → 系统对问题进行清洗和标准化处理
3. **向量化** → 利用嵌入模型将问题转化为向量表示
4. **相似度检索** → 在FAISS向量数据库中检索相关文档片段
5. **上下文构建** → 将检索结果组织为结构化上下文
6. **增强生成** → LLM基于上下文和问题生成专业答案
7. **结果返回** → 返回答案、来源信息和置信度评分


### 环境要求

- Python 3.8+
- pip 或 conda
- DashScope API Key（通义千问访问密钥）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <your-repo-url>
   cd WHI-chatbot
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   
   创建 `.env` 文件并添加您的DashScope API Key：
   ```
   DASHSCOPE_API_KEY=your_api_key_here
   ```
   请确保您的API Key具有访问通义千问模型的权限。

4. **准备向量数据库**
   
   运行数据处理脚本以生成或更新向量数据库：
   ```bash
   python data/processor.py
   ```
   此步骤会读取 `whi_dataset_desc_with_url.csv` 和 `whi_mesa_v2.csv` 文件，并构建FAISS向量索引。

5. **启动应用**
   ```bash
   python app.py
   ```
   应用将在本地启动，通常在 `http://localhost:8000`

## 📖 使用指南

### 基本使用流程

1. **访问应用**：在浏览器中打开应用地址
2. **输入问题**：在问答框中输入关于WHI数据集的问题
3. **查看结果**：系统将显示详细答案、数据来源和置信度评分
4. **探索更多**：尝试不同类型的问题或点击示例问题

### 示例问题

您可以尝试以下类型的问题：

- "WHI研究中女性心血管疾病的主要风险因素有哪些？"
- "激素替代疗法对骨密度的影响如何？"
- "WHI研究的参与者年龄分布情况？"
- "膳食钙摄入量与骨折风险的关系？"

### 功能说明

- **智能问答**：支持复杂的医学术语查询
- **历史记录**：查看之前的问答历史
- **答案详情**：点击可查看详细的数据来源信息
- **置信度评分**：了解答案的可靠程度

## 🔧 API文档

### 主要接口

#### POST /api/question

提交问题并获取答案

**请求参数：**
```json
{
  "question": "用户问题",
  "history": ["可选的历史对话"]
}
```

**响应格式：**
```json
{
  "answer": "生成的答案",
  "sources": ["数据来源列表"],
  "confidence": 0.85,
  "processing_time": 1.23
}
```

#### GET /api/health

检查系统健康状态

**响应格式：**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## 📁 项目结构
WHI-chatbot/
├── app.py                 # 主应用入口
├── requirements.txt       # 依赖包列表
├── README.md              # 项目文档
├── config/
│   └── settings.py        # 配置管理
├── data/
│   └── processor.py       # 数据处理脚本
├── graph/
│   └── state.py          # 状态管理
├── llm/
│   └── qwen_client.py    # LLM客户端
├── rag/
│   └── system.py         # RAG核心逻辑
├── static/
│   └── styles.css        # 前端样式
├── vector_store/
│   └── manager.py        # 向量数据库管理
├── whi_dataset_desc_with_url.csv  # WHI数据集描述
├── whi_mesa_v2.csv       # MESA数据集
└── whi_vectorstore/      # 向量索引文件
    ├── index.faiss
    └── index.pkl

### 核心模块说明

- **app.py**: 主应用程序，包含Shiny界面和路由逻辑
- **rag/system.py**: RAG系统核心实现，处理检索和生成逻辑
- **llm/qwen_client.py**: 通义千问模型的客户端封装
- **vector_store/manager.py**: FAISS向量数据库的管理和操作
- **data/processor.py**: 数据预处理和向量化脚本
