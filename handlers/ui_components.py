from shiny import ui

class UIComponents:
    """UI component rendering class for creating interface elements"""
    
    @staticmethod
    def chat_system_status(system_ready: bool):
        """Display chat system status"""
        if system_ready:
            return ui.div(
                "✅ RAG System Ready",
                style="padding: 10px 15px; background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%); color: #2e7d32; border-radius: 8px; font-size: 0.9rem; margin-bottom: 15px; font-weight: 600; border: 1px solid #81c784;"
            )
        else:
            return ui.div(
                "⚠️ Demo Mode",
                style="padding: 10px 15px; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); color: #ef6c00; border-radius: 8px; font-size: 0.9rem; margin-bottom: 15px; font-weight: 600; border: 1px solid #ffcc02;"
            )
    
    @staticmethod
    def chat_history(messages: list):
        """Display chat history"""
        if not messages:
            # Display welcome message and example questions
            return ui.div(
                # Welcome message
                ui.div(
                    "👋 Welcome! Please ask any questions about WHI data, variables, or research methods.",
                    style="color: #6c757d; text-align: center; padding: 20px 20px 15px 20px; font-style: italic;"
                ),
                
                # Example questions title
                ui.div(
                    "💡 Quick Start - Click questions below to fill input field:",
                    style="color: #495057; text-align: center; font-weight: 600; margin-bottom: 15px; font-size: 0.9rem;"
                ),
                
                # Example question buttons
                ui.div(
                    {"style": "display: flex; flex-direction: column; gap: 10px; padding: 0 20px 20px 20px;"},
                    ui.input_action_button(
                        "example1",
                        "🩸 What are the measurement units and normal ranges for hemoglobin (HGB) variable in WHI study?",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); color: #1565c0; border: 1px solid #90caf9; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    ),
                    ui.input_action_button(
                        "example2",
                        "📊 What specific indicators are included in Form 80 physical measurements in WHI study?",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); color: #2e7d32; border: 1px solid #81c784; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    ),
                    ui.input_action_button(
                        "example3",
                        "🎯 What are the main differences between WHI Observational Study (OS) and Clinical Trial (CT)?",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); color: #ef6c00; border: 1px solid #ffcc02; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    )
                )
            )
        
        chat_elements = []
        # Convert chat messages to conversation history format
        for msg in messages:
            if msg['type'] == 'user':
                chat_elements.append(
                    ui.div(
                        {"style": "margin: 12px 0; text-align: right;"},
                        ui.div(
                            msg['content'],
                            style="display: inline-block; background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%); color: white; padding: 12px 18px; border-radius: 18px 18px 6px 18px; max-width: 80%; word-wrap: break-word; box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3); font-weight: 500;"
                        )
                    )
                )
            else:  # assistant
                chat_elements.append(
                    ui.div(
                        {"style": "margin: 12px 0; text-align: left;"},
                        ui.div(
                            ui.HTML(msg['content']),
                            style="display: inline-block; background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%); color: #1565c0; padding: 12px 18px; border-radius: 18px 18px 18px 6px; max-width: 80%; word-wrap: break-word; box-shadow: 0 4px 12px rgba(33, 150, 243, 0.15); border: 1px solid rgba(33, 150, 243, 0.1);"
                        )
                    )
                )
        
        return ui.div(*chat_elements)
    
    @staticmethod
    def current_answer_details(answer: str):
        """Display current answer details"""
        if answer:
            return ui.div(
                ui.HTML(answer),
                style="padding: 15px; line-height: 1.6;"
            )
        else:
            return ui.div(
                "💡 Ask a question to view detailed analysis here.",
                style="color: #6c757d; padding: 15px; text-align: center; font-style: italic;"
            )
    
    @staticmethod
    def history_indicator(history: list, index: int):
        """Display current viewing history record indicator"""
        if not history:
            return ui.div()
        
        if index == -1:
            return ui.div(
                "📍 Latest Answer",
                style="color: #28a745; font-size: 0.85rem; font-weight: 500;"
            )
        else:
            return ui.div(
                f"📚 History {index + 1}/{len(history)}",
                style="color: #6c757d; font-size: 0.85rem; font-weight: 500;"
            )
    
    @staticmethod
    def history_navigation(history: list, index: int):
        """History navigation controls"""
        if len(history) <= 1:
            return ui.div(
                "💭 No History Available",
                style="text-align: center; color: #6c757d; font-size: 0.85rem; padding: 5px;"
            )
        
        total = len(history)
        
        return ui.div(
            {"style": "display: flex; justify-content: space-between; align-items: center;"},
            
            # Left: Previous button
            ui.input_action_button(
                "prev_answer",
                "◀ Previous",
                style="padding: 6px 12px; font-size: 0.85rem; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;"
            ),
            
            # Center: Page indicator and back to latest button
            ui.div(
                {"style": "display: flex; gap: 10px; align-items: center;"},
                ui.div(
                    f"{index + 1} / {total}" if index != -1 else "Latest",
                    style="color: #495057; font-size: 0.85rem; font-weight: 500;"
                ),
                ui.input_action_button(
                    "goto_latest",
                    "📍 Latest",
                    style="padding: 4px 8px; font-size: 0.8rem; background: #28a745; color: white; border: none; border-radius: 4px;"
                ) if index != -1 else ui.div()
            ),
            
            # Right: Next button
            ui.input_action_button(
                "next_answer",
                "Next ▶",
                style="padding: 6px 12px; font-size: 0.85rem; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;"
            )
        )
    
    @staticmethod
    def context_status(messages: list):
        """Display conversation context status"""
        context_count = len([msg for msg in messages if msg['type'] == 'user'])
        
        if context_count > 0:
            return ui.div(
                f"💭 Conversation Context: {context_count} rounds",
                style="padding: 8px 12px; background: #e3f2fd; color: #1565c0; border-radius: 6px; font-size: 0.8rem; margin-bottom: 10px; text-align: center;"
            )
        return ui.div()