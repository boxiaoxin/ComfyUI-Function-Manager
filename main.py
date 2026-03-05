#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI功能管理器主程序
"""

import sys
import os

# 将项目根目录添加到Python模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QSharedMemory
from PyQt5.QtGui import QIcon

from comfyui_manager.ui.main_window import MainWindow
from comfyui_manager.utils.logger import Logger


def main():
    """主函数"""
    # 检查是否已有实例运行
    shared_memory = QSharedMemory("ComfyUI_Manager_Instance")
    if shared_memory.attach():
        # 已有实例运行，退出当前进程
        return
    
    # 创建共享内存，标记实例正在运行
    if not shared_memory.create(1):
        return
    
    # 设置应用程序信息
    app = QApplication(sys.argv)
    app.setApplicationName("ComfyUI功能管理器")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ComfyUI")
    app.setOrganizationDomain("comfyui.org")
    
    # 创建日志系统
    logger = Logger()
    logger.info("启动ComfyUI功能管理器")
    
    # 创建主窗口
    main_window = MainWindow()
    main_window.show()
    
    # 运行应用程序
    try:
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"应用程序异常: {e}")
        sys.exit(1)
    finally:
        # 释放共享内存
        shared_memory.detach()


if __name__ == "__main__":
    main()
