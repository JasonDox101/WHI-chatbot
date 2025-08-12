import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class WHIConfig:
    """WHI RAG系统配置"""
    
    # 阿里云千问配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_NAME = "qwen3-30b-a3b-instruct-2507"
    
    # 数据文件路径 - 修改为相对路径
    MESA_DATA_PATH = "./whi_mesa_v2.csv"
    DATASET_DESC_PATH = "./whi_dataset_desc_with_url.csv"
    
    # 向量数据库配置
    VECTOR_STORE_PATH = "./whi_vectorstore"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # RAG配置
    RETRIEVAL_K = 5
    SIMILARITY_THRESHOLD = 0.7
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否完整"""
        if not cls.DASHSCOPE_API_KEY:
            print(f"DASHSCOPE_API_KEY: {cls.DASHSCOPE_API_KEY}")
            print("Please check if .env file exists and contains correct API key")
            return False
        return True
