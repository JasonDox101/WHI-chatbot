from shiny import App, ui, render, reactive, Inputs, Outputs, Session
import asyncio
from datetime import datetime
import markdown
from pathlib import Path

# 导入项目模块
from config.settings import WHIConfig
from rag.system import WHIRAGSystem

# 初始化配置和系统
config = WHIConfig()
system_ready = False
rag_system = None

# 尝试初始化RAG系统
try:
    rag_system = WHIRAGSystem()
    system_ready = True
    print("✅ RAG系统初始化成功")
except Exception as e:
    print(f"⚠️ RAG系统初始化失败: {e}")
    print("🔄 将使用演示模式")
    rag_system = None

# 创建UI
app_ui = ui.page_fluid(
    # 引入外部CSS文件
    ui.tags.link(rel="stylesheet", href="styles.css"),
    
    # 顶部标题区域 - 保持原样
    ui.div(
        {"class": "top-header"},
        ui.div(
            {"style": "display: flex; align-items: center; justify-content: space-between;"},
            # 左侧：侧边栏切换按钮
            ui.div(
                ui.input_action_button(
                    "toggle_sidebar",
                    "",
                    class_="sidebar-toggle",
                    style="background: none; border: none; font-size: 1.5rem; color: #451a03; cursor: pointer; padding: 8px; border-radius: 4px; transition: all 0.3s ease;"
                ),
                style="flex: 0 0 auto;"
            ),
            # 中间：标题内容 - 保持原样
            ui.div(
                [
                    ui.h2("🧠 WHI 数据问答助手"),
                    ui.p("询问 WHI 变量、数据集或研究方法相关问题")
                ],
                style="flex: 1; text-align: center;"
            ),
            # 右侧：占位符保持对称
            ui.div(
                style="flex: 0 0 auto; width: 60px;"
            )
        )
    ),
    
    # 主要内容区域
    ui.div(
        {"class": "main-content", "id": "main-content", "style": "display: flex; height: calc(100vh - 80px); transition: all 0.3s ease;"},
        
        # 左侧侧边栏（原聊天面板）
        ui.div(
            {
                "class": "sidebar", 
                "id": "sidebar",
                "style": "width: 400px; min-width: 400px; display: flex; flex-direction: column; background: #fed7aa; border-right: 1px solid #ea580c; padding: 15px; transition: all 0.3s ease; overflow: hidden;"
            },
            
            # 系统状态
            ui.output_ui("chat_system_status"),
            
            # 聊天历史区域
            ui.div(
                {"class": "chat-history"},
                ui.output_ui("chat_history")
            ),
            
            # 输入区域 - 调整布局
            ui.div(
                {"class": "input-area"},
                ui.div(
                    {"style": "position: relative;"},
                    ui.input_text_area(
                        "chat_input",
                        "",
                        placeholder="💬 输入您关于 WHI 数据的问题... (按 Enter 发送，Shift+Enter 换行)",
                        height="100px",
                        width="100%"
                    )
                ),
                ui.div(
                    {"style": "margin-top: 18px; display: flex; justify-content: space-between; align-items: center;"},
                    ui.div(
                        # 空白占位，保持按钮居右
                        style="flex: 1;"
                    ),
                    ui.div(
                        [
                            ui.input_action_button(
                                "send_message",
                                "📤 发送",
                                class_="btn-primary"
                            ),
                            ui.input_action_button(
                                "clear_chat",
                                "🗑️ 清空",
                                class_="btn-secondary"
                            )
                        ]
                    )
                ),
                # 提示文字移到按钮下方
                ui.div(
                    "💡 提示：按 Enter 发送，Shift+Enter 换行",
                    style="color: #78909c; font-size: 12px; font-weight: 500; text-align: center; margin-top: 10px;"
                )
            )
        ),
        
        # 右侧主面板 - 自动调整宽度
        ui.div(
            {
                "id": "main-panel",
                "style": "flex: 1; display: flex; flex-direction: column; height: 100%; min-height: calc(100vh - 80px); padding: 0; transition: all 0.3s ease; background: #fffbf5;"
            },
            
            # 当前答案详情 - 完全填充右侧面板
            ui.card(
                ui.card_header("🎯 当前答案详情"),
                ui.div(
                    {"style": "flex: 1; overflow-y: auto; padding: 5px; height: 100%;"},
                    ui.output_ui("current_answer_details")
                )
            )
        )
    ),
    
    # 添加侧边栏控制的JavaScript和CSS
    ui.tags.style("""
        /* 侧边栏切换按钮样式 - 改进图标 */
        .sidebar-toggle:before {
            content: '◧';
            font-weight: bold;
        }
        
        .sidebar-toggle:hover {
            background: rgba(69, 26, 3, 0.1) !important;
            transform: scale(1.05);
        }
        
        /* 侧边栏隐藏状态 */
        .sidebar.collapsed {
            width: 0 !important;
            min-width: 0 !important;
            padding: 0 !important;
            border-right: none !important;
            overflow: hidden !important;
        }
        
        /* 主面板展开状态 */
        .main-panel.expanded {
            width: 100% !important;
        }
        
        /* 响应式调整 */
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
    
    # 添加键盘事件监听和侧边栏控制的JavaScript
    ui.tags.script("""
        document.addEventListener('DOMContentLoaded', function() {
            // 键盘事件监听
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
            
            // 侧边栏切换功能
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
            
            // 添加键盘快捷键支持 (Ctrl+B 切换侧边栏)
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



# 服务器逻辑保持不变...
def server(input: Inputs, output: Outputs, session: Session):
    # 响应式值
    chat_messages = reactive.Value([])
    current_answer = reactive.Value("")
    is_processing = reactive.Value(False)
    
    @output
    @render.ui
    def chat_system_status():
        """显示聊天系统状态"""
        if system_ready:
            return ui.div(
                "✅ RAG 系统就绪",
                style="padding: 10px 15px; background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%); color: #2e7d32; border-radius: 8px; font-size: 0.9rem; margin-bottom: 15px; font-weight: 600; border: 1px solid #81c784;"
            )
        else:
            return ui.div(
                "⚠️ 演示模式",
                style="padding: 10px 15px; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); color: #ef6c00; border-radius: 8px; font-size: 0.9rem; margin-bottom: 15px; font-weight: 600; border: 1px solid #ffcc02;"
            )
    
    @output
    @render.ui
    def chat_history():
        """显示聊天历史"""
        messages = chat_messages.get()
        if not messages:
            # 显示欢迎信息和示例问题
            return ui.div(
                # 欢迎信息
                ui.div(
                    "👋 欢迎！请询问任何关于 WHI 数据、变量或研究方法的问题。",
                    style="color: #6c757d; text-align: center; padding: 20px 20px 15px 20px; font-style: italic;"
                ),
                
                # 示例问题标题
                ui.div(
                    "💡 快速开始 - 点击下方问题填入输入框：",
                    style="color: #495057; text-align: center; font-weight: 600; margin-bottom: 15px; font-size: 0.9rem;"
                ),
                
                # 示例问题按钮
                ui.div(
                    {"style": "display: flex; flex-direction: column; gap: 10px; padding: 0 20px 20px 20px;"},
                    ui.input_action_button(
                        "example1",
                        "🩸 WHI研究中血红蛋白(HGB)变量的测量单位和正常范围是什么？",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); color: #1565c0; border: 1px solid #90caf9; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    ),
                    ui.input_action_button(
                        "example2",
                        "📊 WHI研究中Form 80物理测量包含哪些具体指标？",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); color: #2e7d32; border: 1px solid #81c784; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    ),
                    ui.input_action_button(
                        "example3",
                        "🎯 WHI观察性研究(OS)和临床试验(CT)的主要区别是什么？",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); color: #ef6c00; border: 1px solid #ffcc02; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    )
                )
            )
        
        chat_elements = []
        # 转换聊天消息为对话历史格式
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
    
    @output
    @render.ui
    def current_answer_details():
        """显示当前答案详情"""
        answer = current_answer.get()
        if answer:
            return ui.div(
                ui.HTML(answer),
                style="padding: 15px; line-height: 1.6;"
            )
        else:
            return ui.div(
                "💡 提出问题以在此查看详细分析。",
                style="color: #6c757d; padding: 15px; text-align: center; font-style: italic;"
            )
    
    @output
    @render.ui
    def context_status():
        """显示对话上下文状态"""
        messages = chat_messages.get()
        context_count = len([msg for msg in messages if msg['type'] == 'user'])
        
        if context_count > 0:
            return ui.div(
                f"💭 对话上下文: {context_count} 轮对话",
                style="padding: 8px 12px; background: #e3f2fd; color: #1565c0; border-radius: 6px; font-size: 0.8rem; margin-bottom: 10px; text-align: center;"
            )
        return ui.div()
    
    # 在文件顶部添加HTML转义处理
    import html
    
    # 修改process_question函数中的markdown转换部分
    # 在process_question函数前添加格式标准化函数
    def standardize_detailed_answer_format(raw_answer: str) -> str:
        """标准化右侧详细答案的显示格式"""
        import re
        
        # 确保答案以标准结构开始
        if not raw_answer.strip().startswith('#'):
            raw_answer = f"## 详细分析\n\n{raw_answer}"
        
        # 标准化标题格式
        raw_answer = re.sub(r'^#{1,6}\s*(.+)$', lambda m: f"## {m.group(1).strip()}", raw_answer, flags=re.MULTILINE)
        
        # 标准化列表格式
        raw_answer = re.sub(r'^[•·*-]\s*', '- ', raw_answer, flags=re.MULTILINE)
        
        # 确保段落间距
        raw_answer = re.sub(r'\n{3,}', '\n\n', raw_answer)
        
        # 标准化数值显示
        raw_answer = re.sub(r'(\d+(?:\.\d+)?\s*(?:g/dL|mg/dL|mmHg|%|年|岁))', r'**\1**', raw_answer)
        
        return raw_answer.strip()
    
    # 修改process_question函数中的详细答案处理部分
    async def process_question(question):
        try:
            if rag_system and system_ready:
                # 获取对话历史
                messages = chat_messages.get()
                conversation_history = []
                
                # 改进的对话历史转换逻辑
                for i in range(0, len(messages), 2):  # 每两条消息为一对
                    if i < len(messages) and messages[i]['type'] == 'user':
                        user_question = messages[i]['content']
                        assistant_answer = ""
                        
                        # 查找对应的助手回复
                        if i + 1 < len(messages) and messages[i + 1]['type'] == 'assistant':
                            assistant_answer = messages[i + 1]['content']
                        
                        # 只添加有完整问答对的历史
                        if assistant_answer:
                            conversation_history.append({
                                "question": user_question,
                                "answer": assistant_answer,
                                "timestamp": messages[i]['timestamp'].isoformat() if hasattr(messages[i]['timestamp'], 'isoformat') else str(messages[i]['timestamp'])
                            })
                    
                # 限制对话历史长度，避免累积过多内容
                if len(conversation_history) > 3:  # 只保留最近3轮完整对话
                    conversation_history = conversation_history[-3:]
                
                
                # 使用RAG系统处理，传入对话历史
                result = rag_system.process_question(question, conversation_history)
                
                # 获取详细答案和总结答案
                detailed_answer = result.get('answer', '未生成答案')
                
                # 🔧 添加格式标准化
                detailed_answer = standardize_detailed_answer_format(detailed_answer)
                
                summary_answer = result.get('summary_answer', '未生成总结')
                confidence = result.get('confidence_score', 0)
                sources = result.get('sources', [])
                
                # 将详细答案转换为markdown格式
                markdown_answer = markdown.markdown(detailed_answer, extensions=['extra', 'codehilite', 'tables', 'toc'])
                
                # 优化格式化详细答案（显示在右侧）- 确保HTML正确渲染
                # 在process_question函数中，修改formatted_detailed_answer部分
                formatted_detailed_answer = f"""
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
                        <strong style="font-size: 1.05rem; color: #2c3e50;">详细分析报告</strong>
                    </div>
                    <div class="markdown-content document-style english-optimized">
                        {markdown_answer}
                    </div>
                </div>

                <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; padding: 0 4px;">
                    <div style="background: white; border-radius: 6px; padding: 8px 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); flex: 1; min-width: 120px;">
                        <div style="display: flex; align-items: center; margin-bottom: 4px;">
                            <span style="margin-right: 4px; font-size: 0.9rem;">📊</span>
                            <strong style="color: #2c3e50; font-size: 0.85rem;">置信度</strong>
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="background: {'#28a745' if confidence > 0.7 else '#ffc107' if confidence > 0.4 else '#dc3545'}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">
                                {confidence:.2f}
                            </span>
                            <span style="margin-left: 6px; color: #6c757d; font-size: 0.75rem;">
                                ({'高' if confidence > 0.7 else '中' if confidence > 0.4 else '低'})
                            </span>
                        </div>
                    </div>
                    
                    {f'''
                    <div style="background: white; border-radius: 6px; padding: 8px 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); flex: 1; min-width: 120px;">
                        <div style="display: flex; align-items: center; margin-bottom: 4px;">
                            <span style="margin-right: 4px; font-size: 0.9rem;">📚</span>
                            <strong style="color: #2c3e50; font-size: 0.85rem;">参考来源</strong>
                        </div>
                        <div style="color: #495057; font-size: 0.8rem;">
                            <span style="background: #e9ecef; padding: 1px 6px; border-radius: 8px; font-weight: 500;">
                                {len(sources)} 个文档
                            </span>
                        </div>
                    </div>
                    ''' if sources else ''}
                </div>
                """
                
                current_answer.set(formatted_detailed_answer)
                
                # 返回总结答案（显示在左侧聊天框）
                return summary_answer
            else:
                # 简单关键词匹配的fallback逻辑 - 也支持markdown
                question_lower = question.lower()
                if any(keyword in question_lower for keyword in ['血红蛋白', 'hemo']):
                    answer = "**血红蛋白 (HEMO)** 是测量血液携氧能力的关键变量。\n\n- 通常以 `g/dL` 为单位测量\n- 是评估贫血状态的重要指标"
                elif any(keyword in question_lower for keyword in ['mesa']):
                    answer = "**MESA（多种族动脉粥样硬化研究）** 是一项检查心血管疾病发展的纵向研究。\n\n主要特点：\n- 多种族参与\n- 长期跟踪\n- 心血管疾病预防"
                else:
                    answer = f"我找到了与 **{question}** 相关的信息。\n\n请提供更具体的问题以获得详细答案。"
                
                # 转换为HTML
                markdown_answer = markdown.markdown(answer, extensions=['extra', 'codehilite'])
                
                # 为fallback模式也提供更好的格式化
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
                        <strong style="font-size: 1.1rem; color: #2c3e50;">基础回答</strong>
                    </div>
                    <div class="markdown-content document-style english-optimized">
                        {markdown_answer}
                    </div>
                </div>

                <div style="background: #fff3cd; color: #856404; padding: 12px 16px; border-radius: 8px; text-align: center; font-size: 0.85rem; margin-top: 15px;">
                    ⚠️ 当前为演示模式，建议启用 RAG 系统获得更准确的答案
                </div>
                """
                
                current_answer.set(formatted_fallback)
                return answer
        except Exception as e:
            error_msg = f"处理问题时出错：{str(e)}"
            formatted_error = f"""
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 8px;">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 1.2rem; margin-right: 8px;">⚠️</span>
                    <strong>处理错误</strong>
                </div>
                <div style="font-size: 0.9rem; line-height: 1.5;">
                    {error_msg}
                </div>
            </div>
            """
            current_answer.set(formatted_error)
            return error_msg

    @reactive.Effect
    @reactive.event(input.send_message)
    def handle_send_message():
        """处理发送消息"""
        question = input.chat_input()
        if not question.strip():
            return
        
        # 添加用户消息
        messages = chat_messages.get().copy()
        messages.append({
            'type': 'user',
            'content': question,
            'timestamp': datetime.now()
        })
        chat_messages.set(messages)
        
        # 清空输入框
        ui.update_text_area("chat_input", value="")
        
        # 异步处理问题
        async def process_and_respond():
            is_processing.set(True)
            try:
                answer = await process_question(question)
                
                # 添加助手回复
                messages = chat_messages.get().copy()
                messages.append({
                    'type': 'assistant',
                    'content': answer,
                    'timestamp': datetime.now()
                })
                chat_messages.set(messages)
            finally:
                is_processing.set(False)
        
        # 在新的事件循环中运行
        asyncio.create_task(process_and_respond())
    
    @reactive.Effect
    @reactive.event(input.clear_chat)
    def handle_clear_chat():
        """清空聊天记录"""
        chat_messages.set([])
        current_answer.set("")
    
    # 修改示例问题点击事件 - 只填入输入框，不直接发送
    @reactive.Effect
    @reactive.event(input.example1)
    def handle_example1():
        ui.update_text_area("chat_input", value="WHI研究中血红蛋白(HGB)变量的测量单位和正常范围是什么？")
    
    @reactive.Effect
    @reactive.event(input.example2)
    def handle_example2():
        ui.update_text_area("chat_input", value="WHI研究中Form 80物理测量包含哪些具体指标？")
    
    @reactive.Effect
    @reactive.event(input.example3)
    def handle_example3():
        ui.update_text_area("chat_input", value="WHI观察性研究(OS)和临床试验(CT)的主要区别是什么？")


# 创建应用
app = App(
    app_ui, 
    server,
    static_assets=Path(__file__).parent / "static"
)

if __name__ == "__main__":
    app.run()