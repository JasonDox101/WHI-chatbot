from typing import TypedDict, List, Optional, Dict, Any
from langchain.schema import Document

class WHIRAGState(TypedDict):
    """WHI RAG system state management."""
    # User input
    question: str
    
    # Conversation history context
    conversation_history: Optional[List[Dict[str, Any]]]  # Historical conversation records
    context_summary: Optional[str]  # Context summary
    related_previous_qa: Optional[List[Dict[str, str]]]  # Related historical Q&A
    
    # Question classification
    question_type: Optional[str]  # "variable", "dataset", "general"
    
    # Retrieval related
    search_query: Optional[str]
    retrieved_documents: Optional[List[Document]]
    
    # Generation related
    context: Optional[str]
    answer: Optional[str]
    summary_answer: Optional[str]  # Summary answer
    
    # Validation related
    confidence_score: Optional[float]
    sources: Optional[List[Dict[str, Any]]]
    
    # Processing steps
    processing_steps: Optional[List[str]]
    
    # Error handling
    error: Optional[str]