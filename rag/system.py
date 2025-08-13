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
    
    def process_question(self, question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Process user question with conversation context support."""
        try:
            # Initialize state with conversation history
            initial_state = {
                "question": question,
                "conversation_history": conversation_history or [],
                "processing_steps": []
            }
            
            # Run workflow
            result = self.workflow.invoke(initial_state)
            
            # Save to conversation memory
            self._save_to_memory(question, result)
            
            return result
        except Exception as e:
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
        """Build enhanced LangGraph workflow."""
        workflow = StateGraph(WHIRAGState)
        
        # Add nodes
        workflow.add_node("analyze_context", self._analyze_context)
        workflow.add_node("classify_question", self._classify_question)
        workflow.add_node("retrieve_documents", self._retrieve_documents)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("summarize_answer", self._summarize_answer)
        workflow.add_node("validate_answer", self._validate_answer)
        
        # Set edges - new workflow
        workflow.set_entry_point("analyze_context")
        workflow.add_edge("analyze_context", "classify_question")
        workflow.add_edge("classify_question", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "generate_answer")
        workflow.add_edge("generate_answer", "summarize_answer")
        workflow.add_edge("summarize_answer", "validate_answer")
        workflow.add_edge("validate_answer", END)
        
        self.workflow = workflow.compile()
    
    def _analyze_context(self, state: WHIRAGState) -> Dict[str, Any]:
        """Analyze conversation context node."""
        try:
            question = state["question"]
            history = state.get("conversation_history", [])
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting context analysis")
            
            if not history:
                return {
                    "context_summary": "No historical conversation context",
                    "related_previous_qa": [],
                    "is_context_related": False,
                    "processing_steps": processing_steps
                }
            
            # Enhanced context analysis prompt
            context_prompt = f"""
You are a WHI medical data analysis expert. Please carefully analyze the relationship between the current question and historical conversations.

Current question: {question}

Historical conversations:
{self._format_history_for_analysis(history)}

Analysis requirements:
1. Check if the current question references concepts, values, variable names mentioned previously
2. Determine if previous answers are needed to answer the current question
3. Identify relevant historical Q&A pairs
4. Generate a concise context summary

Please return in JSON format (ensure correct format):
{{
    "is_related": true,
    "context_summary": "Concise context summary",
    "related_qa_indices": [0, 1],
    "reasoning": "Detailed reasoning for relationship analysis"
}}
"""
            
            messages = [
                {"role": "system", "content": "You are a professional medical data analysis assistant, skilled at analyzing conversation context relationships. Please return results strictly in JSON format."},
                {"role": "user", "content": context_prompt}
            ]
            
            try:
                analysis_result = self.llm_client.generate_response(messages)
                
                # Clean possible markdown format
                if "```json" in analysis_result:
                    analysis_result = analysis_result.split("```json")[1].split("```")[0].strip()
                elif "```" in analysis_result:
                    analysis_result = analysis_result.split("```")[1].strip()
                
                analysis = json.loads(analysis_result)
            except Exception as e:
                # If LLM analysis fails, use enhanced keyword matching
                analysis = self._enhanced_context_analysis(question, history)
            
            # Extract relevant historical Q&A
            related_qa = []
            if analysis.get("is_related", False):
                for idx in analysis.get("related_qa_indices", []):
                    if 0 <= idx < len(history):
                        related_qa.append({
                            "question": history[idx]["question"],
                            "answer": history[idx]["answer"]
                        })
            
            processing_steps.append("Context analysis completed")
            
            return {
                "context_summary": analysis.get("context_summary", ""),
                "related_previous_qa": related_qa,
                "is_context_related": analysis.get("is_related", False),
                "processing_steps": processing_steps
            }
            
        except Exception as e:
            return {
                "context_summary": "Context analysis failed",
                "related_previous_qa": [],
                "is_context_related": False,
                "error": f"Context analysis failed: {str(e)}",
                "processing_steps": processing_steps + [f"Context analysis failed: {str(e)}"]
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
    
    def _classify_question(self, state: WHIRAGState) -> Dict[str, Any]:
        """Question classification node."""
        try:
            question = state["question"]
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting question classification")
            
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
            
            # Ensure classification result is valid
            if question_type not in ["variable", "dataset", "general"]:
                question_type = "general"
            
            processing_steps.append(f"Question classification completed: {question_type}")
            
            return {
                "question_type": question_type,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "question_type": "general",
                "error": f"Question classification failed: {str(e)}",
                "processing_steps": processing_steps + [f"Question classification failed: {str(e)}"]
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
        """Generate optimized search query."""
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
            # If generation fails, return original question
            return question
    
    def _generate_answer(self, state: WHIRAGState) -> Dict[str, Any]:
        """Enhanced answer generation node with context support."""
        try:
            question = state["question"]
            retrieved_docs = state.get("retrieved_documents", [])
            related_qa = state.get("related_previous_qa", [])
            context_summary = state.get("context_summary", "")
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting context-aware answer generation")
            
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
            
            # Modified prompt to constrain format while maintaining content style
            enhanced_prompt = f"""
You are a professional WHI medical data analysis assistant. Please answer the user's question based on the provided document context and conversation history.

User's current question: {question}

Document context:
{context}
{context_info}

**Important: Please strictly follow the markdown format requirements below, while maintaining your professional answering style and content depth:**

1. **Title format**: Use ## for main titles, ### for subtitles
2. **List format**: Use - for unordered lists, or 1. for ordered lists
3. **Emphasis format**: Mark important information with **bold**
4. **Numerical format**: Highlight specific values and units with **bold**
5. **Paragraph format**: Separate paragraphs with blank lines

Please maintain your consistent:
- Accurate, professional medical terminology usage
- Accurate, professional answers
- If related to previous questions, please reflect this relationship in the answer
- Detailed data analysis and interpretation
- Objective academic tone
- Rich background information provision
- Include specific data and indicators

Note: If the current question is related to previous questions, please reflect this relationship in your answer.

Ensure standardized output format.
"""
            
            messages = [
                {"role": "system", "content": "You are a professional medical data analysis assistant who can provide accurate answers by combining historical conversation context. Please strictly follow markdown format requirements while maintaining a professional answering style."},
                {"role": "user", "content": enhanced_prompt}
            ]
            
            answer = self.llm_client.generate_response(messages)
            
            # Apply markdown format standardization
            answer = self._ensure_markdown_format(answer)
            
            # Extract source information
            sources = self._extract_sources(retrieved_docs)
            
            processing_steps.append("Context-aware answer generation completed")
            
            return {
                "context": context,
                "answer": answer,
                "sources": sources,
                "processing_steps": processing_steps
            }
            
        except Exception as e:
            return {
                "error": f"Answer generation failed: {str(e)}",
                "answer": "Sorry, an error occurred while generating the answer.",
                "processing_steps": processing_steps + [f"Answer generation failed: {str(e)}"]
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
    
    def _summarize_answer(self, state: WHIRAGState) -> Dict[str, Any]:
        """Answer summarization node - second LLM call."""
        try:
            detailed_answer = state.get("answer", "")
            question = state["question"]
            processing_steps = state.get("processing_steps", [])
            processing_steps.append("Starting answer summarization")
            
            if not detailed_answer:
                return {
                    "summary_answer": "Unable to generate answer summary",
                    "processing_steps": processing_steps + ["Detailed answer is empty, cannot summarize"]
                }
            
            # Summary prompt
            summary_prompt = f"""
You are a professional medical data analysis assistant. Please summarize the following detailed answer into a concise, easy-to-understand reply suitable for display in a chat interface.

User question: {question}

Detailed answer:
{detailed_answer}

Please provide:
1. Concise summary of core points (2-3 sentences)
2. Extraction of key information
3. Maintain professionalism but keep it understandable

The summary should be concise and clear, with length controlled within 100-200 words.
"""
            
            messages = [
                {"role": "system", "content": "You are a professional medical data analysis assistant, skilled at summarizing complex medical information into concise and understandable content."},
                {"role": "user", "content": summary_prompt}
            ]
            
            summary_answer = self.llm_client.generate_response(messages)
            
            processing_steps.append("Answer summarization completed")
            
            return {
                "summary_answer": summary_answer,
                "processing_steps": processing_steps
            }
        except Exception as e:
            return {
                "summary_answer": "Answer summarization failed",
                "error": f"Answer summarization failed: {str(e)}",
                "processing_steps": processing_steps + [f"Answer summarization failed: {str(e)}"]
            }
    
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