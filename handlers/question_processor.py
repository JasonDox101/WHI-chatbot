import markdown
import re

class QuestionProcessor:
    """Question processor class for handling user queries"""
    
    def __init__(self, rag_system=None, system_ready=False):
        self.rag_system = rag_system
        self.system_ready = system_ready
    
    @staticmethod
    def standardize_detailed_answer_format(raw_answer: str) -> str:
        """Standardize the display format of detailed answers in the right panel"""
        # Ensure answer starts with standard structure
        if not raw_answer.strip().startswith('#'):
            raw_answer = f"## Detailed Analysis\n\n{raw_answer}"
        
        # Standardize heading format
        raw_answer = re.sub(r'^#{1,6}\s*(.+)$', lambda m: f"## {m.group(1).strip()}", raw_answer, flags=re.MULTILINE)
        
        # Standardize list format
        raw_answer = re.sub(r'^[•·*-]\s*', '- ', raw_answer, flags=re.MULTILINE)
        
        # Ensure proper paragraph spacing
        raw_answer = re.sub(r'\n{3,}', '\n\n', raw_answer)
        
        # Standardize numerical value display
        raw_answer = re.sub(r'(\d+(?:\.\d+)?\s*(?:g/dL|mg/dL|mmHg|%|years|yrs))', r'**\1**', raw_answer)
        
        return raw_answer.strip()
    
    async def process_question(self, question: str, chat_messages: list):
        """Main logic for processing questions"""
        try:
            if self.rag_system and self.system_ready:
                # Get conversation history
                conversation_history = []
                
                # Improved conversation history conversion logic
                for i in range(0, len(chat_messages), 2):  # Every two messages form a pair
                    if i < len(chat_messages) and chat_messages[i]['type'] == 'user':
                        user_question = chat_messages[i]['content']
                        assistant_answer = ""
                        
                        # Find corresponding assistant reply
                        if i + 1 < len(chat_messages) and chat_messages[i + 1]['type'] == 'assistant':
                            assistant_answer = chat_messages[i + 1]['content']
                        
                        # Only add complete Q&A pairs to history
                        if assistant_answer:
                            conversation_history.append({
                                "question": user_question,
                                "answer": assistant_answer,
                                "timestamp": chat_messages[i]['timestamp'].isoformat() if hasattr(chat_messages[i]['timestamp'], 'isoformat') else str(chat_messages[i]['timestamp'])
                            })
                        
                # Limit conversation history length to avoid accumulating too much content
                if len(conversation_history) > 3:  # Keep only the most recent 3 complete conversations
                    conversation_history = conversation_history[-3:]
                
                # Process using RAG system, passing conversation history
                result = self.rag_system.process_question(question, conversation_history)
                
                # Get detailed answer and summary answer
                detailed_answer = result.get('answer', 'No answer generated')
                
                # Add format standardization
                detailed_answer = self.standardize_detailed_answer_format(detailed_answer)
                
                summary_answer = result.get('summary_answer', 'No summary generated')
                confidence = result.get('confidence_score', 0)
                sources = result.get('sources', [])
                
                # Convert detailed answer to markdown format
                markdown_answer = markdown.markdown(detailed_answer, extensions=['extra', 'codehilite', 'tables', 'toc'])
                
                # Format detailed answer
                formatted_detailed_answer = self._format_detailed_answer(markdown_answer, confidence, sources)
                
                return {
                    'summary_answer': summary_answer,
                    'detailed_answer': formatted_detailed_answer
                }
            else:
                # Simple keyword matching fallback logic
                return self._fallback_answer(question)
                
        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            formatted_error = f"""
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 8px;">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 1.2rem; margin-right: 8px;">⚠️</span>
                    <strong>Processing Error</strong>
                </div>
                <div style="font-size: 0.9rem; line-height: 1.5;">
                    {error_msg}
                </div>
            </div>
            """
            return {
                'summary_answer': error_msg,
                'detailed_answer': formatted_error
            }
    
    def _format_detailed_answer(self, markdown_answer: str, confidence: float, sources: list) -> str:
        """Format detailed answer with styling and metadata"""
        return f"""
        <div class="answer-container" style="
            background: #ffffff; 
            border-radius: 8px; 
            padding: 0; 
            margin-bottom: 15px; 
            border-left: 4px solid #007bff; 
            overflow-y: auto; 
            max-height: calc(100vh - 200px); 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        ">
            <div style="display: flex; align-items: center; padding: 20px 24px 15px 24px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                <span style="font-size: 1.1rem; margin-right: 8px;">📋</span>
                <strong style="font-size: 1.05rem; color: #2c3e50;">Detailed Analysis Report</strong>
            </div>
            <div class="markdown-content document-style english-optimized">
                {markdown_answer}
            </div>
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; padding: 0 4px;">
            <div style="background: white; border-radius: 6px; padding: 8px 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); flex: 1; min-width: 120px;">
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span style="margin-right: 4px; font-size: 0.9rem;">📊</span>
                    <strong style="color: #2c3e50; font-size: 0.85rem;">Confidence</strong>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="background: {'#28a745' if confidence > 0.7 else '#ffc107' if confidence > 0.4 else '#dc3545'}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">
                        {confidence:.2f}
                    </span>
                    <span style="margin-left: 6px; color: #6c757d; font-size: 0.75rem;">
                        ({'High' if confidence > 0.7 else 'Medium' if confidence > 0.4 else 'Low'})
                    </span>
                </div>
            </div>
            
            {f'''
            <div style="background: white; border-radius: 6px; padding: 8px 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); flex: 1; min-width: 120px;">
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span style="margin-right: 4px; font-size: 0.9rem;">📚</span>
                    <strong style="color: #2c3e50; font-size: 0.85rem;">Sources</strong>
                </div>
                <div style="color: #495057; font-size: 0.8rem;">
                    <span style="background: #e9ecef; padding: 1px 6px; border-radius: 8px; font-weight: 500;">
                        {len(sources)} documents
                    </span>
                </div>
            </div>
            ''' if sources else ''}
        </div>
        """
    
    def _fallback_answer(self, question: str) -> dict:
        """Fallback mode answer processing"""
        question_lower = question.lower()
        if any(keyword in question_lower for keyword in ['hemoglobin', 'hemo', 'hgb']):
            answer = "**Hemoglobin (HEMO)** is a key variable for measuring blood oxygen-carrying capacity.\n\n- Usually measured in `g/dL` units\n- Important indicator for assessing anemia status"
        elif any(keyword in question_lower for keyword in ['mesa']):
            answer = "**MESA (Multi-Ethnic Study of Atherosclerosis)** is a longitudinal study examining cardiovascular disease development.\n\nKey features:\n- Multi-ethnic participation\n- Long-term follow-up\n- Cardiovascular disease prevention"
        else:
            answer = f"I found information related to **{question}**.\n\nPlease provide more specific questions for detailed answers."
        
        # Convert to HTML
        markdown_answer = markdown.markdown(answer, extensions=['extra', 'codehilite'])
        
        # Provide better formatting for fallback mode as well
        formatted_fallback = f"""
        <div class="answer-container" style="
            background: #ffffff; 
            border-radius: 8px; 
            padding: 0; 
            margin-bottom: 15px; 
            border-left: 4px solid #6c757d; 
            overflow-y: auto; 
            max-height: calc(100vh - 200px); 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        ">
            <div style="display: flex; align-items: center; padding: 20px 24px 15px 24px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                <span style="font-size: 1.2rem; margin-right: 8px;">💭</span>
                <strong style="font-size: 1.1rem; color: #2c3e50;">Basic Answer</strong>
            </div>
            <div class="markdown-content document-style english-optimized">
                {markdown_answer}
            </div>
        </div>

        <div style="background: #fff3cd; color: #856404; padding: 12px 16px; border-radius: 8px; text-align: center; font-size: 0.85rem; margin-top: 15px;">
            ⚠️ Currently in demo mode, recommend enabling RAG system for more accurate answers
        </div>
        """
        
        return {
            'summary_answer': answer,
            'detailed_answer': formatted_fallback
        }