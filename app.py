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
    # 引入外部CSS文件 - 修改路径
    ui.tags.link(rel="stylesheet", href="styles.css"),
    
    # 顶部标题区域
    ui.div(
        {"class": "top-header"},
        ui.h2("🧠 WHI 数据问答助手"),
        ui.p("询问 WHI 变量、数据集或研究方法相关问题")
    ),
    
    # 主要内容区域
    ui.div(
        {"class": "main-content", "style": "display: flex; gap: 25px; height: calc(100vh - 180px);"},
        
        # 左侧聊天面板
        ui.div(
            {"class": "chat-panel"},
            
            # 系统状态
            ui.output_ui("chat_system_status"),
            
            # 聊天历史区域
            ui.div(
                {"class": "chat-history"},
                ui.output_ui("chat_history")
            ),
            
            # 输入区域
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
                        {"style": "color: #78909c; font-size: 12px; font-weight: 500;"},
                        "💡 提示：按 Enter 发送，Shift+Enter 换行"
                    ),
                    ui.div(
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
                    )
                )
            )
        ),
        
        # 右侧主面板 - 移除快速示例，只保留答案详情
        ui.div(
            {"style": "flex: 1; display: flex; flex-direction: column; height: 100%; min-height: calc(100vh - 60px); padding-right: 0;"},
            
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
    
    # 添加键盘事件监听的JavaScript
    ui.tags.script("""
        document.addEventListener('DOMContentLoaded', function() {
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
                        "🩸 血红蛋白变量是什么？",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); color: #1565c0; border: 1px solid #90caf9; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    ),
                    ui.input_action_button(
                        "example2",
                        "📊 显示 MESA 研究数据集",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); color: #2e7d32; border: 1px solid #81c784; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    ),
                    ui.input_action_button(
                        "example3",
                        "🎯 WHI 的主要研究目标是什么？",
                        style="width: 100%; padding: 12px 16px; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); color: #ef6c00; border: 1px solid #ffcc02; border-radius: 8px; font-size: 0.9rem; text-align: left; transition: all 0.2s ease;"
                    )
                )
            )
        
        chat_elements = []
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
    
    async def process_question(question):
        """处理用户问题"""
        try:
            if rag_system and system_ready:
                # 使用RAG系统处理
                result = rag_system.process_question(question)
                
                # 获取详细答案和总结答案
                detailed_answer = result.get('answer', '未生成答案')
                summary_answer = result.get('summary_answer', '未生成总结')
                confidence = result.get('confidence_score', 0)
                sources = result.get('sources', [])
                
                # 将详细答案转换为markdown格式并渲染为HTML
                markdown_answer = markdown.markdown(detailed_answer, extensions=['extra', 'codehilite'])
                
                # 优化格式化详细答案（显示在右侧）- 使用markdown格式
                formatted_detailed_answer = f"""
                <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #007bff;">
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 1.2rem; margin-right: 8px;">🎯</span>
                        <strong style="font-size: 1.1rem; color: #2c3e50;">详细答案</strong>
                    </div>
                    <div style="line-height: 1.8; color: #34495e; font-size: 0.95rem;">
                        {markdown_answer}
                    </div>
                </div>
                
                <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;">
                    <div style="background: white; border-radius: 8px; padding: 12px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); flex: 1; min-width: 150px;">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="margin-right: 6px;">📊</span>
                            <strong style="color: #2c3e50; font-size: 0.9rem;">置信度评分</strong>
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="background: {'#28a745' if confidence > 0.7 else '#ffc107' if confidence > 0.4 else '#dc3545'}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold;">
                                {confidence:.2f}
                            </span>
                            <span style="margin-left: 8px; color: #6c757d; font-size: 0.8rem;">
                                ({'高' if confidence > 0.7 else '中' if confidence > 0.4 else '低'})
                            </span>
                        </div>
                    </div>
                    
                    {f'''
                    <div style="background: white; border-radius: 8px; padding: 12px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); flex: 1; min-width: 150px;">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="margin-right: 6px;">📚</span>
                            <strong style="color: #2c3e50; font-size: 0.9rem;">参考来源</strong>
                        </div>
                        <div style="color: #495057; font-size: 0.9rem;">
                            <span style="background: #e9ecef; padding: 2px 8px; border-radius: 12px; font-weight: 500;">
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
                <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; border-left: 4px solid #6c757d;">
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 1.2rem; margin-right: 8px;">💭</span>
                        <strong style="font-size: 1.1rem; color: #2c3e50;">基础回答</strong>
                    </div>
                    <div style="line-height: 1.8; color: #34495e; font-size: 0.95rem;">
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
        ui.update_text_area("chat_input", value="血红蛋白变量是什么？")
    
    @reactive.Effect
    @reactive.event(input.example2)
    def handle_example2():
        ui.update_text_area("chat_input", value="显示 MESA 研究数据集")
    
    @reactive.Effect
    @reactive.event(input.example3)
    def handle_example3():
        ui.update_text_area("chat_input", value="WHI 的主要研究目标是什么？")


# 创建应用
app = App(
    app_ui, 
    server,
    static_assets=Path(__file__).parent / "static"
)

if __name__ == "__main__":
    app.run()