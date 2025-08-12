from typing import TypedDict, List, Optional, Dict, Any
from langchain.schema import Document

class WHIRAGState(TypedDict):
    """WHI RAG系统状态"""
    # 用户输入
    question: str
    
    # 新增：对话历史上下文
    conversation_history: Optional[List[Dict[str, Any]]]  # 历史对话记录
    context_summary: Optional[str]  # 上下文总结
    related_previous_qa: Optional[List[Dict[str, str]]]  # 相关的历史问答
    
    # 问题分类
    question_type: Optional[str]  # "variable", "dataset", "general"
    
    # 检索相关
    search_query: Optional[str]
    retrieved_documents: Optional[List[Document]]
    
    # 生成相关
    context: Optional[str]
    answer: Optional[str]
    summary_answer: Optional[str]  # 新增：总结答案
    
    # 验证相关
    confidence_score: Optional[float]
    sources: Optional[List[Dict[str, Any]]]
    
    # 处理步骤
    processing_steps: Optional[List[str]]
    
    # 错误处理
    error: Optional[str]