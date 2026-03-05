#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口类
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QSplitter, QStatusBar, QStyle, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QSize, QRect, QSharedMemory
from PyQt5.QtGui import QIcon, QColor, QBrush, QPen, QPainter, QRegion

from comfyui_manager.utils.logger import Logger
from comfyui_manager.utils.language_manager import lang_manager
from comfyui_manager.utils.config_manager import config_manager
from comfyui_manager.ui.system_tab import SystemTab
from comfyui_manager.ui.one_click_install_tab import OneClickInstallTab
from comfyui_manager.ui.smart_fix_tab import SmartFixTab
from comfyui_manager.ui.file_management_tab import FileManagementTab
from comfyui_manager.ui.one_click_start_tab import OneClickStartTab
from comfyui_manager.ui.settings_tab import SettingsTab
from comfyui_manager.modules.system_detector import SystemDetector


def check_single_instance():
    """检查是否已经有实例在运行
    
    Returns:
        bool: True表示可以运行（没有实例在运行），False表示已有实例在运行
    """
    # 创建一个共享内存对象
    shared_memory = QSharedMemory("ComfyUI-Manager-Single-Instance")
    
    # 尝试创建共享内存
    if shared_memory.create(1):
        # 成功创建，说明没有实例在运行
        return True
    else:
        # 共享内存已存在，说明已有实例在运行
        return False


