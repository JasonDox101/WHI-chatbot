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
    """Core WHI RAG system for medical data analysis and question answering."""
    
    def __init__(self):
        self.llm_client = QwenLLMClient()
        self.vector_manager = WHIVectorStoreManager()
        self.data_processor = WHIDataProcessor()
        self.workflow = None
        self.conversation_memory = []  # Conversation memory storage
        self.max_history_length = 10  # Maximum number of historical conversations to keep
        self._initialize_system()
        self._build_workflow()
    
    def _initialize_system(self) -> None:
        """Initialize the RAG system components."""
        try:
            # Load data
            self.data_processor.load_data()
            
            # Try to load existing vector store
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
    
    def process_question(self, question: str, conversation_history: List[Dict] = None, output_language: str = "english") -> Dict[str, Any]:
        """Process user question with conversation context and language support."""
        try:
            # Initialize state with conversation history and language
            initial_state = {
                "question": question,
                "conversation_history": conversation_history or [],
                "output_language": output_language,
                "processing_steps": []
            }
            
            # Run workflow
            result = self.workflow.invoke(initial_state)
            
            # Save to conversation memory
            self._save_to_memory(question, result)
            
            return result
        except Exception as e:
            # 添加详细的错误日志
            print(f"详细错误信息: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            
            return {
                "error": f"Question processing failed: {str(e)}",
                "answer": "Sorry, an error occurred while processing your question.",
                "summary_answer": "The system is temporarily unable to process your question. Please try again later.",
                "confidence_score": 0.0,
                "sources": [],
                "processing_steps": [f"Error: {str(e)}"]
            }
    
    def _save_to_memory(self, question: str, result: Dict[str, Any]):
        """Save conversation to memory."""
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
            
            # Maintain memory length limit
            if len(self.conversation_memory) > self.max_history_length:
                self.conversation_memory.pop(0)
        except Exception as e:
            print(f"Failed to save conversation memory: {str(e)}")
    
    def _build_workflow(self) -> None:
        """Build optimized LangGraph workflow with reduced LLM calls."""
        workflow = StateGraph(WHIRAGState)
        
        # Add optimized nodes - reduced from 6 to 4 nodes
        workflow.add_node("analyze_context_and_classify", self._analyze_context_and_classify)
        workflow.add_node("retrieve_documents", self._retrieve_documents)
        workflow.add_node("generate_and_summarize_answer", self._generate_and_summarize_answer)
        workflow.add_node("validate_answer", self._validate_answer)
        
        # Set optimized edges - simplified workflow
        workflow.set_entry_point("analyze_context_and_classify")
        workflow.add_edge("analyze_context_and_classify", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "generate_and_summarize_answer")
        workflow.add_edge("generate_and_summarize_answer", "validate_answer")
        workflow.add_edge("validate_answer", END)
        
        self.workflow = workflow.compile()
    
    def _analyze_context_and_classify(self, state: WHIRAGState) -> Dict[str, Any]:
        """Combined context analysis and question classification - First LLM call."""
        try:
            question = state["question"]
            history = state.get("conversation_history", [])
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting combined context analysis and question classification")
            
            # Build comprehensive prompt for both tasks
            if not history:
                context_info = "No historical conversation context available."
            else:
                context_info = f"Historical conversations:\n{self._format_history_for_analysis(history)}"
            
            combined_prompt = f"""
You are a WHI medical data analysis expert. Please perform two tasks simultaneously:

**Task 1: Context Analysis**
Analyze the relationship between the current question and historical conversations.

Current question: {question}

{context_info}

Determine:
1. Is the current question related to previous conversations?
2. Which historical Q&A pairs are relevant?
3. Generate a concise context summary

**Task 2: Question Classification**
Classify the question into one of these categories:
- "variable": Questions about specific variables, measurements, or data fields
- "dataset": Questions about datasets, studies, or data collection methods  
- "general": General questions about WHI research, methodology, or interpretation

Please return results in JSON format:
{{
    "context_analysis": {{
        "is_related": true/false,
        "context_summary": "summary text",
        "related_qa_indices": [0, 1],
        "reasoning": "detailed reasoning"
    }},
    "question_classification": {{
        "question_type": "variable/dataset/general",
        "classification_reasoning": "reasoning for classification"
    }}
}}
"""
            
            messages = [
                {"role": "system", "content": "You are a professional medical data analysis assistant, skilled at analyzing conversation context and classifying questions. Please return results strictly in JSON format."},
                {"role": "user", "content": combined_prompt}
            ]
            
            try:
                combined_result = self.llm_client.generate_response(messages)
                # Clean possible markdown format
                if "```json" in combined_result:
                    combined_result = combined_result.split("```json")[1].split("```")[0].strip()
                elif "```" in combined_result:
                    combined_result = combined_result.split("```")[1].strip()
                
                # 尝试解析JSON
                try:
                    result = json.loads(combined_result)
                    context_analysis = result.get("context_analysis", {})
                    question_classification = result.get("question_classification", {})
                except json.JSONDecodeError as json_error:
                    print(f"JSON解析失败: {json_error}")
                    print(f"尝试解析的内容: {combined_result}")
                    # 使用fallback方法
                    context_analysis = self._enhanced_context_analysis(question, history)
                    question_classification = {"question_type": "general", "classification_reasoning": "JSON解析失败，使用fallback"}
                
            except Exception as e:
                print(f"LLM调用失败: {str(e)}")
                # Fallback to enhanced analysis if LLM fails
                context_analysis = self._enhanced_context_analysis(question, history)
                question_classification = {"question_type": "general", "classification_reasoning": "LLM调用失败，使用fallback"}
            
            # Extract relevant historical Q&A
            related_qa = []
            if context_analysis.get("is_related", False):
                for idx in context_analysis.get("related_qa_indices", []):
                    if 0 <= idx < len(history):
                        related_qa.append({
                            "question": history[idx]["question"],
                            "answer": history[idx]["answer"]
                        })
            
            question_type = question_classification.get("question_type", "general")
            if question_type not in ["variable", "dataset", "general"]:
                question_type = "general"
            
            processing_steps.append("Combined context analysis and question classification completed")
            
            return {
                "context_summary": context_analysis.get("context_summary", ""),
                "related_previous_qa": related_qa,
                "is_context_related": context_analysis.get("is_related", False),
                "question_type": question_type,
                "processing_steps": processing_steps
            }
            
        except Exception as e:
            return {
                "context_summary": "Analysis failed",
                "related_previous_qa": [],
                "is_context_related": False,
                "question_type": "general",
                "error": f"Combined analysis failed: {str(e)}",
                "processing_steps": processing_steps + [f"Combined analysis failed: {str(e)}"]
            }
    
    def _enhanced_context_analysis(self, question: str, history: List[Dict]) -> Dict[str, Any]:
        """Enhanced context analysis using keyword matching and semantic similarity."""
        question_lower = question.lower()
        related_indices = []
        
        # Medical term keywords for WHI research
        medical_keywords = ['hemoglobin', 'hgb', 'blood', 'pressure', 'cholesterol', 'bmi', 'weight', 'height']
        dataset_keywords = ['mesa', 'whi', 'form', 'dataset', 'study', 'variable']
        
        for i, item in enumerate(history):
            hist_question = item.get("question", "").lower()
            hist_answer = item.get("answer", "").lower()
            
            # Keyword overlap detection
            question_words = set(question_lower.split())
            hist_words = set(hist_question.split())
            overlap = len(question_words & hist_words)
            
            # Medical term matching
            medical_overlap = any(term in question_lower and term in hist_question for term in medical_keywords)
            dataset_overlap = any(term in question_lower and term in hist_question for term in dataset_keywords)
            
            if overlap > 1 or medical_overlap or dataset_overlap:
                related_indices.append(i)
        
        return {
            "is_related": len(related_indices) > 0,
            "context_summary": f"Found {len(related_indices)} related historical conversations" if related_indices else "No related historical conversations",
            "related_qa_indices": related_indices,
            "reasoning": "Enhanced analysis based on keyword matching and medical term recognition"
        }
    
    def _retrieve_documents(self, state: WHIRAGState) -> Dict[str, Any]:
        """Document retrieval node."""
        try:
            question = state["question"]
            question_type = state.get("question_type", "general")
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting document retrieval")
            
            # Generate optimized search query
            search_query = self._generate_search_query(question, question_type)
            processing_steps.append(f"Generated search query: {search_query}")
            
            # Execute similarity search
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
                "retrieved_documents": [],
                "processing_steps": processing_steps + [f"Document retrieval failed: {str(e)}"]
            }
    
    def _generate_search_query(self, question: str, question_type: str) -> str:
        """Generate optimized search query without LLM call."""
        # Simple keyword extraction without LLM call to save resources
        import re
        
        # Extract medical terms and key phrases
        medical_terms = re.findall(r'\b(?:hemoglobin|hgb|blood|pressure|cholesterol|bmi|weight|height|mesa|whi)\b', question.lower())
        
        # Extract numbers and units
        numeric_terms = re.findall(r'\b\d+(?:\.\d+)?\s*(?:g/dL|mg/dL|mmHg|%|years)\b', question.lower())
        
        # Combine terms
        search_terms = medical_terms + numeric_terms
        
        if search_terms:
            return ' '.join(search_terms)
        else:
            return question  # Fallback to original question
    
    def _generate_and_summarize_answer(self, state: WHIRAGState) -> Dict[str, Any]:
        """Combined answer generation and summarization - Second LLM call."""
        try:
            question = state["question"]
            retrieved_docs = state.get("retrieved_documents", [])
            related_qa = state.get("related_previous_qa", [])
            context_summary = state.get("context_summary", "")
            output_language = state.get("output_language", "english")
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting combined answer generation and summarization")
            
            # Build document context
            context = self._build_context(retrieved_docs)
            
            # Build prompt with historical context
            context_info = ""
            if related_qa:
                context_info = "\n\n**Related Historical Conversations:**\n"
                for i, qa in enumerate(related_qa, 1):
                    context_info += f"{i}. Q: {qa['question']}\n   A: {qa['answer']}\n\n"
            
            if context_summary and context_summary != "No historical conversation context":
                context_info += f"\n**Conversation Context Summary:**\n{context_summary}\n\n"
            
            # Language-specific instructions
            if output_language == "chinese":
                language_instruction = "请用中文回答。确保所有回答内容都使用中文，包括医学术语的中文表达。"
                system_content = "你是一位专业的WHI医学数据分析助手，能够结合历史对话上下文提供准确答案。请严格遵循markdown格式要求，同时保持专业的回答风格。请用中文回答所有问题。"
            else:
                language_instruction = "Please respond in English. Ensure all content is in English, including medical terminology."
                system_content = "You are a professional medical data analysis assistant who can provide accurate answers by combining historical conversation context. Please strictly follow markdown format requirements while maintaining a professional answering style. Please respond in English."
            
            # 在_generate_and_summarize_answer方法中，将combined_prompt修改为：
            combined_prompt = f"""
            {language_instruction}
            
            You are a professional WHI medical data analysis assistant. Please provide BOTH a comprehensive detailed answer and a concise summary.
            
            User's current question: {question}
            
            Document context:
            {context}
            {context_info}
            
            **Please provide your response in the following JSON format:**
            {{
                "detailed_answer": "Your comprehensive, professional answer with markdown formatting...",
                "summary_answer": "A concise summary for chat display..."
            }}
            
            **CRITICAL: For detailed_answer, provide COMPREHENSIVE and THOROUGH analysis:**
            1. **No Length Restrictions**: Provide as much detail as necessary to fully address the question
            2. **Complete Coverage**: Include all relevant background information, methodology, and statistical details
            3. **Rich Context**: Provide comprehensive medical and research context
            4. **Detailed Data**: Include specific numbers, percentages, research findings, and comparative analysis
            5. **Clinical Implications**: Thoroughly discuss clinical significance and practical applications
            6. **Structured Organization**: Use clear headings, subheadings, and well-organized sections
            7. **Comprehensive Analysis**: Cover all aspects of the question with in-depth explanations
            
            **For summary_answer (separate from detailed answer):**
            1. Keep concise (3-4 sentences, 200-300 words)
            2. Extract only the most critical findings
            3. Suitable for quick chat display
            
            **Formatting requirements for detailed_answer:**
            - Use ## for main titles, ### for subtitles
            - Use - for lists, **bold** for emphasis
            - Include specific data points and statistical values
            - Provide comprehensive background and context
            - Maintain professional medical terminology
            - Add detailed explanations and interpretations
            
            IMPORTANT: The detailed_answer should be as comprehensive and thorough as possible, with NO length limitations. Provide complete, in-depth analysis that fully addresses all aspects of the question.
            """
            
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": combined_prompt}
            ]
            
            combined_response = self.llm_client.generate_response(messages)
            
            try:
                # Clean possible markdown format
                if "```json" in combined_response:
                    combined_response = combined_response.split("```json")[1].split("```")[0].strip()
                elif "```" in combined_response:
                    combined_response = combined_response.split("```")[1].strip()
                
                response_data = json.loads(combined_response)
                detailed_answer = response_data.get("detailed_answer", "")
                summary_answer = response_data.get("summary_answer", "")
                
            except Exception as e:
                # Fallback: split the response manually if JSON parsing fails
                lines = combined_response.split('\n')
                detailed_answer = combined_response
                summary_answer = ' '.join(lines[:3]) if len(lines) >= 3 else combined_response[:200]
            
            # Apply markdown format standardization to detailed answer
            detailed_answer = self._ensure_markdown_format(detailed_answer)
            
            # Extract source information
            sources = self._extract_sources(retrieved_docs)
            
            processing_steps.append("Combined answer generation and summarization completed")
            
            return {
                "context": context,
                "answer": detailed_answer,
                "summary_answer": summary_answer,
                "sources": sources,
                "processing_steps": processing_steps
            }
            
        except Exception as e:
            return {
                "error": f"Combined answer generation failed: {str(e)}",
                "answer": "Sorry, an error occurred while generating the answer.",
                "summary_answer": "Unable to process your question at this time.",
                "processing_steps": processing_steps + [f"Combined answer generation failed: {str(e)}"]
            }
    
    def _build_context(self, documents: List) -> str:
        """Build context string from retrieved documents."""
        if not documents:
            return "No relevant information found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"Information {i}:\n{doc.page_content}\n")
        
        return "\n".join(context_parts)
    
    def _extract_sources(self, documents: List) -> List[Dict[str, Any]]:
        """Extract source information from documents."""
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
        """Answer validation node."""
        try:
            answer = state.get("answer", "")
            sources = state.get("sources", [])
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting answer validation")
            
            # Simple confidence assessment
            confidence_score = self._calculate_confidence(answer, sources)
            
            processing_steps.append(f"Answer validation completed, confidence: {confidence_score:.2f}")
            
            return {
                "confidence_score": confidence_score,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "confidence_score": 0.0,
                "error": f"Answer validation failed: {str(e)}",
                "processing_steps": processing_steps + [f"Answer validation failed: {str(e)}"]
            }
    
    def _calculate_confidence(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on answer quality and source availability."""
        if not answer or not sources:
            return 0.0
        
        # Simple confidence calculation based on answer length and source count
        answer_length_score = min(len(answer) / 500, 1.0)  # Normalize to 0-1
        source_count_score = min(len(sources) / 5, 1.0)    # Normalize to 0-1
        
        # Composite score
        confidence = (answer_length_score * 0.6 + source_count_score * 0.4)
        return round(confidence, 2)
    
    def _format_history_for_analysis(self, history: List[Dict]) -> str:
        """Format conversation history for analysis."""
        formatted = ""
        for i, item in enumerate(history[-5:], 1):  # Only take the last 5 entries
            formatted += f"{i}. Q: {item.get('question', '')}\n   A: {item.get('answer', '')}\n\n"
        return formatted
    
    def _ensure_markdown_format(self, answer: str) -> str:
        """Ensure answer follows standard markdown format without changing content."""
        import re
        
        # Standardize title format
        answer = re.sub(r'^#{1,6}\s*(.+)$', lambda m: f"## {m.group(1).strip()}", answer, flags=re.MULTILINE)
        
        # Standardize list format
        answer = re.sub(r'^[•·*]\s*', '- ', answer, flags=re.MULTILINE)
        
        # Ensure paragraph spacing
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        
        # Ensure numerical values are bolded (if not already)
        answer = re.sub(r'(?<!\*)\b(\d+(?:\.\d+)?\s*(?:g/dL|mg/dL|mmHg|%|years|cases|people|items))(?!\*)', r'**\1**', answer)
        
        return answer.strip()