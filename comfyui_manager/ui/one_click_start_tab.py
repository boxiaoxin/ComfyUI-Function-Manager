#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键启动标签页
"""

import os
import time
import subprocess
import threading
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar,
    QLabel, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from comfyui_manager.utils.logger import Logger
from comfyui_manager.utils.language_manager import lang_manager


class StartComfyUIThread(QThread):
    """启动ComfyUI线程"""
    update_progress = pyqtSignal(int, str)
    update_log = pyqtSignal(str)
    start_finished = pyqtSignal(dict)
    
    def __init__(self, install_path):
        super().__init__()
        self.install_path = install_path
        self.process = None
    
    def run(self):
        """运行启动ComfyUI"""
        try:
            results = {
                "status": "success",
                "message": "ComfyUI启动成功"
            }
            
            # 导入必要的模块
            import time
            import webbrowser
            import re
            import socket
            import psutil
            
            # 发送开始进度
            self.update_progress.emit(0, "开始启动ComfyUI...")
            
            # 直接使用安装路径作为基础路径
            install_dir = self.install_path
            
            # 检查路径是否存在
            if not os.path.exists(install_dir):
                raise Exception(f"安装路径不存在: {install_dir}")
            
            # 检查虚拟环境是否存在于当前目录
            venv_path = os.path.join(install_dir, "ComfyUI_venv")
            self.update_log.emit(f"虚拟环境路径: {venv_path}")
            
            # 检查虚拟环境是否存在
            if not os.path.exists(venv_path):
                # 尝试在父目录查找虚拟环境
                parent_dir = os.path.dirname(install_dir)
                # 确保父目录不是空字符串且与当前目录不同
                if parent_dir and parent_dir != install_dir and os.path.exists(parent_dir):
                    venv_path = os.path.join(parent_dir, "ComfyUI_venv")
                    self.update_log.emit(f"在父目录查找虚拟环境: {venv_path}")
                    if not os.path.exists(venv_path):
                        # 尝试在当前目录直接查找虚拟环境（不限制名称）
                        for item in os.listdir(install_dir):
                            item_path = os.path.join(install_dir, item)
                            if os.path.isdir(item_path) and ("venv" in item.lower() or "env" in item.lower()):
                                venv_path = item_path
                                self.update_log.emit(f"在当前目录找到虚拟环境: {venv_path}")
                                break
                        if not os.path.exists(venv_path):
                            raise Exception("虚拟环境不存在，请先创建环境")
                else:
                    # 尝试在当前目录直接查找虚拟环境（不限制名称）
                    for item in os.listdir(install_dir):
                        item_path = os.path.join(install_dir, item)
                        if os.path.isdir(item_path) and ("venv" in item.lower() or "env" in item.lower()):
                            venv_path = item_path
                            self.update_log.emit(f"在当前目录找到虚拟环境: {venv_path}")
                            break
                    if not os.path.exists(venv_path):
                        raise Exception("虚拟环境不存在，请先创建环境")
            
            # 获取虚拟环境中的Python可执行文件路径
            if os.name == "nt":
                # 在Windows系统下使用pythonw.exe来避免命令提示符窗口
                venv_python = os.path.join(venv_path, "Scripts", "pythonw.exe")
                # 如果pythonw.exe不存在，回退到python.exe
                if not os.path.exists(venv_python):
                    venv_python = os.path.join(venv_path, "Scripts", "python.exe")
            else:
                venv_python = os.path.join(venv_path, "bin", "python")
            if not os.path.exists(venv_python):
                raise Exception("虚拟环境中未找到Python可执行文件")
            self.update_log.emit(f"使用虚拟环境Python: {venv_python}")
            
            # 检查ComfyUI是否存在于当前目录
            comfyui_path = os.path.join(install_dir, "ComfyUI")
            self.update_log.emit(f"ComfyUI安装路径: {comfyui_path}")
            
            # 检查ComfyUI是否存在
            if not os.path.exists(comfyui_path):
                # 尝试在父目录查找ComfyUI
                parent_dir = os.path.dirname(install_dir)
                # 确保父目录不是空字符串且与当前目录不同
                if parent_dir and parent_dir != install_dir and os.path.exists(parent_dir):
                    comfyui_path = os.path.join(parent_dir, "ComfyUI")
                    self.update_log.emit(f"在父目录查找ComfyUI: {comfyui_path}")
                    if not os.path.exists(comfyui_path):
                        raise Exception("ComfyUI未安装，请先安装ComfyUI")
                else:
                    raise Exception("ComfyUI未安装，请先安装ComfyUI")
            
            # 检查main.py文件是否存在
            main_py = os.path.join(comfyui_path, "main.py")
            if not os.path.exists(main_py):
                raise Exception("ComfyUI main.py文件不存在")
            
            # 启动ComfyUI
            self.update_progress.emit(40, "启动ComfyUI...")
            
            # 检查并清理占用8188端口的进程
            self.update_progress.emit(45, "检查端口8188是否被占用...")
            def check_port(port):
                sock = None
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("127.0.0.1", port))
                    return result == 0
                finally:
                    if sock:
                        sock.close()
            
            def kill_process_using_port(port):
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        for conn in proc.connections(kind='inet'):
                            if conn.laddr.port == port:
                                self.update_log.emit(f"找到占用端口{port}的进程: {proc.name()} (PID: {proc.pid})")
                                proc.terminate()
                                try:
                                    proc.wait(timeout=5)
                                    self.update_log.emit(f"已终止占用端口{port}的进程")
                                    return True
                                except psutil.TimeoutExpired:
                                    proc.kill()
                                    self.update_log.emit(f"已强制终止占用端口{port}的进程")
                                    return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                return False
            
            # 检查端口8188
            if check_port(8188):
                self.update_log.emit("端口8188已被占用，尝试清理...")
                kill_process_using_port(8188)
                # 等待一段时间让端口释放
                time.sleep(2)
            
            # 启动ComfyUI进程
            self.update_progress.emit(60, "正在启动ComfyUI进程...")
            # 使用标准方式启动进程，以便读取输出
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            self.process = subprocess.Popen(
                [venv_python, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                cwd=comfyui_path,
                creationflags=creationflags
            )
            
            # 读取输出并查找启动信息
            server_url = None
            startup_complete = False
            start_time = time.time()
            timeout = 60  # 60秒超时
            
            while time.time() - start_time < timeout:
                line = self.process.stdout.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                # 输出启动日志
                line = line.strip()
                self.update_log.emit(line)
                
                # 查找服务器URL
                if "Starting server" in line:
                    # 等待下一行获取服务器地址
                    continue
                elif "To see the GUI go to" in line:
                    match = re.search(r"To see the GUI go to:? (http://[^\s]+)", line)
                    if match:
                        server_url = match.group(1)
                        self.update_progress.emit(80, f"ComfyUI服务器启动成功，地址: {server_url}")
                        
                        # 打开浏览器
                        self.update_progress.emit(90, "打开浏览器界面...")
                        webbrowser.open(server_url)
                        self.update_progress.emit(95, "浏览器已打开")
                        startup_complete = True
                        break
                elif "Running on" in line:
                    match = re.search(r'Running on (http://[^\"]+)', line)
                    if match:
                        server_url = match.group(1)
                        self.update_progress.emit(80, f"ComfyUI服务器启动成功，地址: {server_url}")
                        
                        # 打开浏览器
                        self.update_progress.emit(90, "打开浏览器界面...")
                        webbrowser.open(server_url)
                        self.update_progress.emit(95, "浏览器已打开")
                        startup_complete = True
                        break
                
                # 检查是否有错误，但忽略日志文件占用的错误
                if "error" in line.lower() or "exception" in line.lower():
                    # 忽略日志文件占用的错误
                    if "WinError 32" in line and "另一个程序正在使用此文件" in line:
                        self.update_log.emit("警告: 日志文件被占用，但不影响启动")
                    # 处理端口占用错误
                    elif "OSError: [Errno 10048]" in line or "WinError 10048" in line:
                        raise Exception("ComfyUI启动失败: 端口8188已被占用，请关闭占用该端口的进程后重试")
                    else:
                        raise Exception(f"ComfyUI启动失败: {line}")
            
            if not startup_complete:
                raise Exception("ComfyUI启动失败，未找到服务器地址")
            
            self.update_progress.emit(100, "ComfyUI启动完成")
            self.start_finished.emit(results)
            
            # 持续读取ComfyUI控制台输出
            while True:
                line = self.process.stdout.readline()
                if not line:
                    # 进程可能已经结束
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue
                
                # 输出控制台日志
                line = line.strip()
                self.update_log.emit(line)
        except Exception as e:
            # 发送错误信息
            self.start_finished.emit({"status": "error", "message": str(e)})
    
    def stop(self):
        """停止ComfyUI进程"""
        if self.process:
            try:
                # 先尝试终止进程
                self.process.terminate()
                # 等待进程结束
                try:
                    self.process.wait(timeout=5)
                    self.update_log.emit("ComfyUI进程已停止")
                except subprocess.TimeoutExpired:
                    # 超时后强制杀死进程
                    self.process.kill()
                    self.update_log.emit("ComfyUI进程已强制停止")
            except Exception as e:
                self.update_log.emit(f"停止ComfyUI进程失败: {e}")


class OneClickStartTab(QWidget):
    """一键启动标签页"""
    
    def __init__(self, parent=None):
        """初始化"""
        super().__init__(parent)
        self.logger = Logger()
        self.startup_thread = None
        self.is_auto_start = False
        # 点击时间记录，用于防重复点击
        self.last_click_time = {}
        self.click_cooldown = 2  # 点击冷却时间（秒）
        # 加载保存的安装路径
        self.install_path = self.load_install_path()
        self.init_ui()
        # 设置启动按钮状态
        self.start_button.setEnabled(not self.is_auto_start)
        # 自动启动ComfyUI（如果启用了自动运行）
        if self.is_auto_start:
            self.auto_start_button.setText("取消自动")
            self.logger.info("自动运行已开启，准备启动ComfyUI")
            # 延迟启动，确保UI完全初始化
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self.start_comfyui)
    
    def load_install_path(self):
        """加载保存的安装路径"""
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # 加载自动运行状态
                    if "auto_start" in config:
                        self.is_auto_start = config["auto_start"]
                    return config.get("install_path", "C:\\ComfyUI")
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
        return "C:\\ComfyUI"
    
    def save_install_path(self, path):
        """保存安装路径"""
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        try:
            # 确保配置文件所在目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            # 读取现有配置
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            # 更新安装路径
            config["install_path"] = path
            # 保存自动运行状态
            config["auto_start"] = self.is_auto_start
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
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
        
        # 启动按钮
        self.start_button = QPushButton(lang_manager.get("click_start"))
        self.start_button.clicked.connect(self.start_comfyui)
        buttons_layout.addWidget(self.start_button)
        
        # 自动运行按钮
        self.auto_start_button = QPushButton(lang_manager.get("auto_run"))
        self.auto_start_button.clicked.connect(self.toggle_auto_start)
        buttons_layout.addWidget(self.auto_start_button)
        
        # 停止按钮
        self.stop_button = QPushButton(lang_manager.get("stop"))
        self.stop_button.clicked.connect(self.stop_comfyui)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)
        
        layout.addWidget(buttons_container)
        
        # 启动日志
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(12, 12, 12, 12)
        
        # 日志内容
        self.start_log = QTextEdit()
        self.start_log.setReadOnly(True)
        self.start_log.setMinimumHeight(300)
        self.start_log.setStyleSheet(self.text_edit_style)
        log_layout.addWidget(self.start_log, 1)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setStyleSheet(self.progress_bar_style)
        log_layout.addWidget(self.progress_bar)
        
        # 设置容器样式
        log_container.setStyleSheet(self.container_style)
        
        layout.addWidget(log_container, 1)
    
    def _init_styles(self):
        """初始化样式"""
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
        
        # 文本编辑框样式
        self.text_edit_style = """
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
        """
        
        # 进度条样式
        self.progress_bar_style = """
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
        """
        
        # 容器样式
        self.container_style = """
            QWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(25, 118, 210, 0.4);
                border-radius: 8px;
            }
        """
    
    def _disable_buttons(self):
        """禁用所有按钮"""
        self.start_button.setEnabled(False)
        self.auto_start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def _enable_buttons(self):
        """启用所有按钮"""
        self.start_button.setEnabled(not self.is_auto_start)
        self.auto_start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def _reset_progress(self):
        """重置进度条"""
        self.progress_bar.setValue(0)
    
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
            directory = QFileDialog.getExistingDirectory(self, lang_manager.get("select_install_path"), self.install_path)
            if directory:
                self.install_path = directory
                self.path_edit.setText(self.install_path)
                self.path_changed = True
                self.browse_button.setText(lang_manager.get("save"))
                self.browse_button.disconnect()
                self.browse_button.clicked.connect(self.save_path)
                self.logger.info(f"选择安装路径: {self.install_path}")
        except Exception as e:
            self.logger.error(f"浏览路径失败: {e}")
            self.start_log.append(f"{lang_manager.get('browse_path_failed')}: {str(e)}")
    
    def on_path_text_changed(self, text):
        """路径文本变化时调用"""
        self.path_changed = True
        self.browse_button.setText(lang_manager.get("save"))
        self.browse_button.disconnect()
        self.browse_button.clicked.connect(self.save_path)
        self.logger.info(f"路径文本变化: {text}")
    
    def save_path(self):
        """保存安装路径"""
        try:
            # 保存路径
            new_path = self.path_edit.text().strip()
            if new_path:
                self.install_path = new_path
                self.save_install_path(self.install_path)
                self.logger.info(f"保存路径: {self.install_path}")
                # 恢复按钮状态
                self.path_changed = False
                self.browse_button.setText(lang_manager.get("browse"))
                self.browse_button.disconnect()
                self.browse_button.clicked.connect(self.browse_path)
                # 通知主窗口更新所有标签页的路径
                from PyQt5.QtWidgets import QApplication
                main_window = QApplication.instance().activeWindow()
                if main_window and hasattr(main_window, 'update_all_tabs_path'):
                    main_window.update_all_tabs_path(self.install_path)
                    self.logger.info(f"通知主窗口更新所有标签页路径为: {self.install_path}")
        except Exception as e:
            self.logger.error(f"保存路径失败: {e}")
            self.start_log.append(f"{lang_manager.get('save_path_failed')}: {str(e)}")
    
    def start_comfyui(self):
        """启动ComfyUI"""
        # 检查点击是否有效
        if not self.is_click_valid("start_comfyui"):
            return
            
        try:
            self.logger.info("开始启动ComfyUI")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 清空日志
            self.start_log.setPlainText("开始启动ComfyUI...\n")
            
            # 检查路径是否有效
            if not self.install_path or not os.path.exists(self.install_path):
                self.logger.error("安装路径无效")
                self.start_log.append(lang_manager.get("path_invalid"))
                self._enable_buttons()
                self._reset_progress()
                return
            
            # 通知主窗口更新所有标签页的路径，确保文件管理路径与一键启动路径保持统一
            from PyQt5.QtWidgets import QApplication
            main_window = QApplication.instance().activeWindow()
            if main_window and hasattr(main_window, 'update_all_tabs_path'):
                main_window.update_all_tabs_path(self.install_path)
                self.logger.info(f"通知主窗口更新所有标签页路径为: {self.install_path}")
            
            # 停止之前的线程（如果存在）
            if self.startup_thread and self.startup_thread.isRunning():
                self.logger.info("停止之前的启动线程")
                self.startup_thread.stop()
                self.startup_thread.terminate()
                self.startup_thread.wait()
            
            # 创建并启动启动线程
            self.logger.info(f"创建启动线程，安装路径: {self.install_path}")
            self.startup_thread = StartComfyUIThread(self.install_path)
            self.startup_thread.update_progress.connect(self.update_progress)
            self.startup_thread.update_log.connect(self.update_log)
            self.startup_thread.start_finished.connect(self.startup_finished)
            self.startup_thread.start()
            self.logger.info("启动线程已启动")
        except Exception as e:
            self.logger.error(f"启动ComfyUI失败: {e}")
            self.start_log.setPlainText(f"{lang_manager.get('startup_failed')}: {str(e)}")
            self._enable_buttons()
            self._reset_progress()
    
    def toggle_auto_start(self):
        """切换自动运行状态"""
        # 检查点击是否有效
        if not self.is_click_valid("toggle_auto_start"):
            return
            
        try:
            self.is_auto_start = not self.is_auto_start
            if self.is_auto_start:
                self.auto_start_button.setText("取消自动")
                self.logger.info("自动运行已开启")
                self.start_log.append("自动运行已开启")
                # 禁用运行功能按钮
                self.start_button.setEnabled(False)
                # 保存自动运行状态
                self.save_install_path(self.install_path)
                # 启动ComfyUI
                self.start_comfyui()
            else:
                self.auto_start_button.setText(lang_manager.get("auto_run"))
                self.logger.info("自动运行已关闭")
                self.start_log.append("自动运行已关闭")
                # 启用运行功能按钮
                self.start_button.setEnabled(True)
                # 保存自动运行状态
                self.save_install_path(self.install_path)
        except Exception as e:
            self.logger.error(f"切换自动运行状态失败: {e}")
            self.start_log.append(f"{lang_manager.get('operation_failed').format(message=str(e))}")
    
    def stop_comfyui(self):
        """停止ComfyUI"""
        # 检查点击是否有效
        if not self.is_click_valid("stop_comfyui"):
            return
            
        try:
            self.logger.info("开始停止ComfyUI")
            self.start_log.append("开始停止ComfyUI...")
            
            # 停止启动线程
            if self.startup_thread and self.startup_thread.isRunning():
                self.startup_thread.stop()
                self.startup_thread.terminate()
                self.startup_thread.wait()
            
            # 启用所有按钮
            self._enable_buttons()
            # 重置进度条
            self._reset_progress()
            
            self.logger.info(lang_manager.get("comfyui_stopped"))
            self.start_log.append(lang_manager.get("comfyui_stopped"))
        except Exception as e:
            self.logger.error(f"停止ComfyUI失败: {e}")
            self.start_log.append(f"{lang_manager.get('operation_failed').format(message=str(e))}")
    
    def update_progress(self, value, message):
        """更新进度"""
        try:
            # 更新进度条
            self.progress_bar.setValue(value)
            # 更新日志
            self.start_log.append(message)
            # 记录日志
            self.logger.info(f"启动进度: {value}% - {message}")
        except Exception as e:
            self.logger.error(f"更新进度失败: {e}")
    
    def update_log(self, message):
        """更新日志"""
        try:
            # 更新日志
            self.start_log.append(message)
            # 记录日志
            self.logger.info(f"启动日志: {message}")
        except Exception as e:
            self.logger.error(f"更新日志失败: {e}")
    
    def startup_finished(self, results):
        """启动完成"""
        try:
            self.logger.info("启动操作完成")
            
            # 重置进度条
            self._reset_progress()
            
            # 显示结果
            if results["status"] == "success":
                self.start_log.append(f"\n{results['message']}")
                # 启动成功后，保持停止按钮可用，禁用其他按钮
                self.start_button.setEnabled(not self.is_auto_start)
                self.auto_start_button.setEnabled(True)
                self.stop_button.setEnabled(True)
            else:
                self.start_log.append(f"\n{lang_manager.get('operation_failed').format(message=results['message'])}")
                # 显示启动失败的提示
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, lang_manager.get("startup_failed"), f"{lang_manager.get('error_message').format(message=results['message'])}\n{lang_manager.get('smart_fix_failed_message').split('\n')[1]}")
                # 启动失败后，启用所有按钮
                self._enable_buttons()
        except Exception as e:
            self.logger.error(f"处理完成事件失败: {e}")
    

    
    def update_path(self, new_path):
        """更新路径"""
        try:
            self.install_path = new_path
            self.path_edit.setText(self.install_path)
            self.logger.info(f"更新路径为: {self.install_path}")
        except Exception as e:
            self.logger.error(f"更新路径失败: {e}")
    
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
            self.start_button.setText(lang_manager.get("click_start"))
            self.auto_start_button.setText(lang_manager.get("auto_run"))
            self.stop_button.setText(lang_manager.get("stop"))
            
            # 更新自动运行按钮状态文本
            if self.is_auto_start:
                self.auto_start_button.setText("取消自动")
            else:
                self.auto_start_button.setText(lang_manager.get("auto_run"))
            
            self.logger.info("一键启动标签页UI已刷新")
        except Exception as e:
            self.logger.error(f"刷新UI失败: {e}")
