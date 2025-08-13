from shiny import ui, reactive
import asyncio
from datetime import datetime

class MessageHandlers:
    """Message handling event class for processing user interactions"""
    
    def __init__(self, question_processor, history_manager):
        self.question_processor = question_processor
        self.history_manager = history_manager
    
    def setup_handlers(self, input, chat_messages, current_answer, is_processing):
        """Setup all message handling events"""
        
        @reactive.Effect
        @reactive.event(input.send_message)
        def handle_send_message():
            """Handle send message event"""
            question = input.chat_input()
            if not question.strip():
                return
            
            # Add user message
            messages = chat_messages.get().copy()
            timestamp = datetime.now()
            messages.append({
                'type': 'user',
                'content': question,
                'timestamp': timestamp
            })
            chat_messages.set(messages)
            
            # Clear input field
            ui.update_text_area("chat_input", value="")
            
            # Process question asynchronously
            async def process_and_respond():
                is_processing.set(True)
                try:
                    result = await self.question_processor.process_question(question, chat_messages.get())
                    
                    # Add assistant reply
                    messages = chat_messages.get().copy()
                    messages.append({
                        'type': 'assistant',
                        'content': result['summary_answer'],
                        'timestamp': timestamp
                    })
                    chat_messages.set(messages)
                    
                    # Set detailed answer
                    current_answer.set(result['detailed_answer'])
                    
                    # Add to history
                    self.history_manager.add_to_history(
                        question, 
                        result['detailed_answer'], 
                        result['summary_answer'], 
                        timestamp
                    )
                    
                finally:
                    is_processing.set(False)
            
            # Run in new event loop
            asyncio.create_task(process_and_respond())
        
        @reactive.Effect
        @reactive.event(input.clear_chat)
        def handle_clear_chat():
            """Clear chat history"""
            chat_messages.set([])
            current_answer.set("")
            self.history_manager.clear_history()
        
        # Example question click events
        @reactive.Effect
        @reactive.event(input.example1)
        def handle_example1():
            ui.update_text_area("chat_input", value="What are the measurement units and normal ranges for hemoglobin (HGB) variable in WHI study?")
        
        @reactive.Effect
        @reactive.event(input.example2)
        def handle_example2():
            ui.update_text_area("chat_input", value="What specific indicators are included in Form 80 physical measurements in WHI study?")
        
        @reactive.Effect
        @reactive.event(input.example3)
        def handle_example3():
            ui.update_text_area("chat_input", value="What are the main differences between WHI Observational Study (OS) and Clinical Trial (CT)?")