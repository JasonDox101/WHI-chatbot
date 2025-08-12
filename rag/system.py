from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from graph.state import WHIRAGState
from llm.qwen_client import QwenLLMClient
from vector_store.manager import WHIVectorStoreManager
from data.processor import WHIDataProcessor
from config.settings import WHIConfig
import json
import re
from datetime import datetime

class WHIRAGSystem:
    """WHI RAG系统核心类"""
    
    def __init__(self):
        self.llm_client = QwenLLMClient()
        self.vector_manager = WHIVectorStoreManager()
        self.data_processor = WHIDataProcessor()
        self.workflow = None
        self.conversation_memory = []  # 对话记忆存储
        self.max_history_length = 10  # 最大保存历史对话数量
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
    
    def process_question(self, question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """处理问题，支持对话上下文"""
        try:
            # 初始化状态，包含对话历史
            initial_state = {
                "question": question,
                "conversation_history": conversation_history or [],
                "processing_steps": []
            }
            
            # 运行工作流
            result = self.workflow.invoke(initial_state)
            
            # 保存到对话记忆
            self._save_to_memory(question, result)
            
            return result
        except Exception as e:
            return {
                "error": f"问题处理失败: {str(e)}",
                "answer": "抱歉，处理您的问题时出现了错误。",
                "summary_answer": "系统暂时无法处理您的问题，请稍后重试。",
                "confidence_score": 0.0,
                "sources": [],
                "processing_steps": [f"错误: {str(e)}"]
            }
    
    def _save_to_memory(self, question: str, result: Dict[str, Any]):
        """保存对话到记忆中"""
        try:
            qa_pair = {
                "question": question,
                "answer": result.get("summary_answer", ""),
                "detailed_answer": result.get("answer", ""),
                "timestamp": datetime.now().isoformat(),
                "confidence": result.get("confidence_score", 0),
                "question_type": result.get("question_type", "general")
            }
            
            self.conversation_memory.append(qa_pair)
            
            # 保持记忆长度限制
            if len(self.conversation_memory) > self.max_history_length:
                self.conversation_memory.pop(0)
        except Exception as e:
            print(f"保存对话记忆失败: {str(e)}")
    
    def _build_workflow(self) -> None:
        """构建增强的LangGraph工作流"""
        workflow = StateGraph(WHIRAGState)
        
        # 添加节点
        workflow.add_node("analyze_context", self._analyze_context)
        workflow.add_node("classify_question", self._classify_question)
        workflow.add_node("retrieve_documents", self._retrieve_documents)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("summarize_answer", self._summarize_answer)
        workflow.add_node("validate_answer", self._validate_answer)
        
        # 设置边 - 新的流程
        workflow.set_entry_point("analyze_context")
        workflow.add_edge("analyze_context", "classify_question")
        workflow.add_edge("classify_question", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "generate_answer")
        workflow.add_edge("generate_answer", "summarize_answer")
        workflow.add_edge("summarize_answer", "validate_answer")
        workflow.add_edge("validate_answer", END)
        
        self.workflow = workflow.compile()
    
    def _analyze_context(self, state: WHIRAGState) -> Dict[str, Any]:
        """分析对话上下文的节点"""
        try:
            question = state["question"]
            history = state.get("conversation_history", [])
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("开始上下文分析")
            
            
            if not history:
                return {
                    "context_summary": "无历史对话上下文",
                    "related_previous_qa": [],
                    "is_context_related": False,
                    "processing_steps": processing_steps
                }
            
            # 改进的上下文分析提示
            context_prompt = f"""
你是WHI医学数据分析专家。请仔细分析当前问题与历史对话的关联性。

当前问题：{question}

历史对话：
{self._format_history_for_analysis(history)}

分析要求：
1. 检查当前问题是否引用了之前提到的概念、数值、变量名等
2. 判断是否需要结合之前的答案来回答当前问题
3. 识别相关的历史问答对
4. 生成简洁的上下文总结

请返回JSON格式（确保格式正确）：
{{
    "is_related": true,
    "context_summary": "简洁的上下文总结",
    "related_qa_indices": [0, 1],
    "reasoning": "详细的关联性分析原因"
}}
"""
            
            messages = [
                {"role": "system", "content": "你是专业的医学数据分析助手，擅长分析对话上下文关联性。请严格按照JSON格式返回结果。"},
                {"role": "user", "content": context_prompt}
            ]
            
            try:
                analysis_result = self.llm_client.generate_response(messages)
                # print(f"LLM上下文分析结果: {analysis_result}")  # 移除此行
                
                # 清理可能的markdown格式
                if "```json" in analysis_result:
                    analysis_result = analysis_result.split("```json")[1].split("```")[0].strip()
                elif "```" in analysis_result:
                    analysis_result = analysis_result.split("```")[1].strip()
                
                analysis = json.loads(analysis_result)
            except Exception as e:
                # print(f"LLM分析失败，使用简单匹配: {e}")  # 移除此行
                # 如果LLM分析失败，使用改进的关键词匹配
                analysis = self._enhanced_context_analysis(question, history)
            
            # 提取相关的历史问答
            related_qa = []
            if analysis.get("is_related", False):
                for idx in analysis.get("related_qa_indices", []):
                    if 0 <= idx < len(history):
                        related_qa.append({
                            "question": history[idx]["question"],
                            "answer": history[idx]["answer"]
                        })
            
            processing_steps.append("上下文分析完成")
            
            return {
                "context_summary": analysis.get("context_summary", ""),
                "related_previous_qa": related_qa,
                "is_context_related": analysis.get("is_related", False),
                "processing_steps": processing_steps
            }
            
        except Exception as e:
            return {
                "context_summary": "上下文分析失败",
                "related_previous_qa": [],
                "is_context_related": False,
                "error": f"上下文分析失败: {str(e)}",
                "processing_steps": processing_steps + [f"上下文分析失败: {str(e)}"]
            }
    
    def _simple_context_analysis(self, question: str, history: List[Dict]) -> Dict[str, Any]:
        """简单的上下文分析（关键词匹配）"""
        question_lower = question.lower()
        related_indices = []
        
        for i, item in enumerate(history):
            hist_question = item.get("question", "").lower()
            # 简单的关键词重叠检测
            question_words = set(question_lower.split())
            hist_words = set(hist_question.split())
            overlap = len(question_words & hist_words)
            
            if overlap > 1:  # 如果有超过1个词重叠
                related_indices.append(i)
        
        return {
            "is_related": len(related_indices) > 0,
            "context_summary": f"发现{len(related_indices)}个相关历史对话" if related_indices else "无相关历史对话",
            "related_qa_indices": related_indices,
            "reasoning": "基于关键词匹配的简单分析"
        }
    
    def _classify_question(self, state: WHIRAGState) -> Dict[str, Any]:
        """问题分类节点"""
        try:
            question = state["question"]
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("开始问题分类")
            
            classification_prompt = f"""
Please classify the following question about WHI (Women's Health Initiative) data:

Question: {question}

Classify into one of these categories:
- "variable": Questions about specific variables, measurements, or data fields
- "dataset": Questions about datasets, studies, or data collection methods
- "general": General questions about WHI research, methodology, or interpretation

Return only the category name.
"""
            
            messages = [
                {"role": "system", "content": "You are a professional medical data analysis assistant."},
                {"role": "user", "content": classification_prompt}
            ]
            
            question_type = self.llm_client.generate_response(messages).strip().lower()
            
            # 确保分类结果有效
            if question_type not in ["variable", "dataset", "general"]:
                question_type = "general"
            
            processing_steps.append(f"问题分类完成: {question_type}")
            
            return {
                "question_type": question_type,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "question_type": "general",
                "error": f"问题分类失败: {str(e)}",
                "processing_steps": processing_steps + [f"问题分类失败: {str(e)}"]
            }
    
    def _retrieve_documents(self, state: WHIRAGState) -> Dict[str, Any]:
        """文档检索节点"""
        try:
            question = state["question"]
            question_type = state.get("question_type", "general")
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("开始文档检索")
            
            # 生成优化的搜索查询
            search_query = self._generate_search_query(question, question_type)
            processing_steps.append(f"生成搜索查询: {search_query}")
            
            # 执行相似性搜索
            retrieved_docs = self.vector_manager.similarity_search(
                search_query, 
                k=WHIConfig.RETRIEVAL_K
            )
            
            processing_steps.append(f"检索到 {len(retrieved_docs)} 个相关文档")
            
            return {
                "search_query": search_query,
                "retrieved_documents": retrieved_docs,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "error": f"文档检索失败: {str(e)}",
                "retrieved_documents": [],
                "processing_steps": processing_steps + [f"文档检索失败: {str(e)}"]
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
        """增强的答案生成节点 - 支持上下文"""
        try:
            question = state["question"]
            retrieved_docs = state.get("retrieved_documents", [])
            related_qa = state.get("related_previous_qa", [])
            context_summary = state.get("context_summary", "")
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("开始上下文感知答案生成")
            
            # 构建文档上下文
            context = self._build_context(retrieved_docs)
            
            # 构建包含历史上下文的prompt
            context_info = ""
            if related_qa:
                context_info = "\n\n**相关历史对话：**\n"
                for i, qa in enumerate(related_qa, 1):
                    context_info += f"{i}. Q: {qa['question']}\n   A: {qa['answer']}\n\n"
            
            if context_summary and context_summary != "无历史对话上下文":
                context_info += f"\n**对话上下文总结：**\n{context_summary}\n\n"
            
            # 🔧 修改prompt，只约束格式，保持内容风格
            enhanced_prompt = f"""
你是专业的WHI医学数据分析助手。请基于提供的文档上下文和对话历史回答用户问题。

用户当前问题：{question}

文档上下文：
{context}
{context_info}

**重要：请严格按照以下markdown格式要求输出，但保持你原有的专业回答风格和内容深度：**

1. **标题格式**：使用 ## 作为主标题，### 作为子标题
2. **列表格式**：使用 - 开头的无序列表，或 1. 开头的有序列表
3. **强调格式**：重要信息用 **粗体** 标记
4. **数值格式**：具体数值和单位用 **粗体** 突出显示
5. **段落格式**：段落之间用空行分隔

请保持你一贯的：
- 准确、专业的医学术语使用
- 准确、专业的答案
- 如果与历史对话相关，请适当引用和关联
- 详细的数据分析和解释
- 客观的学术语调
- 丰富的背景信息提供
- 包含具体的数据和指标

注意：如果当前问题与之前的问题相关，请在答案中体现这种关联性。

确保输出格式标准化。
"""
            
            messages = [
                {"role": "system", "content": "你是专业的医学数据分析助手，能够结合历史对话上下文提供准确答案。请严格遵循markdown格式要求，但保持专业的回答风格。"},
                {"role": "user", "content": enhanced_prompt}
            ]
            
            answer = self.llm_client.generate_response(messages)
            
            # 🔧 应用markdown格式标准化
            answer = self._ensure_markdown_format(answer)
            
            # 提取源信息
            sources = self._extract_sources(retrieved_docs)
            
            processing_steps.append("上下文感知答案生成完成")
            
            return {
                "context": context,
                "answer": answer,
                "sources": sources,
                "processing_steps": processing_steps
            }
            
        except Exception as e:
            return {
                "error": f"答案生成失败: {str(e)}",
                "answer": "抱歉，生成答案时出现错误。",
                "processing_steps": processing_steps + [f"答案生成失败: {str(e)}"]
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
    
    def _validate_answer(self, state: WHIRAGState) -> Dict[str, Any]:
        """答案验证节点"""
        try:
            answer = state.get("answer", "")
            sources = state.get("sources", [])
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("开始答案验证")
            
            # 简单的置信度评估
            confidence_score = self._calculate_confidence(answer, sources)
            
            processing_steps.append(f"答案验证完成，置信度: {confidence_score:.2f}")
            
            return {
                "confidence_score": confidence_score,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "confidence_score": 0.0,
                "error": f"答案验证失败: {str(e)}",
                "processing_steps": processing_steps + [f"答案验证失败: {str(e)}"]
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
    
    def _format_history_for_analysis(self, history: List[Dict]) -> str:
        """格式化历史对话用于分析"""
        formatted = ""
        for i, item in enumerate(history[-5:], 1):  # 只取最近5条
            formatted += f"{i}. Q: {item.get('question', '')}\n   A: {item.get('answer', '')}\n\n"
        return formatted


    def _ensure_markdown_format(self, answer: str) -> str:
        """确保答案符合标准markdown格式，但不改变内容"""
        import re
        
        # 确保标题格式标准化
        answer = re.sub(r'^#{1,6}\s*(.+)$', lambda m: f"## {m.group(1).strip()}", answer, flags=re.MULTILINE)
        
        # 确保列表格式标准化
        answer = re.sub(r'^[•·*]\s*', '- ', answer, flags=re.MULTILINE)
        
        # 确保段落间距
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        
        # 确保数值加粗（如果没有的话）
        answer = re.sub(r'(?<!\*)\b(\d+(?:\.\d+)?\s*(?:g/dL|mg/dL|mmHg|%|年|岁|例|人|项))(?!\*)', r'**\1**', answer)
        
        return answer.strip()