from shiny import ui

class UIUtils:
    """UI utility class for creating application interface components"""
    
    @staticmethod
    def create_app_ui():
        """Create application UI - moved from original app_ui"""
        return ui.page_fluid(
            # Include external CSS file
            ui.tags.link(rel="stylesheet", href="styles.css"),
            
            # Top header area
            ui.div(
                {"class": "top-header"},
                ui.div(
                    {"style": "display: flex; align-items: center; justify-content: space-between;"},
                    # Left: Sidebar toggle button
                    ui.div(
                        ui.input_action_button(
                            "toggle_sidebar",
                            "",
                            class_="sidebar-toggle",
                            style="background: none; border: none; font-size: 1.5rem; color: #451a03; cursor: pointer; padding: 8px; border-radius: 4px; transition: all 0.3s ease;"
                        ),
                        style="flex: 0 0 auto;"
                    ),
                    # Center: Title content
                    ui.div(
                        [
                            ui.h2("🧠 WHI Data Q&A Assistant"),
                            ui.p("Ask questions about WHI variables, datasets, or research methods")
                        ],
                        style="flex: 1; text-align: center;"
                    ),
                    # Right: Placeholder for symmetry
                    ui.div(
                        style="flex: 0 0 auto; width: 60px;"
                    )
                )
            ),
            
            # Main content area
            ui.div(
                {"class": "main-content", "id": "main-content", "style": "display: flex; height: calc(100vh - 80px); transition: all 0.3s ease;"},
                
                # Left sidebar (original chat panel)
                ui.div(
                    {
                        "class": "sidebar", 
                        "id": "sidebar",
                        "style": "width: 400px; min-width: 400px; display: flex; flex-direction: column; background: #fed7aa; border-right: 1px solid #ea580c; padding: 15px; transition: all 0.3s ease; overflow: hidden;"
                    },
                    
                    # System status
                    ui.output_ui("chat_system_status"),
                    
                    # Chat history area
                    ui.div(
                        {"class": "chat-history"},
                        ui.output_ui("chat_history")
                    ),
                    
                    # Input area
                    ui.div(
                        {"class": "input-area"},
                        ui.div(
                            {"style": "position: relative;"},
                            ui.input_text_area(
                                "chat_input",
                                "",
                                placeholder="💬 Enter your questions about WHI data... (Press Enter to send, Shift+Enter for new line)",
                                height="100px",
                                width="100%"
                            )
                        ),
                        ui.div(
                            {"style": "margin-top: 18px; display: flex; justify-content: space-between; align-items: center;"},
                            ui.div(
                                # Empty placeholder to keep buttons right-aligned
                                style="flex: 1;"
                            ),
                            ui.div(
                                [
                                    ui.input_action_button(
                                        "send_message",
                                        "📤 Send",
                                        class_="btn-primary"
                                    ),
                                    ui.input_action_button(
                                        "clear_chat",
                                        "🗑️ Clear",
                                        class_="btn-secondary"
                                    )
                                ]
                            )
                        ),
                        # Tip text moved below buttons
                        ui.div(
                            "💡 Tip: Press Enter to send, Shift+Enter for new line",
                            style="color: #78909c; font-size: 12px; font-weight: 500; text-align: center; margin-top: 10px;"
                        )
                    )
                ),
                
                # Right main panel
                ui.div(
                    {
                        "id": "main-panel",
                        "style": "flex: 1; display: flex; flex-direction: column; height: 100%; min-height: calc(100vh - 80px); padding: 0; transition: all 0.3s ease; background: #fffbf5;"
                    },
                    
                    # Current answer details
                    ui.card(
                        ui.card_header(
                            ui.div(
                                {"style": "display: flex; justify-content: space-between; align-items: center;"},
                                ui.div("🎯 Answer Details"),
                                ui.output_ui("history_indicator")  # Show which answer is currently being viewed
                            )
                        ),
                        ui.div(
                            {"style": "flex: 1; overflow-y: auto; padding: 5px; height: 100%;"},
                            ui.output_ui("current_answer_details")
                        ),
                        # History navigation control panel
                        ui.div(
                            {"style": "padding: 10px 15px; border-top: 1px solid #e2e8f0; background: #f8fafc;"},
                            ui.output_ui("history_navigation")
                        )
                    )
                )
            ),
            
            # CSS styles
            ui.tags.style("""
                /* Sidebar toggle button styles - improved icon */
                .sidebar-toggle:before {
                    content: '◧';
                    font-weight: bold;
                }
                
                .sidebar-toggle:hover {
                    background: rgba(69, 26, 3, 0.1) !important;
                    transform: scale(1.05);
                }
                
                /* Sidebar collapsed state */
                .sidebar.collapsed {
                    width: 0 !important;
                    min-width: 0 !important;
                    padding: 0 !important;
                    border-right: none !important;
                    overflow: hidden !important;
                }
                
                /* Main panel expanded state */
                .main-panel.expanded {
                    width: 100% !important;
                }
                
                /* Responsive adjustments */
                @media (max-width: 768px) {
                    .sidebar {
                        position: absolute;
                        left: 0;
                        top: 0;
                        height: 100%;
                        z-index: 1000;
                        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
                    }
                    
                    .sidebar.collapsed {
                        left: -400px;
                    }
                }
            """),
            
            # JavaScript code
            ui.tags.script("""
                document.addEventListener('DOMContentLoaded', function() {
                    // Keyboard event listener
                    const chatInput = document.getElementById('chat_input');
                    if (chatInput) {
                        chatInput.addEventListener('keydown', function(event) {
                            if (event.key === 'Enter' && !event.shiftKey) {
                                event.preventDefault();
                                const sendButton = document.getElementById('send_message');
                                if (sendButton && chatInput.value.trim()) {
                                    sendButton.click();
                                }
                            }
                        });
                    }
                    
                    // Sidebar toggle functionality
                    let sidebarCollapsed = false;
                    const toggleButton = document.getElementById('toggle_sidebar');
                    const sidebar = document.getElementById('sidebar');
                    const mainPanel = document.getElementById('main-panel');
                    
                    if (toggleButton && sidebar && mainPanel) {
                        toggleButton.addEventListener('click', function() {
                            sidebarCollapsed = !sidebarCollapsed;
                            
                            if (sidebarCollapsed) {
                                sidebar.classList.add('collapsed');
                                mainPanel.classList.add('expanded');
                                toggleButton.style.transform = 'rotate(180deg)';
                            } else {
                                sidebar.classList.remove('collapsed');
                                mainPanel.classList.remove('expanded');
                                toggleButton.style.transform = 'rotate(0deg)';
                            }
                        });
                    }
                    
                    // Add keyboard shortcut support (Ctrl+B to toggle sidebar)
                    document.addEventListener('keydown', function(event) {
                        if (event.ctrlKey && event.key === 'b') {
                            event.preventDefault();
                            if (toggleButton) {
                                toggleButton.click();
                            }
                        }
                    });
                });
            """),
            
            fillable=True
        )