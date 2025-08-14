from shiny import ui, reactive
import asyncio
from datetime import datetime

class MessageHandlers:
    """Message handling event class for processing user interactions"""
    
    def __init__(self, question_processor, history_manager):
        self.question_processor = question_processor
        self.history_manager = history_manager
    
    def setup_handlers(self, input, chat_messages, current_answer, is_processing, output_language):
        """Setup all message handling events"""
        
        @reactive.Effect
        @reactive.event(input.send_message)
        async def handle_send_message():
            """Handle send message event"""
            question = input.chat_input().strip()
            if not question or is_processing.get():
                return
            
            is_processing.set(True)
            timestamp = datetime.now()
            
            try:
                # Add user message
                messages = chat_messages.get().copy()
                messages.append({
                    'type': 'user',
                    'content': question,
                    'timestamp': timestamp
                })
                chat_messages.set(messages)
                ui.update_text_area("chat_input", value="")
                
                # Process question
                result = await self.question_processor.process_question(
                    question, messages, output_language.get()
                )
                
                # Add assistant reply
                current_messages = chat_messages.get().copy()
                current_messages.append({
                    'type': 'assistant',
                    'content': result['summary_answer'],
                    'timestamp': timestamp
                })
                chat_messages.set(current_messages)
                
                # Set detailed answer and add to history
                current_answer.set(result['detailed_answer'])
                self.history_manager.add_to_history(
                    question, result['detailed_answer'], 
                    result['summary_answer'], timestamp
                )
                
            except Exception as e:
                print(f"Error processing message: {e}")
                # 简化错误处理
                current_messages = chat_messages.get().copy()
                current_messages.append({
                    'type': 'assistant',
                    'content': f'抱歉，处理您的问题时出现错误：{str(e)}',
                    'timestamp': timestamp
                })
                chat_messages.set(current_messages)
            finally:
                is_processing.set(False)
        
        # 简化示例问题处理
        example_questions = {
            "example1": "What are the measurement units and normal ranges for hemoglobin (HGB) variable in WHI study?",
            "example2": "What specific indicators are included in Form 80 physical measurements in WHI study?",
            "example3": "What are the main differences between WHI Observational Study (OS) and Clinical Trial (CT)?"
        }
        
        for example_id, question_text in example_questions.items():
            @reactive.Effect
            @reactive.event(getattr(input, example_id))
            def handle_example(text=question_text):
                ui.update_text_area("chat_input", value=text)
        
        @reactive.Effect
        @reactive.event(input.clear_chat)
        def handle_clear_chat():
            """Clear chat history"""
            chat_messages.set([])
            current_answer.set("")
            self.history_manager.clear_history()