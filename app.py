from shiny import App, ui, render, reactive, Inputs, Outputs, Session
import asyncio
from datetime import datetime
import markdown
from pathlib import Path

# Import project modules
from config.settings import WHIConfig
from rag.system import WHIRAGSystem
from handlers import UIComponents, MessageHandlers, HistoryHandlers, QuestionProcessor
from handlers.utils import UIUtils

# Initialize configuration and system
config = WHIConfig()
system_ready = False
rag_system = None

# Attempt to initialize RAG system
try:
    rag_system = WHIRAGSystem()
    system_ready = True
    print("✅ RAG system initialized successfully")
except Exception as e:
    print(f"⚠️ RAG system initialization failed: {e}")
    print("🔄 Using demo mode")
    rag_system = None

# Create UI using UIUtils
app_ui = UIUtils.create_app_ui()


def server(input: Inputs, output: Outputs, session: Session):
    # Reactive values
    chat_messages = reactive.Value([])
    current_answer = reactive.Value("")
    is_processing = reactive.Value(False)
    
    # Initialize processors
    question_processor = QuestionProcessor(rag_system, system_ready)
    history_manager = HistoryHandlers()
    message_handlers = MessageHandlers(question_processor, history_manager)
    
    # Setup event handlers
    message_handlers.setup_handlers(input, chat_messages, current_answer, is_processing)
    history_manager.setup_navigation_handlers(input)
    
    # UI rendering functions
    @output
    @render.ui
    def chat_system_status():
        return UIComponents.chat_system_status(system_ready)
    
    @output
    @render.ui
    def chat_history():
        return UIComponents.chat_history(chat_messages.get())
    
    @output
    @render.ui
    def current_answer_details():
        answer = history_manager.get_current_display_answer(current_answer)
        return UIComponents.current_answer_details(answer)
    
    @output
    @render.ui
    def history_indicator():
        return UIComponents.history_indicator(
            history_manager.answer_history.get(), 
            history_manager.current_history_index.get()
        )
    
    @output
    @render.ui
    def history_navigation():
        return UIComponents.history_navigation(
            history_manager.answer_history.get(), 
            history_manager.current_history_index.get()
        )
    
    @output
    @render.ui
    def context_status():
        return UIComponents.context_status(chat_messages.get())

# Create application
app = App(
    app_ui, 
    server,
    static_assets=Path(__file__).parent / "static"
)

if __name__ == "__main__":
    app.run()