class StyleManager:
    """样式管理器"""
    
    @staticmethod
    def get_global_style(theme=1) -> str:
        """获取全局样式
        
        Args:
            theme: 主题类型，0为浅色主题，1为深色主题
        """
        if theme == 0:
            return '''
                QMainWindow {
                    background: #f0f2f5;
                }
            '''
        else:
            return '''
                QMainWindow {
                    background: #12294A;
                }
            '''
    
    @staticmethod
    def get_title_bar_style(theme=1) -> str:
        """获取标题栏样式
        
        Args:
            theme: 主题类型，0为浅色主题，1为深色主题
        """
        if theme == 0:
            return '''
                QWidget {
                    background: #ffffff;
                    border: none;
                    border-bottom: 2px solid rgba(0, 0, 0, 0.1);
                }
                QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton {
                    background: transparent;
                    color: #333333;
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.1);
                    color: #333333;
                }
            '''
        else:
            return '''
                QWidget {
                    background: #12294A;
                    border: none;
                    border-bottom: 2px solid rgba(255, 255, 255, 0.3);
                }
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton {
                    background: transparent;
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.2);
                    color: #ffffff;
                }
            '''
    
    @staticmethod
    def get_sidebar_style(theme=1) -> str:
        """获取侧边栏样式
        
        Args:
            theme: 主题类型，0为浅色主题，1为深色主题
        """
        if theme == 0:
            return '''
                QWidget {
                    background: transparent;
                    color: #333333;
                    border-right: 1px solid rgba(0, 0, 0, 0.1);
                }
            '''
        else:
            return '''
                QWidget {
                    background: transparent;
                    color: #ffffff;
                    border-right: 1px solid rgba(255, 255, 255, 0.3);
                }
            '''
    
    @staticmethod
    def get_button_style(theme=1) -> str:
        """获取按钮样式
        
        Args:
            theme: 主题类型，0为浅色主题，1为深色主题
        """
        if theme == 0:
            return '''
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    color: #333333;
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.1);
                    border-color: rgba(0, 0, 0, 0.3);
                    color: #333333;
                }
                QPushButton:disabled {
                    background: rgba(0, 0, 0, 0.05);
                    color: rgba(0, 0, 0, 0.4);
                    border-color: rgba(0, 0, 0, 0.1);
                }
            '''
        else:
            return '''
                QPushButton {
                    background: rgba(255, 255, 255, 0.2);
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.3);
                    border-color: rgba(255, 255, 255, 0.6);
                    color: #ffffff;
                }
                QPushButton:disabled {
                    background: rgba(255, 255, 255, 0.1);
                    color: rgba(255, 255, 255, 0.6);
                    border-color: rgba(255, 255, 255, 0.2);
                }
            '''
    
    @staticmethod
    def get_active_button_style(theme=1) -> str:
        """获取激活按钮样式
        
        Args:
            theme: 主题类型，0为浅色主题，1为深色主题
        """
        if theme == 0:
            return '''
                QPushButton {
                    background: rgba(25, 118, 210, 0.1);
                    border-color: rgba(25, 118, 210, 0.3);
                    color: #333333;
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 2px 12px rgba(25, 118, 210, 0.2);
                }
            '''
        else:
            return '''
                QPushButton {
                    background: rgba(255, 255, 255, 0.4);
                    border-color: rgba(255, 255, 255, 0.5);
                    color: #ffffff;
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 2px 12px rgba(255, 255, 255, 0.25);
                }
            '''
    
    @staticmethod
    def get_content_area_style(theme=1) -> str:
        """获取内容区域样式
        
        Args:
            theme: 主题类型，0为浅色主题，1为深色主题
        """
        if theme == 0:
            return '''
                QWidget {
                    background: transparent;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                }
                QTextEdit {
                    background: transparent;
                    color: #041a47;
                    border: none;
                    border-radius: 0;
                    padding: 0;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 13px;
                    margin: 0;
                }
                QScrollBar:vertical {
                    background: rgba(0, 0, 0, 0.05);
                    width: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(0, 0, 0, 0.5);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    background: transparent;
                    height: 0;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                QScrollBar:horizontal {
                    background: rgba(0, 0, 0, 0.05);
                    height: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal {
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 5px;
                    min-width: 20px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: rgba(0, 0, 0, 0.5);
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    background: transparent;
                    width: 0;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: transparent;
                }
                QProgressBar {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    border-radius: 4px;
                    padding: 1px;
                    margin-top: 8px;
                }
                QProgressBar::chunk {
                    background: #0077be;
                    border-radius: 3px;
                }
            '''
        else:
            return '''
                QWidget {
                    background: transparent;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QTextEdit {
                    background: transparent;
                    color: #041a47;
                    border: none;
                    border-radius: 0;
                    padding: 0;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 13px;
                    margin: 0;
                }
                QScrollBar:vertical {
                    background: rgba(0, 0, 0, 0.1);
                    width: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 0.6);
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(255, 255, 255, 0.8);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    background: transparent;
                    height: 0;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                QScrollBar:horizontal {
                    background: rgba(0, 0, 0, 0.1);
                    height: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal {
                    background: rgba(255, 255, 255, 0.6);
                    border-radius: 5px;
                    min-width: 20px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: rgba(255, 255, 255, 0.8);
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    background: transparent;
                    width: 0;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: transparent;
                }
                QProgressBar {
                    background: rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    padding: 1px;
                    margin-top: 8px;
                }
                QProgressBar::chunk {
                    background: #0077be;
                    border-radius: 3px;
                }
            '''
    
    @staticmethod
    def get_status_bar_style(theme=1) -> str:
        """获取状态栏样式
        
        Args:
            theme: 主题类型，0为浅色主题，1为深色主题
        """
        if theme == 0:
            return '''
                QStatusBar {
                    background: #ffffff;
                    color: #333333;
                    border-top: 1px solid rgba(0, 0, 0, 0.1);
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
            '''
        else:
            return '''
                QStatusBar {
                    background: #12294A;
                    color: #ffffff;
                    border-top: 1px solid rgba(255, 255, 255, 0.3);
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
            '''


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        """初始化"""
        super().__init__()
        self.logger = Logger()
        self.logger.info("创建主窗口")
        
        # 设置窗口属性
        self.setWindowTitle(lang_manager.get("app_title"))
        self.setGeometry(100, 100, 960, 640)  # 缩小五分之一，从1200x800变为960x640
        self.setMinimumSize(720, 540)  # 相应缩小最小尺寸
        
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 设置窗口图标
        # 由于没有实际图标文件，我们使用Qt的默认图标
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # 窗口拖动变量
        self.dragging = False
        self.drag_position = None
        
        # 点击时间记录，用于防重复点击
        self.last_click_time = {}
        self.click_cooldown = 2  # 点击冷却时间（秒）
        
        # 圆角半径
        self.corner_radius = 12
        
        # 网格大小
        self.grid_size = 20
        
        # 读取主题设置
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        self.theme = 1  # 默认深色主题
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.theme = config.get("theme", 1)
            except Exception as e:
                self.logger.error(f"读取主题设置失败: {e}")
        

        
        # 设置全局样式（添加科技感网格背景）
        self.setStyleSheet(StyleManager.get_global_style(self.theme))
        
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建自定义标题栏
        self.title_bar = self.create_title_bar()
        self.main_layout.addWidget(self.title_bar)
        
        # 创建内容容器
        self.content_container = QWidget()
        self.content_layout = QHBoxLayout(self.content_container)
        
        # 创建侧边栏
        self.sidebar = self.create_sidebar()
        
        # 创建内容区域
        self.content_area = self.create_content_area()
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.content_area)
        self.splitter.setSizes([200, 760])  # 相应调整分割器大小，保持侧边栏宽度不变
        
        # 将分割器添加到内容布局
        self.content_layout.addWidget(self.splitter)
        
        # 将内容容器添加到主布局
        self.main_layout.addWidget(self.content_container, 1)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet(StyleManager.get_status_bar_style(self.theme))
        self.status_bar.showMessage(lang_manager.get("status_ready"))
        
        # 初始化
        self.current_tab = "system"
        
        # 初始化时刷新设置标签页的UI，确保语言正确显示
        if hasattr(self.tab_config.get("settings"), "refresh_ui"):
            self.tab_config["settings"].refresh_ui()
        
        # 显示系统信息标签页
        self.switch_tab("system")
        
        # 检查是否启用了自动运行，如果是则导航到一键启动界面
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if config.get("auto_start", False):
                        self.logger.info("自动运行已启用，导航到一键启动界面")
                        self.switch_tab("one_click_start", skip_validation=True)
        except Exception as e:
            self.logger.error(f"检查自动运行状态失败: {e}")
        
        # 检查是否首次运行
        try:
            if config_manager.get_first_run():
                self.logger.info("首次运行检测: 执行初始化操作")
                
                # 1. 清空日志文件
                self.logger.clear_logs()
                self.logger.info("日志文件已清空")
                
                # 2. 运行系统检测
                self.logger.info("开始系统检测...")
                detector = SystemDetector()
                
                def progress_callback(progress, message):
                    self.status_bar.showMessage(f"系统检测: {message} ({progress}%)")
                
                results = detector.run_complete_detection(progress_callback)
                self.logger.info("系统检测完成")
                
                # 3. 更新系统标签页的检测结果
                if hasattr(self.tab_config.get("system"), "update_detection_results"):
                    self.tab_config["system"].update_detection_results(results)
                
                # 4. 将首次运行标志设置为False
                config_manager.set_first_run(False)
                self.logger.info("首次运行初始化完成")
        except Exception as e:
            self.logger.error(f"首次运行初始化失败: {e}")
    
    def create_title_bar(self):
        """创建自定义标题栏"""
        title_bar = QWidget()
        title_bar.setStyleSheet(StyleManager.get_title_bar_style(self.theme))
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(16, 8, 16, 8)
        
        # 窗口图标和标题
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 16, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(QSize(16, 16)))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(lang_manager.get("app_title"))
        title_layout.addWidget(title_label)
        
        title_bar_layout.addLayout(title_layout)
        
        # 占位符
        title_bar_layout.addStretch()
        
        # 添加垂直隔离线
        separator = QLabel()
        separator.setFixedSize(1, 20)
        separator.setStyleSheet('''
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(25, 118, 210, 0.3), stop:0.5 rgba(25, 118, 210, 0.8), stop:1 rgba(25, 118, 210, 0.3));
                border-radius: 1px;
                margin: 0 16px;
            }
        ''')
        title_bar_layout.addWidget(separator)
        
        # 窗口控制按钮
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 最小化按钮
        self.minimize_button = QPushButton("_")
        self.minimize_button.clicked.connect(lambda: self.handle_minimize())
        control_layout.addWidget(self.minimize_button)
        
        # 最大化/还原按钮
        self.maximize_button = QPushButton("□")
        self.maximize_button.clicked.connect(lambda: self.handle_maximize())
        control_layout.addWidget(self.maximize_button)
        
        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.clicked.connect(lambda: self.handle_close())
        control_layout.addWidget(self.close_button)
        
        title_bar_layout.addLayout(control_layout)
        
        # 启用标题栏拖动
        title_bar.mousePressEvent = self.title_bar_mouse_press_event
        title_bar.mouseMoveEvent = self.title_bar_mouse_move_event
        title_bar.mouseReleaseEvent = self.title_bar_mouse_release_event
        
        return title_bar
    
    def handle_minimize(self):
        """处理最小化按钮点击"""
        if not self.is_click_valid("minimize"):
            return
        self.showMinimized()

    def handle_maximize(self):
        """处理最大化按钮点击"""
        if not self.is_click_valid("maximize"):
            return
        self.toggle_maximize()

    def handle_close(self):
        """处理关闭按钮点击"""
        if not self.is_click_valid("close"):
            return
        self.close()

    def toggle_maximize(self):
        """切换最大化/还原"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_button.setText("□")
        else:
            self.showMaximized()
            self.maximize_button.setText("▢")
    
    def title_bar_mouse_press_event(self, event):
        """标题栏鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def title_bar_mouse_move_event(self, event):
        """标题栏鼠标移动事件"""
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def title_bar_mouse_release_event(self, event):
        """标题栏鼠标释放事件"""
        self.dragging = False
    
    def create_sidebar(self):
        """创建侧边栏"""
        sidebar = QWidget()
        sidebar.setStyleSheet(StyleManager.get_sidebar_style(self.theme))
        sidebar_layout = QVBoxLayout(sidebar)
        
        # 菜单项配置
        self.menu_config = {
            "system": {"name": lang_manager.get("system_info"), "name_key": "system_info", "icon": QStyle.SP_ComputerIcon},
            "one_click_install": {"name": lang_manager.get("one_click_install"), "name_key": "one_click_install", "icon": QStyle.SP_DialogApplyButton},
            "smart_fix": {"name": lang_manager.get("smart_fix"), "name_key": "smart_fix", "icon": QStyle.SP_DialogResetButton},
            "file_management": {"name": lang_manager.get("file_management"), "name_key": "file_management", "icon": QStyle.SP_DirIcon},
            "one_click_start": {"name": lang_manager.get("one_click_start"), "name_key": "one_click_start", "icon": QStyle.SP_ArrowRight},
            "settings": {"name": lang_manager.get("settings"), "name_key": "settings", "icon": QStyle.SP_CustomBase}
        }
        
        # 菜单项
        self.menu_buttons = {}
        
        # 添加菜单项到侧边栏（除了设置按钮）
        for key, config in self.menu_config.items():
            if key != "settings":
                button = QPushButton(config["name"])
                button.clicked.connect(lambda checked, k=key: self.switch_tab(k))
                # 添加图标
                button.setIcon(self.style().standardIcon(config["icon"]))
                button.setIconSize(QSize(16, 16))
                # 设置按钮样式
                button.setStyleSheet(StyleManager.get_button_style(self.theme))
                self.menu_buttons[key] = button
                sidebar_layout.addWidget(button)
        
        # 占位符
        sidebar_layout.addStretch()
        
        # 添加设置按钮到最下端
        if "settings" in self.menu_config:
            config = self.menu_config["settings"]
            button = QPushButton(config["name"])
            button.clicked.connect(lambda checked, k="settings": self.switch_tab(k))
            # 添加图标
            button.setIcon(self.style().standardIcon(config["icon"]))
            button.setIconSize(QSize(16, 16))
            # 设置按钮样式
            button.setStyleSheet(StyleManager.get_button_style(self.theme))
            self.menu_buttons["settings"] = button
            sidebar_layout.addWidget(button)
        
        return sidebar
    
    def create_content_area(self):
        """创建内容区域"""
        content_area = QWidget()
        content_area.setStyleSheet(StyleManager.get_content_area_style(self.theme))
        content_layout = QVBoxLayout(content_area)
        
        # 创建标签栈
        self.tab_stack = QStackedWidget()
        
        # 标签页配置
        self.tab_order = ["system", "one_click_install", "smart_fix", "file_management", "one_click_start", "settings"]
        self.tab_config = {
            "system": SystemTab(),
            "one_click_install": OneClickInstallTab(),
            "smart_fix": SmartFixTab(),
            "file_management": FileManagementTab(),
            "one_click_start": OneClickStartTab(),
            "settings": SettingsTab()
        }
        
        # 添加标签页到栈
        for i, tab_name in enumerate(self.tab_order):
            try:
                tab = self.tab_config[tab_name]
                self.tab_stack.addWidget(tab)
            except Exception as e:
                self.logger.error(f"添加标签页失败: {e}")
        
        # 添加标签栈到内容布局
        content_layout.addWidget(self.tab_stack)
        
        return content_area
    
    def is_click_valid(self, button_id: str) -> bool:
        """检查点击是否有效（防重复点击）
        
        Args:
            button_id: 按钮唯一标识
            
        Returns:
            bool: True表示点击有效，False表示点击无效
        """
        import time
        current_time = time.time()
        last_time = self.last_click_time.get(button_id, 0)
        
        if current_time - last_time < self.click_cooldown:
            # 点击过于频繁，无效
            return False
        
        # 更新点击时间
        self.last_click_time[button_id] = current_time
        return True

    def switch_tab(self, tab_name: str, skip_validation=False):
        """切换标签页"""
        # 检查点击是否有效
        if not skip_validation and not self.is_click_valid(f"tab_{tab_name}"):
            return
            
        try:
            # 刷新语言设置
            lang_manager.refresh_language()
            
            # 更新侧边栏菜单项文本
            for key, button in self.menu_buttons.items():
                if key in self.menu_config:
                    button.setText(lang_manager.get(self.menu_config[key].get("name_key", key)))
            
            self.current_tab = tab_name
            
            # 更新侧边栏按钮状态
            for key, button in self.menu_buttons.items():
                if key == tab_name:
                    button.setStyleSheet(StyleManager.get_active_button_style(self.theme))
                else:
                    button.setStyleSheet(StyleManager.get_button_style(self.theme))
            
            # 切换标签栈
            if hasattr(self, 'tab_order') and hasattr(self, 'tab_stack') and tab_name in self.tab_order:
                # 使用tab_order列表来获取标签页索引，确保与添加顺序一致
                tab_index = self.tab_order.index(tab_name)
                self.logger.info(f"切换到标签 {tab_name}，索引 {tab_index}")
                self.tab_stack.setCurrentIndex(tab_index)
            
            # 更新状态栏消息
            if tab_name == "system":
                self.status_bar.showMessage(lang_manager.get("status_tab_system"))
            elif tab_name == "one_click_install":
                self.status_bar.showMessage(lang_manager.get("status_tab_install"))
            elif tab_name == "smart_fix":
                self.status_bar.showMessage(lang_manager.get("status_tab_fix"))
            elif tab_name == "file_management":
                self.status_bar.showMessage(lang_manager.get("status_tab_file"))
            elif tab_name == "one_click_start":
                self.status_bar.showMessage(lang_manager.get("status_tab_start"))
            elif tab_name == "settings":
                self.status_bar.showMessage(lang_manager.get("status_tab_settings"))
            
            # 记录日志
            self.logger.info(f"切换到标签: {tab_name}")
            
            # 刷新所有标签页的UI以更新语言
            for tab in self.tab_config.values():
                if hasattr(tab, "refresh_ui"):
                    tab.refresh_ui()
            
            # 刷新当前标签页的UI以更新语言
            if hasattr(self.tab_config.get(tab_name), "refresh_ui"):
                self.tab_config[tab_name].refresh_ui()
        except Exception as e:
            self.logger.error(f"切换标签失败: {e}")
            self.status_bar.showMessage(f"切换标签失败: {str(e)}")
    
    def update_all_tabs_path(self, new_path):
        """更新所有标签页的路径"""
        try:
            # 检查路径是否有虚拟环境
            has_venv = self._check_has_virtualenv(new_path)
            self.logger.info(f"路径 {new_path} 是否有虚拟环境: {has_venv}")
            
            for tab_name, tab in self.tab_config.items():
                if hasattr(tab, 'update_path'):
                    # 如果路径没有虚拟环境，智能修复不需要同步，但文件管理需要同步
                    if not has_venv and tab_name == "smart_fix":
                        self.logger.info(f"路径没有虚拟环境，跳过更新标签页 {tab_name}")
                        continue
                    tab.update_path(new_path)
                    self.logger.info(f"更新标签页 {tab_name} 的路径为: {new_path}")
        except Exception as e:
            self.logger.error(f"更新所有标签页路径失败: {e}")
    
    def _check_has_virtualenv(self, path):
        """检查路径是否有虚拟环境"""
        try:
            import os
            # 虚拟环境路径
            install_dir = os.path.dirname(path) if os.path.dirname(path) else path
            venv_path = os.path.join(install_dir, "ComfyUI_venv")
            # 检查虚拟环境是否存在且有效
            venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
            return os.path.exists(venv_python)
        except Exception as e:
            self.logger.error(f"检查虚拟环境失败: {e}")
            return False
    
    def set_rounded_corners(self):
        """设置圆角窗口"""
        try:
            # 获取窗口大小
            size = self.size()
            
            # 创建一个圆角的QRegion
            rect = QRect(0, 0, size.width(), size.height())
            region = QRegion(rect.adjusted(self.corner_radius, 0, -self.corner_radius, 0))
            region |= QRegion(rect.adjusted(0, self.corner_radius, 0, -self.corner_radius))
            
            # 添加四个圆角
            region |= QRegion(0, 0, self.corner_radius * 2, self.corner_radius * 2, QRegion.Ellipse)
            region |= QRegion(size.width() - self.corner_radius * 2, 0, self.corner_radius * 2, self.corner_radius * 2, QRegion.Ellipse)
            region |= QRegion(0, size.height() - self.corner_radius * 2, self.corner_radius * 2, self.corner_radius * 2, QRegion.Ellipse)
            region |= QRegion(size.width() - self.corner_radius * 2, size.height() - self.corner_radius * 2, self.corner_radius * 2, self.corner_radius * 2, QRegion.Ellipse)
            
            # 设置窗口的区域
            self.setMask(region)
        except Exception as e:
            self.logger.error(f"设置圆角窗口失败: {e}")
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        try:
            # 重新设置圆角
            self.set_rounded_corners()
            event.accept()
        except Exception as e:
            self.logger.error(f"窗口大小改变事件处理失败: {e}")
            event.accept()
    
    def paintEvent(self, event):
        """绘制事件, 实现圆角窗口"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制圆角背景（使用网格背景）
            rect = self.rect()
            painter.setPen(Qt.NoPen)
            
            # 绘制基础背景
            if self.theme == 0:
                painter.setBrush(QBrush(QColor(240, 242, 245)))  # 浅色主题背景
            else:
                painter.setBrush(QBrush(QColor(18, 41, 74)))  # #12294A的RGB值（深色主题背景）
            painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
            
            # 绘制网格效果
            if self.theme == 0:
                painter.setPen(QPen(QColor(0, 0, 0, 10), 1))  # 浅色主题使用深色网格
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 15), 1))  # 深色主题使用白色网格
            
            # 绘制垂直线
            for x in range(0, rect.width(), self.grid_size):
                painter.drawLine(x, 0, x, rect.height())
            
            # 绘制水平线
            for y in range(0, rect.height(), self.grid_size):
                painter.drawLine(0, y, rect.width(), y)
            
            event.accept()
        except Exception as e:
            self.logger.error(f"绘制事件处理失败: {e}")
            event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        try:
            # 双击标题栏最大化/还原窗口
            if event.button() == Qt.LeftButton and event.y() < 40:  # 假设标题栏高度为40
                self.toggle_maximize()
            event.accept()
        except Exception as e:
            self.logger.error(f"鼠标双击事件处理失败: {e}")
            event.accept()
    

    
    def closeEvent(self, event):
        """关闭事件"""
        try:
            # 显示确认对话框
            reply = QMessageBox.question(
                self, lang_manager.get("confirm_close"), 
                lang_manager.get("confirm_close_message"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.logger.info("关闭应用程序")
                
                # 停止ComfyUI进程
                try:
                    # 获取一键启动标签页实例
                    one_click_start_tab = self.tab_config.get("one_click_start")
                    if one_click_start_tab and hasattr(one_click_start_tab, "startup_thread"):
                        startup_thread = one_click_start_tab.startup_thread
                        if startup_thread and startup_thread.isRunning():
                            self.logger.info("停止ComfyUI进程...")
                            # 调用停止方法
                            startup_thread.stop()
                            # 等待线程结束
                            startup_thread.terminate()
                            startup_thread.wait()
                            self.logger.info("ComfyUI进程已停止")
                except Exception as e:
                    self.logger.error(f"停止ComfyUI进程失败: {e}")
                
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            self.logger.error(f"关闭事件处理失败: {e}")
            event.accept()


# 测试代码
if __name__ == "__main__":
    import sys
    
    # 检查是否已经有实例在运行
    if not check_single_instance():
        # 已有实例在运行，显示提示并退出
        app = QApplication(sys.argv)
        QMessageBox.warning(None, lang_manager.get("already_running"), lang_manager.get("already_running_message"))
        sys.exit(0)
    
    # 没有实例在运行，继续启动
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())