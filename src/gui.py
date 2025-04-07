#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import markdown
from mdx_math import MathExtension
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                            QSplitter, QFrame, QStyleFactory, QProgressBar,
                            QListWidget, QListWidgetItem, QMenu, QAction, QInputDialog,
                            QMessageBox, QDialog, QLineEdit, QDateEdit, QComboBox, QDialogButtonBox, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QRectF
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPainterPath, QRegion
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 导入flow模块
import flow
# 导入对话管理器
from conversations_manager import ConversationsManager
from datetime import datetime

class RoundedWebEngineView(QWebEngineView):
    def __init__(self, corner_radius=7, parent=None):
        super().__init__(parent)
        self.corner_radius = corner_radius

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # 1. 根据控件的实际大小，创建一个QPainterPath
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        # 2. 将QPainterPath转为QRegion
        region = QRegion(path.toFillPolygon().toPolygon())
        
        # 3. 设置QWebEngineView的蒙版
        self.setMask(region)

# 处理线程
class ProcessingThread(QThread):
    result_ready = pyqtSignal(str)
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self, query, conversation_id=None):
        super().__init__()
        self.query = query
        self.conversation_id = conversation_id
        
    def run(self):
        try:
            # 使用flow.py中的process_query函数处理查询
            # 传入状态和进度回调函数
            result = flow.process_query(
                self.query, 
                status_callback=self.status_update.emit,
                progress_callback=self.progress_update.emit,
                conversation_id=self.conversation_id
            )
            
            # 发送结果信号
            self.result_ready.emit(result)
        except Exception as e:
            self.result_ready.emit(f"错误: {str(e)}")

class LoadingAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.dots = 0
        self.active = False
        self.base_text = "处理中"
        self.setVisible(False)
        
        self.label = QLabel(self.base_text)
        self.label.setStyleSheet("color: #ff7eb3; font-weight: bold;")
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ffcce0;
                border-radius: 5px;
                text-align: center;
                height: 10px;
                background-color: #fff5f8;
            }
            QProgressBar::chunk {
                background-color: #ff9ece;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def start(self):
        self.active = True
        self.setVisible(True)
        self.timer.start(500)
    
    def stop(self):
        self.active = False
        self.timer.stop()
        self.setVisible(False)
    
    def update_animation(self):
        if not self.active:
            return
        
        self.dots = (self.dots + 1) % 4
        self.label.setText(f"{self.base_text}{'.' * self.dots}")
    
    def set_progress(self, value):
        self.progress_bar.setValue(value)

class CesiumRagGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化对话管理器
        self.conversations_manager = ConversationsManager()
        # 当前对话ID
        self.current_conversation_id = None
        
        self.set_style()
        self.initUI()
        
        # 初始化时创建新对话
        self.create_new_conversation()
        
    def set_style(self):
        # 设置应用样式
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        # 自定义调色板 - 清新可爱风格
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 242, 245))  # 淡粉色背景
        palette.setColor(QPalette.WindowText, QColor(90, 90, 90))  # 深灰色文字
        palette.setColor(QPalette.Base, QColor(255, 250, 250))  # 淡白粉色输入框背景
        palette.setColor(QPalette.AlternateBase, QColor(232, 245, 252))  # 淡蓝色交替背景
        palette.setColor(QPalette.ToolTipBase, QColor(255, 240, 245))  # 浅粉色提示背景
        palette.setColor(QPalette.ToolTipText, QColor(90, 90, 90))  # 深灰色提示文字
        palette.setColor(QPalette.Text, QColor(90, 90, 90))  # 深灰色文字
        palette.setColor(QPalette.Button, QColor(210, 230, 255))  # 淡蓝色按钮
        palette.setColor(QPalette.ButtonText, QColor(90, 90, 90))  # 深灰色按钮文字
        palette.setColor(QPalette.BrightText, QColor(255, 105, 180))  # 热粉色强调色
        palette.setColor(QPalette.Link, QColor(147, 196, 250))  # 宝宝蓝链接颜色
        palette.setColor(QPalette.Highlight, QColor(183, 232, 244))  # 浅蓝色高亮颜色
        palette.setColor(QPalette.HighlightedText, QColor(90, 90, 90))  # 深灰色高亮文字
        QApplication.setPalette(palette)
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('Cesium RAG助手')
        self.setMinimumSize(1000, 600)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局 - 使用水平布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧对话历史面板
        history_panel = QWidget()
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        # 历史标题
        history_title = QLabel('对话历史')
        history_title.setAlignment(Qt.AlignCenter)
        history_title_font = QFont()
        history_title_font.setPointSize(14)
        history_title_font.setBold(True)
        history_title.setFont(history_title_font)
        history_layout.addWidget(history_title)
        
        # 添加搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索对话...')
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffecf1;
                color: #5a5a5a;
                border: 1px solid #ffcce0;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_conversations)
        search_layout.addWidget(self.search_input)
        
        # 搜索按钮
        search_button = QPushButton('搜索')
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #ffb6c1;
                color: #5a5a5a;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #ffc8d6;
            }
        """)
        search_button.clicked.connect(self.filter_conversations)
        search_layout.addWidget(search_button)
        
        history_layout.addLayout(search_layout)
        
        # 添加新建对话按钮
        new_conv_button = QPushButton('新建对话')
        new_conv_button.setStyleSheet("""
            QPushButton {
                background-color: #a5dda5;
                color: #5a5a5a;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 5px;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #b8e6b8;
            }
        """)
        new_conv_button.clicked.connect(self.create_new_conversation)
        history_layout.addWidget(new_conv_button)
        
        # 创建对话列表
        self.conversation_list = QListWidget()
        self.conversation_list.setStyleSheet("""
            QListWidget {
                background-color: #fff5f8;
                color: #5a5a5a;
                border: 1px solid #ffcce0;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #ffecf1;
                color: #5a5a5a;
                margin: 5px;
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #ffd6e5;
            }
            QListWidget::item:hover {
                background-color: #ffcce0;
            }
        """)
        self.conversation_list.itemClicked.connect(self.select_conversation)
        self.conversation_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.conversation_list.customContextMenuRequested.connect(self.show_context_menu)
        history_layout.addWidget(self.conversation_list)
        
        # 加载现有对话
        self.load_conversations()
        
        # 主内容区域
        content_panel = QWidget()
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标题标签
        title_label = QLabel('Cesium API 查询助手')
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setFixedHeight(50)  # 设置固定高度为50像素
        content_layout.addWidget(title_label)
        
        # 创建分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(line)
        
        # 当前对话标题
        self.conversation_title_label = QLabel('新对话')
        self.conversation_title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.conversation_title_label.setFont(title_font)
        self.conversation_title_label.setStyleSheet("color: #ff7eb3;")
        self.conversation_title_label.setFixedHeight(40)  # 设置固定高度为40像素
        content_layout.addWidget(self.conversation_title_label)
        
        # 创建输入区域
        input_label = QLabel('请输入您的Cesium相关问题:')
        input_label.setFixedHeight(40)  # 设置固定高度为40像素
        content_layout.addWidget(input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText('在这里输入您的问题...')
        self.input_text.setFixedHeight(100)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffecf1;
                color: #5a5a5a;
                border: 1px solid #ffcce0;
                border-radius: 5px;
                padding: 10px;
                selection-background-color: #ffd6e5;
            }
            QTextEdit::placeholder {
                color: #b0b0b0;
            }
        """)
        content_layout.addWidget(self.input_text)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 添加提交按钮
        self.submit_button = QPushButton('提交问题')
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #a5dda5;
                color: #5a5a5a;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b8e6b8;
            }
            QPushButton:pressed {
                background-color: #93cc93;
            }
            QPushButton:disabled {
                background-color: #e5e5e5;
                color: #a0a0a0;
            }
        """)
        self.submit_button.clicked.connect(self.process_query)
        button_layout.addWidget(self.submit_button)
        
        # 添加清除按钮
        self.clear_button = QPushButton('清除')
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ffb6c1;
                color: #5a5a5a;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffc8d6;
            }
            QPushButton:pressed {
                background-color: #ff9eb6;
            }
        """)
        self.clear_button.clicked.connect(self.clear_input)
        button_layout.addWidget(self.clear_button)
        
        content_layout.addLayout(button_layout)
        
        # 创建加载动画
        self.loading_animation = LoadingAnimation()
        content_layout.addWidget(self.loading_animation)
        
        # 创建对话区域标签
        chat_area_label = QLabel('对话内容:')
        chat_area_label.setFixedHeight(40)  # 设置固定高度为40像素
        content_layout.addWidget(chat_area_label)
        
        # 创建统一的对话显示区域 - 使用QWebEngineView代替QTextBrowser
        self.chat_display = RoundedWebEngineView()
        self.chat_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chat_display.setStyleSheet("background-color: #fafafa; border-radius: 10px;")  # 添加圆角
        content_layout.addWidget(self.chat_display)
        
        # 添加状态指示
        self.status_label = QLabel('就绪')
        self.status_label.setStyleSheet("font-style: italic; color: #ff9eb6;")
        content_layout.addWidget(self.status_label)
        
        # 创建分割器，使左右两个面板可以调整大小
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(history_panel)
        splitter.addWidget(content_panel)
        splitter.setSizes([250, 750])  # 设置初始大小比例
        
        # 将分割器添加到主布局
        main_layout.addWidget(splitter)
        
        # 显示窗口
        self.show()
    
    def process_query(self):
        query = self.input_text.toPlainText().strip()
        if not query:
            self.status_label.setText('请输入问题')
            return
        
        # 检查当前对话是否存在
        if not self.current_conversation_id:
            self.create_new_conversation()
        
        # 更新状态
        self.status_label.setText('处理中...')
        self.submit_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        # 显示加载动画
        self.loading_animation.start()
        
        # 创建处理线程
        self.processing_thread = ProcessingThread(query, self.current_conversation_id)
        self.processing_thread.result_ready.connect(self.update_result)
        self.processing_thread.status_update.connect(self.update_status)
        self.processing_thread.progress_update.connect(self.update_progress)
        self.processing_thread.start()
    
    def update_result(self, result):
        # 停止加载动画
        self.loading_animation.stop()
        
        # 清空输入框并设置焦点，为下一个问题做准备
        self.input_text.clear()
        self.input_text.setFocus()
        
        # 强制重新加载对话数据，确保获取最新内容
        self.conversations_manager.load_conversations()
        
        # 更新对话显示
        if self.current_conversation_id:
            conversation = self.conversations_manager.get_conversation(self.current_conversation_id)
            if conversation:
                # 更新对话标题（如果有变化）
                self.conversation_title_label.setText(conversation.get('title', '未命名对话'))
                # 更新聊天历史显示
                self.update_chat_display(conversation)
                # 更新对话列表（标题可能已更新）
                self.load_conversations()
            else:
                # 如果当前对话不存在（可能已被删除），创建新对话
                self.create_new_conversation()
        
        self.status_label.setText('就绪')
        self.submit_button.setEnabled(True)
        self.clear_button.setEnabled(True)
    
    def update_status(self, status):
        self.status_label.setText(status)
        self.loading_animation.base_text = status
    
    def update_progress(self, value):
        self.loading_animation.set_progress(value)
    
    def clear_input(self):
        self.input_text.clear()
        self.input_text.setFocus()

    def create_new_conversation(self):
        # 检查当前对话是否有消息，如果没有则删除
        if self.current_conversation_id:
            current_conversation = self.conversations_manager.get_conversation(self.current_conversation_id)
            if current_conversation and len(current_conversation.get('messages', [])) == 0:
                # 删除未使用的对话
                self.conversations_manager.delete_conversation(self.current_conversation_id)
                
        # 创建新对话
        self.current_conversation_id = self.conversations_manager.create_new_conversation()
        # 获取新对话信息
        conversation = self.conversations_manager.get_conversation(self.current_conversation_id)
        # 更新UI
        self.conversation_title_label.setText(conversation['title'])
        # 清空聊天显示区域
        self.chat_display.setHtml("<p>还没有对话消息...</p>")
        # 更新对话列表
        self.load_conversations()
        
    def load_conversations(self):
        # 清空列表
        self.conversation_list.clear()
        # 获取所有对话并按创建时间倒序排序
        all_conversations = self.conversations_manager.get_all_conversations()
        all_conversations.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 添加到列表
        for conversation in all_conversations:
            item = QListWidgetItem()
            title = conversation.get('title', '未命名对话')
            created_at = conversation.get('created_at', '')
            if created_at:
                try:
                    # 格式化日期
                    date_obj = datetime.fromisoformat(created_at)
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                    item_text = f"{title}\n{date_str}"
                except:
                    item_text = f"{title}\n{created_at}"
            else:
                item_text = title
                
            # 设置对话ID为项目数据
            item.setData(Qt.UserRole, conversation.get('id'))
            item.setText(item_text)
            self.conversation_list.addItem(item)
            
            # 高亮当前选中的对话
            if conversation.get('id') == self.current_conversation_id:
                self.conversation_list.setCurrentItem(item)
        
        # 检查当前对话是否在列表中，如果不在且有其他对话，则选择第一个
        if self.current_conversation_id and self.conversation_list.count() > 0:
            found = False
            for i in range(self.conversation_list.count()):
                item = self.conversation_list.item(i)
                if item.data(Qt.UserRole) == self.current_conversation_id:
                    found = True
                    break
            
            if not found:
                # 当前对话不在列表中，选择第一个
                self.current_conversation_id = self.conversation_list.item(0).data(Qt.UserRole)
                # 更新UI
                conversation = self.conversations_manager.get_conversation(self.current_conversation_id)
                if conversation:
                    self.conversation_title_label.setText(conversation.get('title', '未命名对话'))
                    self.update_chat_display(conversation)
                    self.conversation_list.setCurrentItem(self.conversation_list.item(0))
    
    def filter_conversations(self):
        search_text = self.search_input.text().strip().lower()
        if not search_text:
            # 如果搜索框为空，显示所有对话
            self.load_conversations()
            return
            
        # 根据搜索文本过滤对话
        filtered_conversations = self.conversations_manager.get_conversation_by_title(search_text)
        
        # 清空列表
        self.conversation_list.clear()
        
        # 添加筛选后的对话到列表
        for conversation in filtered_conversations:
            item = QListWidgetItem()
            title = conversation.get('title', '未命名对话')
            created_at = conversation.get('created_at', '')
            if created_at:
                try:
                    date_obj = datetime.fromisoformat(created_at)
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                    item_text = f"{title}\n{date_str}"
                except:
                    item_text = f"{title}\n{created_at}"
            else:
                item_text = title
                
            item.setData(Qt.UserRole, conversation.get('id'))
            item.setText(item_text)
            self.conversation_list.addItem(item)
    
    def select_conversation(self, item):
        conversation_id = item.data(Qt.UserRole)
        if not conversation_id:
            return
        
        # 检查当前对话是否有消息，如果没有则删除
        if self.current_conversation_id:
            current_conversation = self.conversations_manager.get_conversation(self.current_conversation_id)
            if current_conversation and len(current_conversation.get('messages', [])) == 0:
                # 删除未使用的对话
                self.conversations_manager.delete_conversation(self.current_conversation_id)
            
        # 设置当前对话ID
        self.current_conversation_id = conversation_id
        
        # 获取对话信息
        conversation = self.conversations_manager.get_conversation(conversation_id)
        if not conversation:
            return
            
        # 更新UI
        self.conversation_title_label.setText(conversation.get('title', '未命名对话'))
        
        # 清空输入区域
        self.input_text.clear()
        
        # 更新聊天显示
        self.update_chat_display(conversation)
    
    def update_chat_display(self, conversation):
        # 获取消息
        messages = conversation.get('messages', [])
        
        # 如果没有消息
        if not messages:
            self.chat_display.setHtml("<p>还没有对话消息...</p>")
            return
            
        # 构建HTML内容
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {
                    box-sizing: border-box;
                }
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 10px;
                    background-color: #fafafa;
                }
                .message-container {
                    margin-bottom: 20px;
                    width: 100%;
                    overflow: hidden;
                }
                .user-message { 
                    background-color: #ffecf1;
                    color: #5a5a5a;
                    padding: 10px 15px;
                    border-radius: 8px;
                    margin: 0 20px 0 5px;
                    border: 1px solid #ffcce0;
                    font-family: monospace;
                    white-space: pre-wrap;
                    word-break: break-word;
                    width: calc(100% - 25px);
                    float: right;
                }
                .assistant-message { 
                    background-color: #e8f5e9;
                    color: #5a5a5a;
                    padding: 10px 15px;
                    border-radius: 8px;
                    margin: 0 5px 0 20px;
                    border: 1px solid #c8e6c9;
                    width: calc(100% - 25px);
                    float: left;
                }
                .timestamp {
                    font-size: 0.8em;
                    color: #ff9eb6;
                    margin-top: 3px;
                    text-align: right;
                    clear: both;
                }
                code {
                    background-color: #fff5f8;
                    padding: 0.2em 0.4em;
                    border-radius: 3px;
                    font-family: monospace;
                }
                pre {
                    background-color: #fff5f8;
                    padding: 10px;
                    border-radius: 5px;
                    overflow: auto;
                    margin: 10px 0;
                    border: 1px solid #ffcce0;
                }
                pre code {
                    background-color: transparent;
                    padding: 0;
                }
                ol, ul {
                    padding-left: 20px;
                }
                table {
                    border-collapse: collapse;
                    margin: 10px 0;
                    width: 100%;
                }
                table, th, td {
                    border: 1px solid #ffcce0;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #fff0f5;
                }
            </style>
            <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-AMS_HTML"></script>
            <script type="text/x-mathjax-config">
                MathJax.Hub.Config({
                    tex2jax: {
                        inlineMath: [['$','$'], ['\\(','\\)']],
                        displayMath: [['$$','$$'], ['\\[','\\]']],
                        processEscapes: true
                    }
                });
            </script>
        </head>
        <body>
        """
        
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            # 格式化时间戳
            time_str = ""
            if timestamp:
                try:
                    time_obj = datetime.fromisoformat(timestamp)
                    time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = timestamp
            
            # 内容处理
            if role == 'assistant':
                try:
                    # 仅为assistant消息转换Markdown内容为HTML
                    content_html = markdown.markdown(
                        content,
                        extensions=[
                            'markdown.extensions.tables',
                            'markdown.extensions.fenced_code',
                            'markdown.extensions.codehilite',
                            'markdown.extensions.nl2br',
                            'markdown.extensions.sane_lists',
                            MathExtension(enable_dollar_delimiter=True)
                        ]
                    )
                except:
                    content_html = content
            else:
                # 用户消息显示为纯文本，对特殊HTML字符进行转义，保留原始格式
                content_html = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # 添加消息
            class_name = f"{role}-message"
            html_content += f"""
            <div class="message-container">
                <div class="{class_name}">{content_html}</div>
                <div class="timestamp">{role} · {time_str}</div>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        # 设置HTML内容
        self.chat_display.setHtml(html_content)
        
        # QWebEngineView不需要手动滚动到底部，它会自动处理
    
    def show_context_menu(self, position):
        # 获取当前选中的项
        current_item = self.conversation_list.itemAt(position)
        if not current_item:
            return
            
        # 创建上下文菜单
        menu = QMenu()
        
        # 添加菜单项
        rename_action = QAction("重命名", self)
        delete_action = QAction("删除", self)
        
        # 绑定动作
        rename_action.triggered.connect(lambda: self.rename_conversation(current_item))
        delete_action.triggered.connect(lambda: self.delete_conversation(current_item))
        
        # 添加动作到菜单
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec_(self.conversation_list.mapToGlobal(position))
    
    def rename_conversation(self, item):
        conversation_id = item.data(Qt.UserRole)
        if not conversation_id:
            return
            
        # 获取对话信息
        conversation = self.conversations_manager.get_conversation(conversation_id)
        if not conversation:
            return
            
        # 获取当前标题
        current_title = conversation.get('title', '未命名对话')
        
        # 弹出对话框
        new_title, ok = QInputDialog.getText(
            self, '重命名对话', '请输入新标题:',
            QLineEdit.Normal, current_title
        )
        
        if ok and new_title.strip():
            # 更新标题
            if self.conversations_manager.change_conversation_title_by_id(conversation_id, new_title):
                # 如果是当前对话，更新标题标签
                if conversation_id == self.current_conversation_id:
                    self.conversation_title_label.setText(new_title)
                # 重新加载对话列表
                self.load_conversations()
    
    def delete_conversation(self, item):
        conversation_id = item.data(Qt.UserRole)
        if not conversation_id:
            return
            
        # 获取对话信息
        conversation = self.conversations_manager.get_conversation(conversation_id)
        if not conversation:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, '确认删除',
            f"确定要删除对话 '{conversation.get('title', '未命名对话')}' 吗?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除对话
            if self.conversations_manager.delete_conversation(conversation_id):
                # 如果删除的是当前对话，创建新对话或选择现有对话
                if conversation_id == self.current_conversation_id:
                    # 重新加载对话列表
                    self.load_conversations()
                    # 检查是否还有其他对话
                    if self.conversation_list.count() > 0:
                        # 选择第一个对话
                        first_item = self.conversation_list.item(0)
                        self.select_conversation(first_item)
                    else:
                        # 没有其他对话，创建新对话
                        self.create_new_conversation()
                else:
                    # 重新加载对话列表
                    self.load_conversations()

    def closeEvent(self, event):
        """窗口关闭事件，在关闭前检查并清理未使用的对话"""
        # 检查当前对话是否有消息，如果没有则删除
        if self.current_conversation_id:
            current_conversation = self.conversations_manager.get_conversation(self.current_conversation_id)
            if current_conversation and len(current_conversation.get('messages', [])) == 0:
                # 删除未使用的对话
                self.conversations_manager.delete_conversation(self.current_conversation_id)
        
        # 接受关闭事件
        event.accept()

def main():
    app = QApplication(sys.argv)
    app_icon = QIcon("assets/icon.png")
    app.setWindowIcon(app_icon)
    ex = CesiumRagGUI()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 