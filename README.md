# WHI Data Q&A Assistant

<div align="center">

![WHI Logo](https://img.shields.io/badge/WHI-Data%20Assistant-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)

Intelligent Q&A system for WHI (Women's Health Initiative) dataset based on RAG (Retrieval-Augmented Generation) technology



</div>

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Technical Architecture](#technical-architecture)
- [Quick Start](#quick-start)
- [User Guide](#user-guide)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)


## 🎯 Project Overview

### Background

WHI (Women's Health Initiative) is a long-term, large-scale national health study aimed at investigating the major causes affecting the health of middle-aged and elderly women, including cardiovascular disease, cancer, and osteoporosis. This research has generated massive clinical data and research reports, which are of great value for medical research and public health.

### Project Goals

This project aims to build an intelligent Q&A system for the WHI dataset based on RAG (Retrieval-Augmented Generation) technology. By combining the powerful understanding and generation capabilities of Large Language Models (LLM) with the efficient information retrieval capabilities of vector databases, users can quickly and accurately obtain relevant information from the WHI dataset in natural language, thereby:

- 🎯 Lowering data access barriers
- 🚀 Improving research efficiency
- 💡 Promoting medical research innovation
- 🤝 Supporting interdisciplinary collaboration

## ✨ Features

- 🔍 **Intelligent Retrieval**: Precise information retrieval based on vector similarity
- 💬 **Natural Language Interaction**: Supports Chinese and English Q&A, understands complex medical terminology
- 📊 **Detailed Analysis**: Provides answer confidence scores and data source tracking
- 🎯 **Quick Guidance**: Built-in example questions to help users get started quickly
- 📱 **Responsive Design**: Supports desktop and mobile access
- 🔄 **Real-time Updates**: Supports dynamic dataset updates and index rebuilding
- 🛡️ **Security & Reliability**: Encrypted API key storage, secure data transmission

## 🏗️ Technical Architecture

### Core Technology Stack

- **Frontend Framework**: Shiny for Python - Interactive Web Application
- **Backend Service**: Python + FastAPI - High-performance API Service
- **AI Model**: Qwen (Tongyi Qianwen) - Large Language Model
- **Vector Database**: FAISS - Efficient Similarity Search
- **Deployment Platform**: Vercel - Cloud Deployment

### System Architecture Diagram


```plaintext
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Interface │    │   Backend API   │    │   AI Service    │
│  (Shiny UI)     │◄──►│  (FastAPI)      │◄──►│  (Qwen LLM)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
│
▼
┌─────────────────┐
│  Vector Database │
│   (FAISS)       │
└─────────────────┘
```

### RAG Q&A Process

1. **User Question** → User inputs natural language question through frontend interface
2. **Question Preprocessing** → System cleans and standardizes the question
3. **Vectorization** → Uses embedding model to convert question into vector representation
4. **Similarity Search** → Retrieves relevant document fragments from FAISS vector database
5. **Context Construction** → Organizes search results into structured context
6. **Augmented Generation** → LLM generates professional answers based on context and question
7. **Result Return** → Returns answer, source information, and confidence score


### Environment Requirements

- Python 3.8+
- pip or conda
- DashScope API Key (Qwen access key)

### Installation Steps

1. **Clone Project**
   ```bash
   git clone <your-repo-url>
   cd WHI-chatbot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   
   Create `.env` file and add your DashScope API Key:
   ```
   DASHSCOPE_API_KEY=your_api_key_here
   ```
   Please ensure your API Key has permission to access Qwen models.

4. **Prepare Vector Database**
   
   Run data processing script to generate or update vector database:
   ```bash
   python data/processor.py
   ```
   This step will read `whi_dataset_desc_with_url.csv` and `whi_mesa_v2.csv` files and build FAISS vector index.

5. **Start Application**
   ```bash
   python app.py
   ```
   The application will start locally, usually at `http://localhost:8000`

## 📖 User Guide

### Basic Usage Flow

1. **Access Application**: Open the application address in your browser
2. **Input Question**: Enter questions about WHI dataset in the Q&A box
3. **View Results**: System will display detailed answers, data sources, and confidence scores
4. **Explore More**: Try different types of questions or click example questions

### Example Questions

You can try the following types of questions:

- "What are the main risk factors for cardiovascular disease in women in the WHI study?"
- "How does hormone replacement therapy affect bone density?"
- "What is the age distribution of WHI study participants?"
- "What is the relationship between dietary calcium intake and fracture risk?"

### Feature Description

- **Intelligent Q&A**: Supports complex medical terminology queries
- **History Records**: View previous Q&A history
- **Answer Details**: Click to view detailed data source information
- **Confidence Score**: Understand the reliability of answers

## 🔧 API Documentation

### Main Interfaces

#### POST /api/question

Submit question and get answer

**Request Parameters:**
```json
{
  "question": "User question",
  "history": ["Optional conversation history"]
}
```

**Response Format:**
```json
{
  "answer": "Generated answer",
  "sources": ["Data source list"],
  "confidence": 0.85,
  "processing_time": 1.23
}
```

#### GET /api/health

Check system health status

**Response Format:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## 📁 Project Structure
```plaintext
WHI-chatbot/
├── app.py # Main application entry
├── requirements.txt # Dependency list
├── README.md # Project documentation
├── config/
│ └── settings.py # Configuration management
├── data/
│ └── processor.py # Data processing script
├── graph/
│ └── state.py # State management
├── handlers/ # UI and interaction handlers
│ ├── __init__.py # Handler module initialization
│ ├── history_handlers.py # Answer history management
│ ├── message_handlers.py # Chat message processing
│ ├── question_processor.py # Question analysis and processing
│ ├── ui_components.py # UI component rendering
│ └── utils.py # UI utility functions
├── llm/
│ └── qwen_client.py # LLM client
├── rag/
│ └── system.py # RAG core logic
├── static/
│ └── styles.css # Frontend styles
├── vector_store/
│ └── manager.py # Vector database management
├── whi_dataset_desc_with_url.csv # WHI dataset description
├── whi_mesa_v2.csv # MESA dataset
└── whi_vectorstore/ # Vector index files
├── index.faiss
└── index.pkl
```
### Core Module Description

- **app.py**: Main application program, contains Shiny interface and routing logic
- **rag/system.py**: RAG system core implementation, handles retrieval and generation logic
- **llm/qwen_client.py**: Qwen model client wrapper
- **vector_store/manager.py**: FAISS vector database management and operations
- **data/processor.py**: Data preprocessing and vectorization script
- **handlers/**: UI and interaction handler modules
- **history_handlers.py**: Manages answer history tracking and navigation
- **message_handlers.py**: Handles chat message processing and user interactions
- **question_processor.py**: Processes and analyzes user questions with RAG integration
- **ui_components.py**: Renders UI components including chat interface and status indicators
- **utils.py**: Provides UI utility functions and helper components
