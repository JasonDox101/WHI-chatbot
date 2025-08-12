from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from graph.state import WHIRAGState
from llm.qwen_client import QwenLLMClient
from vector_store.manager import WHIVectorStoreManager
from data.processor import WHIDataProcessor
from config.settings import WHIConfig
import json
import re

class WHIRAGSystem:
    """WHI RAG系统核心类"""
    
    def __init__(self):
        self.llm_client = QwenLLMClient()
        self.vector_manager = WHIVectorStoreManager()
        self.data_processor = WHIDataProcessor()
        self.workflow = None
        self._initialize_system()
        self._build_workflow()
    
    def _initialize_system(self) -> None:
        """初始化系统"""
        try:
            # 加载数据
            self.data_processor.load_data()
            
            # 尝试加载已存在的向量存储
            if not self.vector_manager.load_vector_store():
                print("Creating new vector store...")
                documents = self.data_processor.create_documents()
                self.vector_manager.create_vector_store(documents)
                print("Vector store creation completed")
            else:
                print("Vector store loaded successfully")
        except Exception as e:
            print(f"System initialization failed: {str(e)}")
            raise
    
    # 在_build_workflow方法中添加总结节点
    def _build_workflow(self) -> None:
        """构建LangGraph工作流"""
        workflow = StateGraph(WHIRAGState)
        
        # 添加节点
        workflow.add_node("classify_question", self._classify_question)
        workflow.add_node("retrieve_documents", self._retrieve_documents)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("summarize_answer", self._summarize_answer)  # 新增总结节点
        workflow.add_node("validate_answer", self._validate_answer)
        
        # 设置边
        workflow.set_entry_point("classify_question")
        workflow.add_edge("classify_question", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "generate_answer")
        workflow.add_edge("generate_answer", "summarize_answer")  # 新增边
        workflow.add_edge("summarize_answer", "validate_answer")   # 修改边
        workflow.add_edge("validate_answer", END)
        
        self.workflow = workflow.compile()
    
    # 添加答案总结方法
    def _summarize_answer(self, state: WHIRAGState) -> Dict[str, Any]:
        """答案总结节点 - 第二个LLM调用"""
        try:
            detailed_answer = state.get("answer", "")
            question = state["question"]
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("开始答案总结")
            
            if not detailed_answer:
                return {
                    "summary_answer": "无法生成答案总结",
                    "processing_steps": processing_steps + ["详细答案为空，无法总结"]
                }
            
            # 总结prompt
            summary_prompt = f"""
你是一个专业的医学数据分析助手。请将以下详细答案总结为简洁、易懂的回复，适合在聊天界面中显示。

用户问题：{question}

详细答案：
{detailed_answer}

请提供：
1. 核心要点的简洁总结（2-3句话）
2. 关键信息的提炼
3. 保持专业性但易于理解

总结应该简洁明了，长度控制在100-200字以内。
"""
            
            messages = [
                {"role": "system", "content": "你是一个专业的医学数据分析助手，擅长将复杂的医学信息总结为简洁易懂的内容。"},
                {"role": "user", "content": summary_prompt}
            ]
            
            summary_answer = self.llm_client.generate_response(messages)
            
            processing_steps.append("答案总结完成")
            
            return {
                "summary_answer": summary_answer,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "summary_answer": "答案总结失败",
                "error": f"答案总结失败: {str(e)}",
                "processing_steps": processing_steps + [f"答案总结失败: {str(e)}"]
            }
    
    def _classify_question(self, state: WHIRAGState) -> Dict[str, Any]:
        """问题分类节点"""
        try:
            question = state["question"]
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting question classification")
            
            # 使用LLM进行问题分类
            classification_prompt = f"""
You are a professional medical data analysis assistant. Please analyze the following user question and classify it into one of the following three types:

1. "variable" - Questions about specific variables, indicators, or measurements
2. "dataset" - Questions about datasets, studies, or databases
3. "general" - General questions or questions requiring comprehensive information

User question: {question}

Please return only the classification result (variable/dataset/general), without any other content.
"""
            
            messages = [
                {"role": "system", "content": "You are a professional medical data analysis assistant."},
                {"role": "user", "content": classification_prompt}
            ]
            
            question_type = self.llm_client.generate_response(messages).strip().lower()
            
            # 确保分类结果有效
            if question_type not in ["variable", "dataset", "general"]:
                question_type = "general"
            
            processing_steps.append(f"Question classification completed: {question_type}")
            
            return {
                "question_type": question_type,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "error": f"Question classification failed: {str(e)}",
                "processing_steps": processing_steps + [f"Question classification failed: {str(e)}"]
            }
    
    def _retrieve_documents(self, state: WHIRAGState) -> Dict[str, Any]:
        """文档检索节点"""
        try:
            question = state["question"]
            question_type = state.get("question_type", "general")
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting document retrieval")
            
            # 生成优化的搜索查询
            search_query = self._generate_search_query(question, question_type)
            processing_steps.append(f"Generated search query: {search_query}")
            
            # 执行相似性搜索
            retrieved_docs = self.vector_manager.similarity_search(
                search_query, 
                k=WHIConfig.RETRIEVAL_K
            )
            
            processing_steps.append(f"Retrieved {len(retrieved_docs)} relevant documents")
            
            return {
                "search_query": search_query,
                "retrieved_documents": retrieved_docs,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "error": f"Document retrieval failed: {str(e)}",
                "processing_steps": processing_steps + [f"Document retrieval failed: {str(e)}"]
            }
    
    def _generate_search_query(self, question: str, question_type: str) -> str:
        """生成优化的搜索查询"""
        try:
            query_prompt = f"""
Based on question type "{question_type}" and user question, generate keyword queries suitable for retrieval in WHI medical data.

User question: {question}

Please extract key medical terms, variable names, or dataset names to generate concise search queries.
Return only the search query, without any other content.
"""
            
            messages = [
                {"role": "system", "content": "You are a professional medical research assistant."},
                {"role": "user", "content": query_prompt}
            ]
            
            return self.llm_client.generate_response(messages).strip()
        except:
            # 如果生成失败，返回原始问题
            return question
    
    def _generate_answer(self, state: WHIRAGState) -> Dict[str, Any]:
        """答案生成节点"""
        try:
            question = state["question"]
            retrieved_docs = state.get("retrieved_documents", [])
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting answer generation")
            
            # 构建上下文
            context = self._build_context(retrieved_docs)
            
            # 生成答案
            answer_prompt = f"""
You are a professional WHI (Women's Health Initiative) medical data analysis expert. Based on the provided context information, please answer the user's question.

Context information:
{context}

User question: {question}

Please provide detailed and accurate answers, including:
1. Direct answer to the user's question
2. Relevant variable or dataset information
3. If applicable, provide data interpretation or usage suggestions

If the context information is insufficient to fully answer the question, please indicate this and provide possible suggestions.
"""
            
            messages = [
                {"role": "system", "content": "You are a professional WHI medical data analysis expert."},
                {"role": "user", "content": answer_prompt}
            ]
            
            answer = self.llm_client.generate_response(messages)
            
            # 提取源信息
            sources = self._extract_sources(retrieved_docs)
            
            processing_steps.append("Answer generation completed")
            
            return {
                "context": context,
                "answer": answer,
                "sources": sources,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "error": f"Answer generation failed: {str(e)}",
                "processing_steps": processing_steps + [f"Answer generation failed: {str(e)}"]
            }
    
    def _build_context(self, documents: List) -> str:
        """构建上下文字符串"""
        if not documents:
            return "No relevant information found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"Information {i}:\n{doc.page_content}\n")
        
        return "\n".join(context_parts)
    
    def _extract_sources(self, documents: List) -> List[Dict[str, Any]]:
        """提取源信息"""
        sources = []
        for doc in documents:
            source_info = {
                "type": doc.metadata.get("type", "unknown"),
                "dataset_name": doc.metadata.get("dataset_name", "N/A"),
                "variable_name": doc.metadata.get("variable_name", "N/A"),
                "study": doc.metadata.get("study", "N/A")
            }
            sources.append(source_info)
        return sources
    
    def _validate_answer(self, state: WHIRAGState) -> Dict[str, Any]:
        """答案验证节点"""
        try:
            answer = state.get("answer", "")
            sources = state.get("sources", [])
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting answer validation")
            
            # 简单的置信度评估
            confidence_score = self._calculate_confidence(answer, sources)
            
            processing_steps.append(f"Answer validation completed, confidence: {confidence_score:.2f}")
            
            return {
                "confidence_score": confidence_score,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "error": f"Answer validation failed: {str(e)}",
                "processing_steps": processing_steps + [f"Answer validation failed: {str(e)}"]
            }
    
    def _calculate_confidence(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """计算置信度分数"""
        if not answer or not sources:
            return 0.0
        
        # 基于答案长度和源数量的简单置信度计算
        answer_length_score = min(len(answer) / 500, 1.0)  # 标准化到0-1
        source_count_score = min(len(sources) / 5, 1.0)    # 标准化到0-1
        
        # 综合评分
        confidence = (answer_length_score * 0.6 + source_count_score * 0.4)
        return round(confidence, 2)
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """处理用户问题的主入口"""
        try:
            initial_state = {
                "question": question,
                "processing_steps": []
            }
            
            # 执行工作流
            result = self.workflow.invoke(initial_state)
            
            return result
        except Exception as e:
            return {
                "error": f"Question processing failed: {str(e)}",
                "question": question,
                "processing_steps": [f"System error: {str(e)}"]
            }