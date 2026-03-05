#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理标签页
"""

import os
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar,
    QLabel, QLineEdit, QFileDialog, QTreeWidget, QTreeWidgetItem, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from comfyui_manager.utils.logger import Logger
from comfyui_manager.utils.language_manager import lang_manager


class FileManagementTab(QWidget):
    """文件管理标签页"""
    
    def __init__(self, parent=None):
        """初始化"""
        super().__init__(parent)
        self.logger = Logger()
        # 点击时间记录，用于防重复点击
        self.last_click_time = {}
        self.click_cooldown = 2  # 点击冷却时间（秒）
        # 加载保存的安装路径
        self.install_path = self.load_install_path()
        # 当前浏览的路径
        self.current_path = None
        # 初始化定时器用于自动刷新
        from PyQt5.QtCore import QTimer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_files)
        self.refresh_timer.start(5000)  # 每5秒自动刷新一次
        self.init_ui()
    
    def load_install_path(self):
        """加载保存的安装路径"""
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("install_path", "C:\\ComfyUI")
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
        return "C:\\ComfyUI"
    
    def save_install_path(self):
        """保存安装路径到配置文件"""
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        try:
            # 读取现有配置
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            
            # 更新安装路径
            config["install_path"] = self.install_path
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"保存安装路径到配置文件: {self.install_path}")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def on_path_text_changed(self, text):
        """路径文本变化时调用"""
        self.path_changed = True
        self.browse_button.setText("保存")
        self.browse_button.disconnect()
        self.browse_button.clicked.connect(self.save_path)
        self.logger.info(f"路径文本变化: {text}")
    
    def update_path(self, new_path):
        """更新路径"""
        try:
            self.install_path = new_path
            self.path_edit.setText(self.install_path)
            self.refresh_files()
            self.logger.info(f"更新路径为: {self.install_path}")
        except Exception as e:
            self.logger.error(f"更新路径失败: {e}")
    
    def _handle_button_click(self, button, callback):
        """处理按钮点击事件，实现高亮功能
        
        Args:
            button: 被点击的按钮
            callback: 原始的点击处理函数
        """
        # 重置当前高亮按钮的样式
        if self.current_highlighted_button:
            self.current_highlighted_button.setStyleSheet("")
        
        # 为当前点击的按钮设置高亮样式
        button.setStyleSheet(self.highlighted_button_style)
        
        # 更新当前高亮按钮
        self.current_highlighted_button = button
        
        # 调用原始的点击处理函数
        callback()
    
    def refresh_ui(self):
        """刷新UI，更新语言"""
        try:
            # 刷新语言设置
            lang_manager.refresh_language()
            
            # 更新路径标签和按钮
            for widget in self.findChildren(QLabel):
                if widget.text() == "选择路径" or widget.text() == "Select Path":
                    widget.setText(lang_manager.get("select_path"))
            
            # 更新浏览按钮文本
            self.browse_button.setText(lang_manager.get("browse"))
            
            # 更新功能按钮文本
            self.workflow_button.setText(lang_manager.get("workflows"))
            self.models_button.setText(lang_manager.get("models"))
            self.works_button.setText(lang_manager.get("works"))
            
            # 更新文件树表头
            if hasattr(self, 'file_tree'):
                self.file_tree.setHeaderLabels([lang_manager.get("filename"), lang_manager.get("size"), lang_manager.get("modify_time")])
            
            self.logger.info("文件管理标签页UI已刷新")
        except Exception as e:
            self.logger.error(f"刷新UI失败: {e}")
    
    def save_path(self):
        """保存安装路径"""
        try:
            # 保存路径
            new_path = self.path_edit.text().strip()
            if new_path:
                self.install_path = new_path
                self.save_install_path()
                self.refresh_files()
                self.logger.info(f"保存路径: {self.install_path}")
                
                # 检查ComfyUI是否安装
                comfyui_path = os.path.join(self.install_path, "ComfyUI")
                if not os.path.exists(comfyui_path):
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("no_comfyui_warning"))
                    self.logger.info("路径下未安装ComfyUI，弹出提示信息")
                
                # 恢复按钮状态
                self.path_changed = False
                self.browse_button.setText("浏览")
                self.browse_button.disconnect()
                self.browse_button.clicked.connect(self.browse_path)
                # 通知主窗口更新所有标签页的路径
                from PyQt5.QtWidgets import QApplication
                main_window = QApplication.instance().activeWindow()
                if main_window and hasattr(main_window, 'update_all_tabs_path'):
                    main_window.update_all_tabs_path(new_path)
                    self.logger.info(f"通知主窗口更新所有标签页路径为: {new_path}")
        except Exception as e:
            self.logger.error(f"保存路径失败: {e}")
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 初始化样式
        self._init_styles()
        
        # 设置样式
        self.setStyleSheet(self.widget_style)
        
        # 安装路径
        path_container = QWidget()
        path_layout = QHBoxLayout(path_container)
        path_layout.setContentsMargins(0, 0, 0, 16)
        
        path_label = QLabel(lang_manager.get("select_path"))
        self.path_edit = QLineEdit()
        self.path_edit.setText(self.install_path)
        # 保存按钮状态
        self.path_changed = False
        self.browse_button = QPushButton(lang_manager.get("browse"))
        self.browse_button.clicked.connect(self.browse_path)
        # 连接文本变化信号
        self.path_edit.textChanged.connect(self.on_path_text_changed)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit, 1)
        path_layout.addWidget(self.browse_button)
        
        layout.addWidget(path_container)
        
        # 二级功能按钮容器
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 16)
        
        # 存储当前高亮的按钮
        self.current_highlighted_button = None
        
        # 工作流按钮
        self.workflow_button = QPushButton(lang_manager.get("workflows"))
        self.workflow_button.clicked.connect(lambda: self._handle_button_click(self.workflow_button, self.manage_workflows))
        buttons_layout.addWidget(self.workflow_button)
        
        # 模型文件按钮
        self.models_button = QPushButton(lang_manager.get("models"))
        self.models_button.clicked.connect(lambda: self._handle_button_click(self.models_button, self.manage_models))
        buttons_layout.addWidget(self.models_button)
        
        # 个人作品按钮
        self.works_button = QPushButton(lang_manager.get("works"))
        self.works_button.clicked.connect(lambda: self._handle_button_click(self.works_button, self.manage_works))
        buttons_layout.addWidget(self.works_button)
        
        layout.addWidget(buttons_container)
        
        # 文件浏览区域
        file_container = QWidget()
        file_layout = QVBoxLayout(file_container)
        file_layout.setContentsMargins(12, 12, 12, 12)
        
        # 文件树
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels([lang_manager.get("filename"), lang_manager.get("size"), lang_manager.get("modify_time")])
        self.file_tree.setStyleSheet(self.tree_style)
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        file_layout.addWidget(self.file_tree, 1)
        

        
        # 设置容器样式
        file_container.setStyleSheet(self.container_style)
        
        layout.addWidget(file_container, 1)
    
    def _init_styles(self):
        """初始化样式"""
        # 获取当前主题
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        current_theme = 1  # 默认深色主题
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    current_theme = config.get("theme", 1)
            except Exception as e:
                self.logger.error(f"读取主题设置失败: {e}")
        
        if current_theme == 0:  # 浅色主题
            # 组件样式
            self.widget_style = """
                QWidget {
                    background: transparent;
                    color: #333333;
                }
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
                QLabel {
                    color: #333333;
                    font-size: 14px;
                    margin-right: 12px;
                }
                QLineEdit {
                    background: rgba(0, 0, 0, 0.05);
                    color: #333333;
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                }
            """
            # 高亮按钮样式
            self.highlighted_button_style = """
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
            """
        else:  # 深色主题
            # 组件样式
            self.widget_style = """
                QWidget {
                    background: transparent;
                    color: #ffffff;
                }
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
                }
                QPushButton:disabled {
                    background: rgba(255, 255, 255, 0.1);
                    color: rgba(255, 255, 255, 0.6);
                    border-color: rgba(255, 255, 255, 0.2);
                }
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    margin-right: 12px;
                }
                QLineEdit {
                    background: rgba(255, 255, 255, 0.2);
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                }
            """
            # 高亮按钮样式
            self.highlighted_button_style = """
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
            """
        
        # 树控件样式
        if current_theme == 0:  # 浅色主题
            self.tree_style = """
                QTreeWidget {
                    background: transparent;
                    color: #041a47;
                    border: none;
                    border-radius: 0;
                    padding: 0;
                    font-size: 13px;
                    margin: 0;
                }
                QTreeWidget::item {
                    padding: 4px;
                }
                QTreeWidget::item:hover {
                    background: rgba(0, 119, 190, 0.1);
                }
                QTreeWidget::item:selected {
                    background: rgba(0, 119, 190, 0.2);
                }
                QHeaderView {
                    background: rgba(0, 0, 0, 0.1);
                    color: #041a47;
                    font-weight: 500;
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
            """
        else:  # 深色主题
            self.tree_style = """
                QTreeWidget {
                    background: transparent;
                    color: #041a47;
                    border: none;
                    border-radius: 0;
                    padding: 0;
                    font-size: 13px;
                    margin: 0;
                }
                QTreeWidget::item {
                    padding: 4px;
                }
                QTreeWidget::item:hover {
                    background: rgba(0, 119, 190, 0.1);
                }
                QTreeWidget::item:selected {
                    background: rgba(0, 119, 190, 0.2);
                }
                QHeaderView {
                    background: rgba(0, 0, 0, 0.1);
                    color: #041a47;
                    font-weight: 500;
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
            """
        
        # 树控件样式
        self.tree_style = """
            QTreeWidget {
                background: transparent;
                color: #041a47;
                border: none;
                border-radius: 0;
                padding: 0;
                font-size: 13px;
                margin: 0;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background: rgba(0, 119, 190, 0.1);
            }
            QTreeWidget::item:selected {
                background: rgba(0, 119, 190, 0.2);
            }
            QHeaderView {
                background: rgba(0, 0, 0, 0.1);
                color: #041a47;
                font-weight: 500;
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
        """
        
        # 容器样式
        self.container_style = """
            QWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(25, 118, 210, 0.4);
                border-radius: 8px;
            }
        """
    
    def is_click_valid(self, button_id):
        """检查点击是否有效（防重复点击）
        
        Args:
            button_id: 按钮唯一标识
            
        Returns:
            bool: True表示点击有效，False表示点击无效
        """
        current_time = time.time()
        last_time = self.last_click_time.get(button_id, 0)
        
        if current_time - last_time < self.click_cooldown:
            # 点击过于频繁，无效
            self.logger.info(f"点击过于频繁，{button_id} 按钮在 {self.click_cooldown} 秒内不可重复点击")
            return False
        
        # 更新点击时间
        self.last_click_time[button_id] = current_time
        self.logger.info(f"点击有效，更新 {button_id} 按钮的点击时间为 {current_time}")
        return True
    
    def browse_path(self):
        """浏览安装路径"""
        try:
            directory = QFileDialog.getExistingDirectory(self, lang_manager.get("select_path"), self.install_path)
            if directory:
                self.install_path = directory
                self.path_edit.setText(self.install_path)
                self.path_changed = True
                self.browse_button.setText(lang_manager.get("save"))
                self.browse_button.disconnect()
                self.browse_button.clicked.connect(self.save_path)
                self.logger.info(f"选择路径: {self.install_path}")
        except Exception as e:
            self.logger.error(f"浏览路径失败: {e}")
    
    def manage_workflows(self):
        """管理工作流"""
        if not self.is_click_valid("manage_workflows"):
            return
        
        try:
            self.logger.info("开始管理工作流")
            # 工作流路径
            comfyui_path = os.path.join(self.install_path, "ComfyUI")
            # 使用 user\default 目录
            workflows_path = os.path.join(comfyui_path, "user", "default")
            
            self.logger.info(f"ComfyUI路径: {comfyui_path}")
            self.logger.info(f"工作流路径: {workflows_path}")
            
            # 检查路径是否有效
            if not self.install_path or not os.path.exists(self.install_path):
                self.logger.error("安装路径无效")
                return
            
            # 检查ComfyUI是否安装
            if not os.path.exists(comfyui_path):
                self.logger.error("ComfyUI未安装，无法管理工作流")
                return
            
            if not os.path.exists(workflows_path):
                try:
                    os.makedirs(workflows_path, exist_ok=True)
                    self.logger.info(f"创建工作流目录: {workflows_path}")
                except Exception as e:
                    self.logger.error(f"创建工作流目录失败: {e}")
                    return
            
            # 刷新文件列表
            self.load_files(workflows_path)
        except Exception as e:
            self.logger.error(f"管理工作流失败: {e}")
    
    def manage_models(self):
        """管理模型文件"""
        if not self.is_click_valid("manage_models"):
            return
        
        try:
            self.logger.info("开始管理模型文件")
            # 模型路径
            comfyui_path = os.path.join(self.install_path, "ComfyUI")
            models_path = os.path.join(comfyui_path, "models")
            self.logger.info(f"ComfyUI路径: {comfyui_path}")
            self.logger.info(f"模型文件路径: {models_path}")
            
            # 检查路径是否有效
            if not self.install_path or not os.path.exists(self.install_path):
                self.logger.error("安装路径无效")
                return
            
            # 检查ComfyUI是否安装
            if not os.path.exists(comfyui_path):
                self.logger.error("ComfyUI未安装，无法管理模型文件")
                return
            
            if not os.path.exists(models_path):
                try:
                    os.makedirs(models_path, exist_ok=True)
                    self.logger.info(f"创建模型目录: {models_path}")
                except Exception as e:
                    self.logger.error(f"创建模型目录失败: {e}")
                    return
            
            # 刷新文件列表
            self.load_files(models_path)
        except Exception as e:
            self.logger.error(f"管理模型文件失败: {e}")
    
    def manage_works(self):
        """管理个人作品"""
        if not self.is_click_valid("manage_works"):
            return
        
        try:
            self.logger.info("开始管理个人作品")
            # 个人作品路径
            comfyui_path = os.path.join(self.install_path, "ComfyUI")
            works_path = os.path.join(comfyui_path, "output")
            self.logger.info(f"ComfyUI路径: {comfyui_path}")
            self.logger.info(f"个人作品路径: {works_path}")
            
            # 检查路径是否有效
            if not self.install_path or not os.path.exists(self.install_path):
                self.logger.error("安装路径无效")
                return
            
            # 检查ComfyUI是否安装
            if not os.path.exists(comfyui_path):
                self.logger.error("ComfyUI未安装，无法管理个人作品")
                return
            
            if not os.path.exists(works_path):
                try:
                    os.makedirs(works_path, exist_ok=True)
                    self.logger.info(f"创建个人作品目录: {works_path}")
                except Exception as e:
                    self.logger.error(f"创建个人作品目录失败: {e}")
                    return
            
            # 刷新文件列表
            self.load_files(works_path)
        except Exception as e:
            self.logger.error(f"管理个人作品失败: {e}")
    
    def refresh_files(self):
        """刷新文件列表"""
        if not self.is_click_valid("refresh_files"):
            return
        
        try:
            self.logger.info("刷新文件列表")
            # 加载当前路径的文件
            self.load_files(self.install_path)
        except Exception as e:
            self.logger.error(f"刷新文件列表失败: {e}")
    
    def load_files(self, path):
        """加载文件到树控件"""
        try:
            # 记录当前浏览的路径
            self.current_path = path
            
            # 清空树控件
            self.file_tree.clear()
            
            # 检查路径是否存在
            if not os.path.exists(path):
                self.logger.error(f"路径不存在: {path}")
                return
            
            # 检查路径是否是目录
            if not os.path.isdir(path):
                self.logger.error(f"路径不是目录: {path}")
                return
            
            # 创建根节点
            root_item = QTreeWidgetItem(self.file_tree, [os.path.basename(path) or path, "", ""])
            root_item.setData(0, Qt.UserRole, path)
            
            # 加载文件（限制深度，防止栈溢出）
            self.add_files_to_tree(root_item, path, max_depth=3)
            
            # 展开根节点
            root_item.setExpanded(True)
            
            # 自动调整列宽
            self.file_tree.resizeColumnToContents(0)  # 调整文件名列宽
            self.file_tree.resizeColumnToContents(1)  # 调整大小列宽
            self.file_tree.resizeColumnToContents(2)  # 调整修改时间列宽
        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
    
    def add_files_to_tree(self, parent_item, path, max_depth=3, current_depth=0):
        """递归添加文件到树控件（带深度限制）"""
        try:
            # 检查深度限制
            if current_depth >= max_depth:
                return
            
            # 限制文件数量，防止系统崩溃
            items = os.listdir(path)[:100]  # 最多显示100个文件/目录
            
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    # 目录
                    dir_item = QTreeWidgetItem(parent_item, [item, "", ""])
                    dir_item.setData(0, Qt.UserRole, item_path)
                    # 递归添加子文件
                    self.add_files_to_tree(dir_item, item_path, max_depth, current_depth + 1)
                else:
                    # 文件
                    size = os.path.getsize(item_path)
                    mtime = os.path.getmtime(item_path)
                    mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
                    file_item = QTreeWidgetItem(parent_item, [item, f"{size} bytes", mtime_str])
                    file_item.setData(0, Qt.UserRole, item_path)
        except Exception as e:
            self.logger.error(f"添加文件到树失败: {e}")
    
    def open_file(self):
        """打开选中的文件或目录"""
        try:
            selected_items = self.file_tree.selectedItems()
            if not selected_items:
                return
            
            item = selected_items[0]
            file_path = item.data(0, Qt.UserRole)
            
            if os.path.isdir(file_path):
                # 打开目录
                import subprocess
                if os.name == "nt":
                    subprocess.run(["explorer", file_path], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["open", file_path])
            else:
                # 打开文件
                import subprocess
                if os.name == "nt":
                    os.startfile(file_path)
                else:
                    subprocess.run(["open", file_path])
        except Exception as e:
            self.logger.error(f"打开文件失败: {e}")
    
    def delete_file(self):
        """删除选中的文件或目录"""
        try:
            selected_items = self.file_tree.selectedItems()
            if not selected_items:
                return
            
            item = selected_items[0]
            file_path = item.data(0, Qt.UserRole)
            
            # 显示确认对话框
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, lang_manager.get("confirm_delete"), 
                f"{lang_manager.get('confirm_delete_message_file').format(filename=os.path.basename(file_path))}",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import shutil
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                
                # 刷新文件列表
                parent_item = item.parent()
                if parent_item:
                    parent_path = parent_item.data(0, Qt.UserRole)
                    self.load_files(parent_path)
                else:
                    self.refresh_files()
        except Exception as e:
            self.logger.error(f"删除文件失败: {e}")
    
    def auto_refresh_files(self):
        """自动刷新文件列表"""
        try:
            if self.current_path:
                # 重新加载当前路径的文件
                self.load_files(self.current_path)
                self.logger.info(f"自动刷新文件列表: {self.current_path}")
        except Exception as e:
            self.logger.error(f"自动刷新文件列表失败: {e}")
    
    def on_item_double_clicked(self, item, column):
        """处理双击事件，打开文件夹或文件"""
        try:
            file_path = item.data(0, Qt.UserRole)
            self.logger.info(f"双击打开: {file_path}")
            
            if os.path.isdir(file_path):
                # 打开目录
                import subprocess
                if os.name == "nt":
                    # 直接打开目录
                    self.logger.info(f"使用explorer打开目录: {file_path}")
                    # 确保路径是绝对路径
                    abs_path = os.path.abspath(file_path)
                    self.logger.info(f"绝对路径: {abs_path}")
                    # 直接使用explorer命令打开目录
                    subprocess.run(["explorer", abs_path], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["open", file_path])
            else:
                # 打开文件
                import subprocess
                if os.name == "nt":
                    os.startfile(file_path)
                else:
                    subprocess.run(["open", file_path])
        except Exception as e:
            self.logger.error(f"双击打开文件失败: {e}")
