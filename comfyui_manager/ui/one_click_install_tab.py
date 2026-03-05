#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键安装标签页
"""

import os
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar,
    QLabel, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from comfyui_manager.utils.logger import Logger
from comfyui_manager.utils.embedded_tools import embedded_tools
from comfyui_manager.utils.language_manager import lang_manager


class InstallationThread(QThread):
    """安装线程"""
    update_progress = pyqtSignal(int, str)
    installation_finished = pyqtSignal(dict)
    
    def __init__(self, install_path, step):
        super().__init__()
        self.install_path = install_path
        self.step = step
    
    def run(self):
        """运行安装"""
        try:
            results = {
                "status": "success",
                "message": "操作完成"
            }
            
            # 模拟安装过程
            for i in range(101):
                time.sleep(0.05)
                self.update_progress.emit(i, f"{self.step}中... {i}%")
            
            self.installation_finished.emit(results)
        except Exception as e:
            # 发送错误信息
            self.installation_finished.emit({"status": "error", "message": str(e)})


class CreateEnvThread(QThread):
    """创建环境线程"""
    update_progress = pyqtSignal(int, str)
    installation_finished = pyqtSignal(dict)
    
    def __init__(self, install_path):
        super().__init__()
        self.install_path = install_path
    
    def run(self):
        """运行创建环境"""
        try:
            results = {
                "status": "success",
                "message": "环境创建完成"
            }
            
            # 发送开始进度
            self.update_progress.emit(0, "开始创建虚拟环境...")
            
            # 获取安装路径所在的磁盘
            install_dir = os.path.dirname(self.install_path)
            if not install_dir:
                install_dir = self.install_path
            
            # 虚拟环境路径
            venv_path = os.path.join(install_dir, "ComfyUI_venv")
            self.update_progress.emit(10, f"虚拟环境路径: {venv_path}")
            
            # 获取嵌入的Python路径
            python_path = embedded_tools.get_python_path()
            if not python_path:
                raise Exception("未找到Python可执行文件")
            self.update_progress.emit(20, f"使用Python: {python_path}")
            
            # 检查并安装virtualenv模块
            self.update_progress.emit(30, "检查virtualenv模块...")
            import subprocess
            check_result = subprocess.run(
                [python_path, "-c", "import virtualenv"],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if check_result.returncode != 0:
                self.update_progress.emit(40, "virtualenv模块未安装，正在安装...")
                # 尝试安装virtualenv模块，优先使用清华镜像源
                install_result = subprocess.run(
                    [python_path, "-m", "pip", "install", "virtualenv", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # 如果清华源安装失败，使用官方源
                if install_result.returncode != 0:
                    self.update_progress.emit(45, "清华源安装失败，使用官方源...")
                    install_result = subprocess.run(
                    [python_path, "-m", "pip", "install", "virtualenv"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if install_result.returncode != 0:
                    raise Exception(f"安装virtualenv模块失败: {install_result.stderr}")
                self.update_progress.emit(60, "virtualenv模块安装成功")
            
            # 检查虚拟环境是否已存在
            if os.path.exists(venv_path):
                self.update_progress.emit(70, "虚拟环境已存在，正在清理...")
                # 清理旧的虚拟环境
                import shutil
                shutil.rmtree(venv_path, ignore_errors=True)
            
            # 创建虚拟环境
            self.update_progress.emit(80, "正在创建虚拟环境...")
            import subprocess
            result = subprocess.run(
                [python_path, "-m", "virtualenv", venv_path],
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                raise Exception(f"创建虚拟环境失败: {result.stderr}")
            
            self.update_progress.emit(90, "虚拟环境创建成功")
            self.update_progress.emit(95, "正在验证虚拟环境...")
            
            # 验证虚拟环境
            venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
            if not os.path.exists(venv_python):
                raise Exception("虚拟环境创建失败，未找到Python可执行文件")
            
            # 测试虚拟环境
            test_result = subprocess.run(
                [venv_python, "--version"],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if test_result.returncode != 0:
                raise Exception(f"虚拟环境验证失败: {test_result.stderr}")
            
            self.update_progress.emit(100, "虚拟环境创建完成")
            self.installation_finished.emit(results)
        except Exception as e:
            # 发送错误信息
            self.installation_finished.emit({"status": "error", "message": str(e)})


class InstallPyTorchThread(QThread):
    """安装PyTorch线程"""
    update_progress = pyqtSignal(int, str)
    update_log = pyqtSignal(str)
    installation_finished = pyqtSignal(dict)
    
    def __init__(self, install_path):
        super().__init__()
        self.install_path = install_path
    
    def run(self):
        """运行安装PyTorch"""
        try:
            results = {
                "status": "success",
                "message": "PyTorch安装完成"
            }
            
            # 发送开始进度
            self.update_progress.emit(0, "开始安装PyTorch...")
            
            # 获取安装路径所在的磁盘
            install_dir = os.path.dirname(self.install_path)
            if not install_dir:
                install_dir = self.install_path
            
            # 虚拟环境路径
            venv_path = os.path.join(install_dir, "ComfyUI_venv")
            self.update_progress.emit(10, f"虚拟环境路径: {venv_path}")
            
            # 检查虚拟环境是否存在
            if not os.path.exists(venv_path):
                raise Exception("虚拟环境不存在，请先创建环境")
            
            # 获取虚拟环境中的Python可执行文件路径
            venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
            if not os.path.exists(venv_python):
                raise Exception("虚拟环境中未找到Python可执行文件")
            self.update_progress.emit(20, f"使用虚拟环境Python: {venv_python}")
            
            # 检测系统显卡型号
            self.update_progress.emit(30, "检测系统显卡型号...")
            gpu_vendor = self.detect_gpu_vendor()
            self.update_progress.emit(40, f"检测到显卡厂商: {gpu_vendor}")
            
            # 根据显卡厂商安装对应的PyTorch
            if gpu_vendor == "Intel":
                self.update_progress.emit(50, "安装Intel XPU版本PyTorch...")
                # 安装Intel XPU版本PyTorch，使用预发布版本和清华镜像源
                install_command = [
                    venv_python, "-m", "pip", "install", "--pre", "torch", "torchvision", "torchaudio",
                    "--index-url", "https://download.pytorch.org/whl/nightly/xpu",
                    "--extra-index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
                    "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                    "--timeout", "120",
                    "--retries", "5",
                    "--no-cache-dir"
                ]
            elif gpu_vendor == "NVIDIA":
                self.update_progress.emit(50, "安装NVIDIA CUDA版本PyTorch...")
                # 安装NVIDIA CUDA版本PyTorch，添加清华镜像源作为额外索引
                install_command = [
                    venv_python, "-m", "pip", "install", "torch", "torchvision",
                    "--index-url", "https://download.pytorch.org/whl/cu126",
                    "--extra-index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
                    "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                    "--timeout", "120",
                    "--retries", "5",
                    "--no-cache-dir"
                ]
            elif gpu_vendor == "AMD":
                self.update_progress.emit(50, "安装AMD ROCm版本PyTorch...")
                # 安装AMD ROCm版本PyTorch，添加清华镜像源作为额外索引
                install_command = [
                    venv_python, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "transformers", "accelerate",
                    "--index-url", "https://download.pytorch.org/whl/rocm",
                    "--extra-index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
                    "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                    "--timeout", "120",
                    "--retries", "5",
                    "--no-cache-dir"
                ]
            else:
                raise Exception(f"不支持的显卡厂商: {gpu_vendor}")
            
            # 执行安装命令
            self.update_progress.emit(60, f"执行安装命令: {' '.join(install_command)}")
            import subprocess
            
            # 实时执行命令并更新进度
            process = subprocess.Popen(
                install_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 读取输出并更新进度
            progress_steps = 0
            total_steps = 40  # 60%到100%之间的进度
            for line in iter(process.stdout.readline, ''):
                # 输出安装日志
                self.update_log.emit(line.strip())
                # 每读取一行输出，增加一点进度
                progress_steps += 1
                current_progress = 60 + min(int((progress_steps / total_steps) * 40), 40)
                self.update_progress.emit(current_progress, f"安装中... {current_progress}%")
            
            # 等待进程结束
            process.wait()
            
            if process.returncode != 0:
                # 对于Intel XPU，提供更详细的错误信息
                if gpu_vendor == "Intel":
                    raise Exception(f"Intel XPU版本PyTorch安装失败\n请确保您的Intel显卡支持XPU，并且已安装最新的Intel驱动程序")
                else:
                    raise Exception(f"安装PyTorch失败")
            
            self.update_progress.emit(90, "PyTorch安装成功")
            self.update_progress.emit(95, "正在验证PyTorch...")
            
            # 验证PyTorch安装
            verify_result = subprocess.run(
                [venv_python, "-c", "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available())"],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if verify_result.returncode != 0:
                raise Exception(f"PyTorch验证失败: {verify_result.stderr}")
            
            self.update_progress.emit(100, "PyTorch安装完成")
            self.installation_finished.emit(results)
        except Exception as e:
            # 发送错误信息
            self.installation_finished.emit({"status": "error", "message": str(e)})
    
    def detect_gpu_vendor(self):
        """检测显卡厂商"""
        import subprocess
        import platform
        
        system = platform.system()
        
        if system == "Windows":
            # Windows系统使用wmic命令检测
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "Name"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                output = result.stdout.lower()
                if "intel" in output:
                    return "Intel"
                elif "nvidia" in output:
                    return "NVIDIA"
                elif "amd" in output or "radeon" in output:
                    return "AMD"
            except Exception:
                pass
        elif system == "Linux":
            # Linux系统使用lspci命令检测
            try:
                result = subprocess.run(
                    ["lspci"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                output = result.stdout.lower()
                if "intel" in output and "vga" in output:
                    return "Intel"
                elif "nvidia" in output:
                    return "NVIDIA"
                elif "amd" in output and "vga" in output:
                    return "AMD"
            except Exception:
                pass
        elif system == "Darwin":
            # macOS系统使用system_profiler命令检测
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                output = result.stdout.lower()
                if "intel" in output:
                    return "Intel"
                elif "amd" in output:
                    return "AMD"
            except Exception:
                pass
        
        # 如果无法检测，默认返回Intel
        return "Intel"


class InstallComfyUIThread(QThread):
    """安装ComfyUI线程"""
    update_progress = pyqtSignal(int, str)
    update_log = pyqtSignal(str)
    installation_finished = pyqtSignal(dict)
    
    def __init__(self, install_path):
        super().__init__()
        self.install_path = install_path
    
    def run(self):
        """运行安装ComfyUI"""
        try:
            results = {
                "status": "success",
                "message": "ComfyUI安装完成"
            }
            
            # 发送开始进度
            self.update_progress.emit(0, "开始安装ComfyUI...")
            
            # 获取安装路径所在的磁盘
            install_dir = os.path.dirname(self.install_path)
            if not install_dir:
                install_dir = self.install_path
            
            # 虚拟环境路径
            venv_path = os.path.join(install_dir, "ComfyUI_venv")
            self.update_progress.emit(10, f"虚拟环境路径: {venv_path}")
            
            # 检查虚拟环境是否存在
            if not os.path.exists(venv_path):
                raise Exception("虚拟环境不存在，请先创建环境")
            
            # 获取虚拟环境中的Python可执行文件路径
            venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
            if not os.path.exists(venv_python):
                raise Exception("虚拟环境中未找到Python可执行文件")
            self.update_progress.emit(20, f"使用虚拟环境Python: {venv_python}")
            
            # ComfyUI安装路径
            comfyui_path = os.path.join(install_dir, "ComfyUI")
            self.update_progress.emit(30, f"ComfyUI安装路径: {comfyui_path}")
            
            # 检查ComfyUI是否已存在
            if not os.path.exists(comfyui_path):
                # 克隆ComfyUI仓库
                self.update_progress.emit(40, "克隆ComfyUI仓库...")
                import subprocess
                git_path = embedded_tools.get_git_path()
                if not git_path:
                    raise Exception("未找到Git可执行文件")
                
                clone_command = [
                    git_path, "clone", "https://github.com/comfyanonymous/ComfyUI.git", comfyui_path
                ]
                self.update_log.emit(f"执行克隆命令: {' '.join(clone_command)}")
                
                process = subprocess.Popen(
                    clone_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # 读取输出并更新进度
                for line in iter(process.stdout.readline, ''):
                    self.update_log.emit(line.strip())
                
                process.wait()
                
                if process.returncode != 0:
                    raise Exception("克隆ComfyUI仓库失败")
                
                self.update_progress.emit(60, "ComfyUI仓库克隆成功")
            else:
                # ComfyUI已存在，拉取最新版本
                self.update_progress.emit(40, "ComfyUI已存在，拉取最新版本...")
                import subprocess
                git_path = embedded_tools.get_git_path()
                if not git_path:
                    raise Exception("未找到Git可执行文件")
                
                # 尝试从不同的远程仓库拉取最新版本
                repo_urls = [
                    "https://github.com/comfyanonymous/ComfyUI.git",
                    "https://gitee.com/ComfyUI/ComfyUI.git"  # Gitee镜像
                ]
                
                pull_success = False
                for url in repo_urls:
                    # 先设置远程仓库
                    self.update_log.emit(f"设置远程仓库为: {url}")
                    remote_command = [
                        git_path, "remote", "set-url", "origin", url
                    ]
                    remote_process = subprocess.Popen(
                        remote_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        cwd=comfyui_path,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    remote_process.wait()
                    
                    # 拉取最新更改
                    pull_command = [
                        git_path, "pull"
                    ]
                    self.update_log.emit(f"从 {url} 拉取最新版本...")
                    self.update_log.emit(f"执行拉取命令: {' '.join(pull_command)}")
                    
                    process = subprocess.Popen(
                        pull_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        cwd=comfyui_path,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    # 读取输出并更新进度
                    for line in iter(process.stdout.readline, ''):
                        self.update_log.emit(line.strip())
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        self.update_log.emit(f"成功从 {url} 拉取ComfyUI最新版本")
                        
                        # 尝试获取并切换到最新的标签版本
                        tag_result = subprocess.run([git_path, "describe", "--tags", "--abbrev=0"], 
                                                   cwd=comfyui_path,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.STDOUT,
                                                   text=True,
                                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        
                        if tag_result.returncode == 0:
                            latest_tag = tag_result.stdout.strip()
                            self.update_log.emit(f"发现最新标签版本: {latest_tag}")
                            
                            # 尝试切换到最新标签
                            checkout_result = subprocess.run([git_path, "checkout", latest_tag], 
                                                          cwd=comfyui_path,
                                                          stdout=subprocess.PIPE,
                                                          stderr=subprocess.STDOUT,
                                                          text=True,
                                                          creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                            
                            if checkout_result.returncode == 0:
                                self.update_log.emit(f"成功切换到标签版本: {latest_tag}")
                            else:
                                self.update_log.emit(f"无法切换到标签版本: {checkout_result.stderr}")
                        
                        pull_success = True
                        break
                    else:
                        self.update_log.emit(f"从 {url} 拉取失败，尝试其他源...")
                
                if not pull_success:
                    self.update_log.emit("拉取最新版本失败，继续使用当前版本")
                
                self.update_progress.emit(60, "ComfyUI更新完成")
            
            # 安装ComfyUI依赖
            self.update_progress.emit(70, "安装ComfyUI依赖...")
            requirements_file = os.path.join(comfyui_path, "requirements.txt")
            if os.path.exists(requirements_file):
                install_command = [
                    venv_python, "-m", "pip", "install", "-r", requirements_file,
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                    "--timeout", "120", "--retries", "5", "--no-cache-dir"
                ]
                self.update_log.emit(f"执行依赖安装命令: {' '.join(install_command)}")
                
                process = subprocess.Popen(
                    install_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=comfyui_path,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # 读取输出并更新进度
                progress_steps = 0
                total_steps = 30
                for line in iter(process.stdout.readline, ''):
                    self.update_log.emit(line.strip())
                    progress_steps += 1
                    current_progress = 70 + min(int((progress_steps / total_steps) * 20), 20)
                    self.update_progress.emit(current_progress, f"安装依赖中... {current_progress}%")
                
                process.wait()
                
                if process.returncode != 0:
                    raise Exception("安装ComfyUI依赖失败")
            
            self.update_progress.emit(90, "ComfyUI依赖安装成功")
            
            # 添加ComfyUI-Manager插件
            self.update_progress.emit(95, "添加ComfyUI-Manager插件...")
            plugins_path = os.path.join(comfyui_path, "custom_nodes")
            if not os.path.exists(plugins_path):
                os.makedirs(plugins_path)
            
            manager_path = os.path.join(plugins_path, "ComfyUI-Manager")
            if not os.path.exists(manager_path):
                # 克隆ComfyUI-Manager仓库
                git_path = embedded_tools.get_git_path()
                if not git_path:
                    raise Exception("未找到Git可执行文件")
                
                clone_command = [
                    git_path, "clone", "https://github.com/ltdrdata/ComfyUI-Manager.git", manager_path
                ]
                self.update_log.emit(f"执行克隆命令: {' '.join(clone_command)}")
                
                process = subprocess.Popen(
                    clone_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # 读取输出并更新进度
                for line in iter(process.stdout.readline, ''):
                    self.update_log.emit(line.strip())
                
                process.wait()
                
                if process.returncode != 0:
                    raise Exception("克隆ComfyUI-Manager仓库失败")
            else:
                self.update_log.emit("ComfyUI-Manager已存在，跳过克隆")
            
            # 更新ComfyUI-Manager依赖
            self.update_progress.emit(98, "更新ComfyUI-Manager依赖...")
            manager_requirements = os.path.join(manager_path, "requirements.txt")
            if os.path.exists(manager_requirements):
                install_command = [
                    venv_python, "-m", "pip", "install", "-r", manager_requirements,
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                    "--timeout", "120", "--retries", "5", "--no-cache-dir"
                ]
                self.update_log.emit(f"执行依赖安装命令: {' '.join(install_command)}")
                
                process = subprocess.Popen(
                    install_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=manager_path
                )
                
                # 读取输出并更新进度
                for line in iter(process.stdout.readline, ''):
                    self.update_log.emit(line.strip())
                
                process.wait()
                
                if process.returncode != 0:
                    raise Exception("安装ComfyUI-Manager依赖失败")
            
            self.update_progress.emit(100, "ComfyUI安装完成")
            self.installation_finished.emit(results)
        except Exception as e:
            # 发送错误信息
            self.installation_finished.emit({"status": "error", "message": str(e)})


class StartComfyUIThread(QThread):
    """启动ComfyUI线程"""
    update_progress = pyqtSignal(int, str)
    update_log = pyqtSignal(str)
    installation_finished = pyqtSignal(dict)
    
    def __init__(self, install_path):
        super().__init__()
        self.install_path = install_path
    
    def run(self):
        """运行启动ComfyUI"""
        try:
            results = {
                "status": "success",
                "message": "ComfyUI启动成功"
            }
            
            # 发送开始进度
            self.update_progress.emit(0, "开始启动ComfyUI...")
            
            # 获取安装路径所在的磁盘
            install_dir = os.path.dirname(self.install_path)
            if not install_dir:
                install_dir = self.install_path
            
            # 虚拟环境路径
            venv_path = os.path.join(install_dir, "ComfyUI_venv")
            self.update_progress.emit(10, f"虚拟环境路径: {venv_path}")
            
            # 检查虚拟环境是否存在
            if not os.path.exists(venv_path):
                raise Exception("虚拟环境不存在，请先创建环境")
            
            # 获取虚拟环境中的Python可执行文件路径
            venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
            if not os.path.exists(venv_python):
                raise Exception("虚拟环境中未找到Python可执行文件")
            self.update_progress.emit(20, f"使用虚拟环境Python: {venv_python}")
            
            # ComfyUI安装路径
            comfyui_path = os.path.join(install_dir, "ComfyUI")
            self.update_progress.emit(30, f"ComfyUI安装路径: {comfyui_path}")
            
            # 检查ComfyUI是否存在
            if not os.path.exists(comfyui_path):
                raise Exception("ComfyUI未安装，请先安装ComfyUI")
            
            # 检查main.py文件是否存在
            main_py = os.path.join(comfyui_path, "main.py")
            if not os.path.exists(main_py):
                raise Exception("ComfyUI main.py文件不存在")
            
            # 启动ComfyUI
            self.update_progress.emit(40, "启动ComfyUI...")
            import subprocess
            import webbrowser
            import re
            import socket
            import psutil
            
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
                import time
                time.sleep(2)
            
            # 启动ComfyUI进程
            process = subprocess.Popen(
                [venv_python, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=comfyui_path,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 读取输出并查找启动信息
            server_url = None
            startup_complete = False
            
            for line in iter(process.stdout.readline, ''):
                # 输出启动日志
                self.update_log.emit(line.strip())
                
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
                    match = re.search(r"Running on (http://[^\s]+)", line)
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
            self.installation_finished.emit(results)
        except Exception as e:
            # 发送错误信息
            self.installation_finished.emit({"status": "error", "message": str(e)})


class FullInstallThread(QThread):
    """完整安装线程"""
    update_progress = pyqtSignal(int, str)
    update_log = pyqtSignal(str)
    installation_finished = pyqtSignal(dict)
    
    def __init__(self, install_path):
        super().__init__()
        self.install_path = install_path
    
    def run(self):
        """运行完整安装"""
        try:
            results = {
                "status": "success",
                "message": "完整安装完成"
            }
            
            # 发送开始进度
            self.update_progress.emit(0, "开始完整安装...")
            
            # 步骤1: 创建环境
            self.update_progress.emit(5, "开始创建环境...")
            self.create_environment()
            self.update_progress.emit(25, "环境创建完成")
            
            # 步骤2: 安装显卡PyTorch
            self.update_progress.emit(30, "开始安装显卡PyTorch...")
            self.install_pytorch()
            self.update_progress.emit(55, "显卡PyTorch安装完成")
            
            # 步骤3: 安装ComfyUI
            self.update_progress.emit(60, "开始安装ComfyUI...")
            self.install_comfyui()
            self.update_progress.emit(85, "ComfyUI安装完成")
            
            # 步骤4: 测试启动
            self.update_progress.emit(90, "开始测试启动...")
            self.start_comfyui()
            self.update_progress.emit(100, "完整安装完成")
            
            self.installation_finished.emit(results)
        except Exception as e:
            # 发送错误信息
            self.installation_finished.emit({"status": "error", "message": str(e)})
    
    def create_environment(self):
        """创建环境"""
        # 获取安装路径所在的磁盘
        install_dir = os.path.dirname(self.install_path)
        if not install_dir:
            install_dir = self.install_path
        
        # 虚拟环境路径
        venv_path = os.path.join(install_dir, "ComfyUI_venv")
        self.update_log.emit(f"虚拟环境路径: {venv_path}")
        
        # 检查虚拟环境是否已存在且有效
        venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
        if os.path.exists(venv_python):
            # 测试虚拟环境是否可用
            import subprocess
            test_result = subprocess.run(
                [venv_python, "--version"],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if test_result.returncode == 0:
                self.update_log.emit("虚拟环境已存在且可用，跳过创建步骤")
                return
            else:
                self.update_log.emit("虚拟环境存在但不可用，需要重新创建...")
        
        # 获取嵌入的Python路径
        python_path = embedded_tools.get_python_path()
        if not python_path:
            raise Exception("未找到Python可执行文件")
        self.update_log.emit(f"使用Python: {python_path}")
        
        # 检查并安装virtualenv模块
        self.update_log.emit("检查virtualenv模块...")
        import subprocess
        check_result = subprocess.run(
            [python_path, "-c", "import virtualenv"],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if check_result.returncode != 0:
            self.update_log.emit("virtualenv模块未安装，正在安装...")
            # 尝试安装virtualenv模块，优先使用清华镜像源
            install_result = subprocess.run(
                [python_path, "-m", "pip", "install", "virtualenv", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn"],
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 如果清华源安装失败，使用官方源
            if install_result.returncode != 0:
                self.update_log.emit("清华源安装失败，使用官方源...")
                install_result = subprocess.run(
                    [python_path, "-m", "pip", "install", "virtualenv"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            
            if install_result.returncode != 0:
                raise Exception(f"安装virtualenv模块失败: {install_result.stderr}")
            self.update_log.emit("virtualenv模块安装成功")
        
        # 清理旧的虚拟环境（如果存在）
        if os.path.exists(venv_path):
            self.update_log.emit("虚拟环境已存在，正在清理...")
            import shutil
            shutil.rmtree(venv_path, ignore_errors=True)
        
        # 创建虚拟环境
        self.update_log.emit("正在创建虚拟环境...")
        import subprocess
        result = subprocess.run(
            [python_path, "-m", "virtualenv", venv_path],
            capture_output=True,
            text=True,
            timeout=300,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if result.returncode != 0:
            raise Exception(f"创建虚拟环境失败: {result.stderr}")
        
        self.update_log.emit("虚拟环境创建成功")
        self.update_log.emit("正在验证虚拟环境...")
        
        # 验证虚拟环境
        if not os.path.exists(venv_python):
            raise Exception("虚拟环境创建失败，未找到Python可执行文件")
        
        # 测试虚拟环境
        test_result = subprocess.run(
            [venv_python, "--version"],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if test_result.returncode != 0:
            raise Exception(f"虚拟环境验证失败: {test_result.stderr}")
        
        self.update_log.emit("虚拟环境创建完成")
    
    def install_pytorch(self):
        """安装显卡PyTorch"""
        # 获取安装路径所在的磁盘
        install_dir = os.path.dirname(self.install_path)
        if not install_dir:
            install_dir = self.install_path
        
        # 虚拟环境路径
        venv_path = os.path.join(install_dir, "ComfyUI_venv")
        
        # 获取虚拟环境中的Python可执行文件路径
        venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
        if not os.path.exists(venv_python):
            raise Exception("虚拟环境中未找到Python可执行文件")
        
        # 检测系统显卡型号
        self.update_log.emit("检测系统显卡型号...")
        gpu_vendor = self.detect_gpu_vendor()
        self.update_log.emit(f"检测到显卡厂商: {gpu_vendor}")
        
        # 检查PyTorch是否已经安装
        self.update_log.emit("检查PyTorch是否已安装...")
        import subprocess
        check_result = subprocess.run(
            [venv_python, "-c", "import torch"],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if check_result.returncode == 0:
            # PyTorch已安装，验证是否正确
            self.update_log.emit("PyTorch已安装，验证是否正确...")
            verify_result = subprocess.run(
                [venv_python, "-c", "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available())"],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if verify_result.returncode == 0:
                self.update_log.emit("PyTorch已正确安装，跳过安装步骤")
                return
            else:
                self.update_log.emit("PyTorch安装不正确，需要重新安装...")
        
        # 根据显卡厂商安装对应的PyTorch
        if gpu_vendor == "Intel":
            self.update_log.emit("安装Intel XPU版本PyTorch...")
            # 安装Intel XPU版本PyTorch，使用预发布版本和清华镜像源
            install_command = [
                venv_python, "-m", "pip", "install", "--pre", "torch", "torchvision", "torchaudio",
                "--index-url", "https://download.pytorch.org/whl/nightly/xpu",
                "--extra-index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
                "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                "--timeout", "120",
                "--retries", "5",
                "--no-cache-dir"
            ]
        elif gpu_vendor == "NVIDIA":
            self.update_log.emit("安装NVIDIA CUDA版本PyTorch...")
            # 安装NVIDIA CUDA版本PyTorch，添加清华镜像源作为额外索引
            install_command = [
                venv_python, "-m", "pip", "install", "torch", "torchvision",
                "--index-url", "https://download.pytorch.org/whl/cu126",
                "--extra-index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
                "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                "--timeout", "120",
                "--retries", "5",
                "--no-cache-dir"
            ]
        elif gpu_vendor == "AMD":
            self.update_log.emit("安装AMD ROCm版本PyTorch...")
            # 安装AMD ROCm版本PyTorch，添加清华镜像源作为额外索引
            install_command = [
                venv_python, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "transformers", "accelerate",
                "--index-url", "https://download.pytorch.org/whl/rocm",
                "--extra-index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
                "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                "--timeout", "120",
                "--retries", "5",
                "--no-cache-dir"
            ]
        else:
            raise Exception(f"不支持的显卡厂商: {gpu_vendor}")
        
        # 执行安装命令
        self.update_log.emit(f"执行安装命令: {' '.join(install_command)}")
        import subprocess
        
        # 实时执行命令并更新进度
        process = subprocess.Popen(
            install_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # 读取输出并更新日志
        for line in iter(process.stdout.readline, ''):
            self.update_log.emit(line.strip())
        
        # 等待进程结束
        process.wait()
        
        if process.returncode != 0:
            # 对于Intel XPU，提供更详细的错误信息
            if gpu_vendor == "Intel":
                raise Exception(f"Intel XPU版本PyTorch安装失败\n请确保您的Intel显卡支持XPU，并且已安装最新的Intel驱动程序")
            else:
                raise Exception("安装PyTorch失败")
        
        self.update_log.emit("PyTorch安装成功")
        self.update_log.emit("正在验证PyTorch...")
        
        # 验证PyTorch安装
        verify_result = subprocess.run(
            [venv_python, "-c", "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available())"],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if verify_result.returncode != 0:
            raise Exception(f"PyTorch验证失败: {verify_result.stderr}")
        
        self.update_log.emit("PyTorch安装完成")
    
    def detect_gpu_vendor(self):
        """检测显卡厂商"""
        import subprocess
        import platform
        
        system = platform.system()
        
        if system == "Windows":
            # Windows系统使用wmic命令检测
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "Name"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                output = result.stdout.lower()
                if "intel" in output:
                    return "Intel"
                elif "nvidia" in output:
                    return "NVIDIA"
                elif "amd" in output or "radeon" in output:
                    return "AMD"
            except Exception:
                pass
        elif system == "Linux":
            # Linux系统使用lspci命令检测
            try:
                result = subprocess.run(
                    ["lspci"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                output = result.stdout.lower()
                if "intel" in output and "vga" in output:
                    return "Intel"
                elif "nvidia" in output:
                    return "NVIDIA"
                elif "amd" in output and "vga" in output:
                    return "AMD"
            except Exception:
                pass
        elif system == "Darwin":
            # macOS系统使用system_profiler命令检测
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                output = result.stdout.lower()
                if "intel" in output:
                    return "Intel"
                elif "amd" in output:
                    return "AMD"
            except Exception:
                pass
        
        # 如果无法检测，默认返回Intel
        return "Intel"
    
    def install_comfyui(self):
        """安装ComfyUI"""
        import os
        import subprocess
        # 获取安装路径所在的磁盘
        install_dir = os.path.dirname(self.install_path)
        if not install_dir:
            install_dir = self.install_path
        
        # 虚拟环境路径
        venv_path = os.path.join(install_dir, "ComfyUI_venv")
        
        # 获取虚拟环境中的Python可执行文件路径
        venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
        if not os.path.exists(venv_python):
            raise Exception("虚拟环境中未找到Python可执行文件")
        
        # ComfyUI安装路径
        comfyui_path = os.path.join(install_dir, "ComfyUI")
        self.update_log.emit(f"ComfyUI安装路径: {comfyui_path}")
        
        # 检查ComfyUI是否已存在
        if not os.path.exists(comfyui_path):
            # 克隆ComfyUI仓库
            self.update_log.emit("克隆ComfyUI仓库...")
            git_path = embedded_tools.get_git_path()
            if not git_path:
                raise Exception("未找到Git可执行文件")
            
            # 尝试使用不同的仓库地址，增加成功概率
            repo_urls = [
                "https://github.com/comfyanonymous/ComfyUI.git",
                "https://gitee.com/ComfyUI/ComfyUI.git"  # Gitee镜像
            ]
            
            clone_success = False
            for url in repo_urls:
                self.update_log.emit(f"尝试从 {url} 克隆...")
                clone_command = [
                    git_path, "clone", "--depth", "1", url, comfyui_path
                ]
                self.update_log.emit(f"执行克隆命令: {' '.join(clone_command)}")
                
                # 重试机制
                max_retries = 3
                for retry in range(max_retries):
                    self.update_log.emit(f"尝试第 {retry + 1}/{max_retries} 次")
                    process = subprocess.Popen(
                        clone_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    # 读取输出并更新日志
                    for line in iter(process.stdout.readline, ''):
                        self.update_log.emit(line.strip())
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        self.update_log.emit("ComfyUI仓库克隆成功")
                        clone_success = True
                        break
                    else:
                        self.update_log.emit(f"克隆失败，正在重试...")
                        import time
                        time.sleep(2)  # 等待2秒后重试
                
                if clone_success:
                    break
            
            if not clone_success:
                raise Exception("克隆ComfyUI仓库失败，请检查网络连接后重试")
        else:
            # ComfyUI已存在，拉取最新版本
            self.update_log.emit("ComfyUI已存在，拉取最新版本...")
            git_path = embedded_tools.get_git_path()
            if not git_path:
                raise Exception("未找到Git可执行文件")
            
            # 尝试从不同的远程仓库拉取最新版本
            repo_urls = [
                "https://github.com/comfyanonymous/ComfyUI.git",
                "https://gitee.com/ComfyUI/ComfyUI.git"  # Gitee镜像
            ]
            
            pull_success = False
            for url in repo_urls:
                # 先设置远程仓库
                self.update_log.emit(f"设置远程仓库为: {url}")
                remote_command = [
                    git_path, "remote", "set-url", "origin", url
                ]
                remote_process = subprocess.Popen(
                    remote_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=comfyui_path
                )
                remote_process.wait()
                
                # 拉取最新更改
                pull_command = [
                    git_path, "pull"
                ]
                self.update_log.emit(f"从 {url} 拉取最新版本...")
                self.update_log.emit(f"执行拉取命令: {' '.join(pull_command)}")
                
                # 重试机制
                max_retries = 3
                for retry in range(max_retries):
                    self.update_log.emit(f"尝试第 {retry + 1}/{max_retries} 次")
                    process = subprocess.Popen(
                        pull_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        cwd=comfyui_path
                    )
                    
                    # 读取输出并更新日志
                    for line in iter(process.stdout.readline, ''):
                        self.update_log.emit(line.strip())
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        self.update_log.emit(f"成功从 {url} 拉取ComfyUI最新版本")
                        
                        # 尝试获取并切换到最新的标签版本
                        tag_result = subprocess.run([git_path, "describe", "--tags", "--abbrev=0"], 
                                                   cwd=comfyui_path,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.STDOUT,
                                                   text=True)
                        
                        if tag_result.returncode == 0:
                            latest_tag = tag_result.stdout.strip()
                            self.update_log.emit(f"发现最新标签版本: {latest_tag}")
                            
                            # 尝试切换到最新标签
                            checkout_result = subprocess.run([git_path, "checkout", latest_tag], 
                                                          cwd=comfyui_path,
                                                          stdout=subprocess.PIPE,
                                                          stderr=subprocess.STDOUT,
                                                          text=True)
                            
                            if checkout_result.returncode == 0:
                                self.update_log.emit(f"成功切换到标签版本: {latest_tag}")
                            else:
                                self.update_log.emit(f"无法切换到标签版本: {checkout_result.stderr}")
                        
                        pull_success = True
                        break
                    else:
                        self.update_log.emit(f"从 {url} 拉取失败，正在重试...")
                        import time
                        time.sleep(2)  # 等待2秒后重试
                
                if pull_success:
                    break
            
            if not pull_success:
                self.update_log.emit("拉取最新版本失败，继续使用当前版本")
        
        # 安装ComfyUI依赖
        self.update_log.emit("安装ComfyUI依赖...")
        requirements_file = os.path.join(comfyui_path, "requirements.txt")
        if os.path.exists(requirements_file):
            install_command = [
                venv_python, "-m", "pip", "install", "-r", requirements_file,
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                "--timeout", "120", "--retries", "5", "--no-cache-dir"
            ]
            self.update_log.emit(f"执行依赖安装命令: {' '.join(install_command)}")
            
            process = subprocess.Popen(
                install_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=comfyui_path
            )
            
            # 读取输出并更新日志
            for line in iter(process.stdout.readline, ''):
                self.update_log.emit(line.strip())
            
            process.wait()
            
            if process.returncode != 0:
                raise Exception("安装ComfyUI依赖失败")
        
        self.update_log.emit("ComfyUI依赖安装成功")
        
        # 添加ComfyUI-Manager插件
        self.update_log.emit("添加ComfyUI-Manager插件...")
        plugins_path = os.path.join(comfyui_path, "custom_nodes")
        if not os.path.exists(plugins_path):
            os.makedirs(plugins_path)
        
        manager_path = os.path.join(plugins_path, "ComfyUI-Manager")
        # 检查ComfyUI-Manager是否存在且完整
        init_file = os.path.join(manager_path, "__init__.py")
        if not os.path.exists(manager_path) or not os.path.exists(init_file):
            # 如果目录存在但缺少__init__.py，先删除它
            if os.path.exists(manager_path):
                self.update_log.emit("ComfyUI-Manager目录存在但不完整，正在清理...")
                import shutil
                shutil.rmtree(manager_path, ignore_errors=True)
            
            # 克隆ComfyUI-Manager仓库
            git_path = embedded_tools.get_git_path()
            if not git_path:
                raise Exception("未找到Git可执行文件")
            
            # 尝试使用不同的仓库地址，增加成功概率
            repo_urls = [
                "https://github.com/ltdrdata/ComfyUI-Manager.git",
                "https://gitee.com/ComfyUI/ComfyUI-Manager.git"  # Gitee镜像
            ]
            
            clone_success = False
            for url in repo_urls:
                self.update_log.emit(f"尝试从 {url} 克隆ComfyUI-Manager...")
                clone_command = [
                    git_path, "clone", "--depth", "1", url, manager_path
                ]
                self.update_log.emit(f"执行克隆命令: {' '.join(clone_command)}")
                
                # 重试机制
                max_retries = 3
                for retry in range(max_retries):
                    self.update_log.emit(f"尝试第 {retry + 1}/{max_retries} 次")
                    process = subprocess.Popen(
                        clone_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    # 读取输出并更新日志
                    for line in iter(process.stdout.readline, ''):
                        self.update_log.emit(line.strip())
                    
                    process.wait()
                    
                    # 检查克隆是否成功且包含__init__.py
                    if process.returncode == 0 and os.path.exists(os.path.join(manager_path, "__init__.py")):
                        self.update_log.emit("ComfyUI-Manager仓库克隆成功")
                        clone_success = True
                        break
                    else:
                        self.update_log.emit(f"克隆失败或不完整，正在重试...")
                        # 清理不完整的目录
                        if os.path.exists(manager_path):
                            import shutil
                            shutil.rmtree(manager_path, ignore_errors=True)
                        import time
                        time.sleep(2)  # 等待2秒后重试
                
                if clone_success:
                    break
            
            if not clone_success:
                # 如果克隆失败，创建一个基本的__init__.py文件以避免启动错误
                self.update_log.emit("克隆失败，创建基本的ComfyUI-Manager结构...")
                os.makedirs(manager_path, exist_ok=True)
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write("""
# ComfyUI-Manager
# 基本初始化文件

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
""")
                self.update_log.emit("已创建基本的ComfyUI-Manager结构")
        else:
            self.update_log.emit("ComfyUI-Manager已存在且完整，跳过克隆")
        
        # 更新ComfyUI-Manager依赖
        self.update_log.emit("更新ComfyUI-Manager依赖...")
        manager_requirements = os.path.join(manager_path, "requirements.txt")
        if os.path.exists(manager_requirements):
            install_command = [
                venv_python, "-m", "pip", "install", "-r", manager_requirements,
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                "--timeout", "120", "--retries", "5", "--no-cache-dir"
            ]
            self.update_log.emit(f"执行依赖安装命令: {' '.join(install_command)}")
            
            process = subprocess.Popen(
                install_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=manager_path
            )
            
            # 读取输出并更新日志
            for line in iter(process.stdout.readline, ''):
                self.update_log.emit(line.strip())
            
            process.wait()
            
            if process.returncode != 0:
                # 依赖安装失败不阻止继续执行，只记录警告
                self.update_log.emit("警告: 安装ComfyUI-Manager依赖失败，但不影响ComfyUI启动")
        else:
            self.update_log.emit("未找到ComfyUI-Manager依赖文件，跳过依赖安装")
        
        self.update_log.emit("ComfyUI安装完成")
    
    def start_comfyui(self):
        """启动ComfyUI"""
        # 获取安装路径所在的磁盘
        install_dir = os.path.dirname(self.install_path)
        if not install_dir:
            install_dir = self.install_path
        
        # 虚拟环境路径
        venv_path = os.path.join(install_dir, "ComfyUI_venv")
        
        # 获取虚拟环境中的Python可执行文件路径
        venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
        if not os.path.exists(venv_python):
            raise Exception("虚拟环境中未找到Python可执行文件")
        
        # ComfyUI安装路径
        comfyui_path = os.path.join(install_dir, "ComfyUI")
        
        # 检查main.py文件是否存在
        main_py = os.path.join(comfyui_path, "main.py")
        if not os.path.exists(main_py):
            raise Exception("ComfyUI main.py文件不存在")
        
        # 启动ComfyUI
        self.update_log.emit("启动ComfyUI...")
        import subprocess
        import webbrowser
        import re
        import socket
        import psutil
        
        # 检查并清理占用8188端口的进程
        self.update_log.emit("检查端口8188是否被占用...")
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
            import time
            time.sleep(2)
        
        # 启动ComfyUI进程
        process = subprocess.Popen(
            [venv_python, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=comfyui_path
        )
        
        # 读取输出并查找启动信息
        server_url = None
        startup_complete = False
        
        for line in iter(process.stdout.readline, ''):
            # 输出启动日志
            self.update_log.emit(line.strip())
            
            # 查找服务器URL
            if "Starting server" in line:
                # 等待下一行获取服务器地址
                continue
            elif "To see the GUI go to" in line:
                match = re.search(r"To see the GUI go to:? (http://[^\s]+)", line)
                if match:
                    server_url = match.group(1)
                    self.update_log.emit(f"ComfyUI服务器启动成功，地址: {server_url}")
                    
                    # 打开浏览器
                    self.update_log.emit("打开浏览器界面...")
                    webbrowser.open(server_url)
                    self.update_log.emit("浏览器已打开")
                    startup_complete = True
                    break
            elif "Running on" in line:
                match = re.search(r"Running on (http://[^\s]+)", line)
                if match:
                    server_url = match.group(1)
                    self.update_log.emit(f"ComfyUI服务器启动成功，地址: {server_url}")
                    
                    # 打开浏览器
                    self.update_log.emit("打开浏览器界面...")
                    webbrowser.open(server_url)
                    self.update_log.emit("浏览器已打开")
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
        
        self.update_log.emit("ComfyUI启动完成")


class OneClickInstallTab(QWidget):
    """一键安装标签页"""
    
    def __init__(self, parent=None):
        """初始化"""
        super().__init__(parent)
        self.logger = Logger()
        self.installation_thread = None
        # 点击时间记录，用于防重复点击
        self.last_click_time = {}
        self.click_cooldown = 2  # 点击冷却时间（秒）
        # 加载保存的安装路径
        self.install_path = self.load_install_path()
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
        
        path_label = QLabel(lang_manager.get("install_path"))
        self.path_edit = QLineEdit()
        self.path_edit.setText(self.install_path)
        # 保存按钮状态
        self.path_changed = False
        self.browse_button = QPushButton(lang_manager.get("browse"))
        self.browse_button.clicked.connect(self.browse_path)
        
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
        
        # 开始安装按钮
        self.start_install_button = QPushButton(lang_manager.get("start_install"))
        self.start_install_button.clicked.connect(lambda: self._handle_button_click(self.start_install_button, self.start_install))
        buttons_layout.addWidget(self.start_install_button)
        
        # 创建环境按钮
        self.create_env_button = QPushButton(lang_manager.get("create_environment"))
        self.create_env_button.clicked.connect(lambda: self._handle_button_click(self.create_env_button, self.create_env))
        buttons_layout.addWidget(self.create_env_button)
        
        # 显卡PyTorch按钮
        self.install_pytorch_button = QPushButton(lang_manager.get("install_pytorch"))
        self.install_pytorch_button.clicked.connect(lambda: self._handle_button_click(self.install_pytorch_button, self.install_pytorch))
        buttons_layout.addWidget(self.install_pytorch_button)
        
        # 安装ComfyUI按钮
        self.install_comfyui_button = QPushButton(lang_manager.get("install_comfyui"))
        self.install_comfyui_button.clicked.connect(lambda: self._handle_button_click(self.install_comfyui_button, self.install_comfyui))
        buttons_layout.addWidget(self.install_comfyui_button)
        
        # 测试启动按钮
        self.test_start_button = QPushButton(lang_manager.get("test_start"))
        self.test_start_button.clicked.connect(lambda: self._handle_button_click(self.test_start_button, self.test_start))
        buttons_layout.addWidget(self.test_start_button)
        
        layout.addWidget(buttons_container)
        
        # 安装日志
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(12, 12, 12, 12)
        

        
        # 日志内容
        self.install_log = QTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setMinimumHeight(300)
        self.install_log.setStyleSheet(self.text_edit_style)
        log_layout.addWidget(self.install_log, 1)
        
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
        """刷新UI，根据当前语言设置更新界面文本"""
        # 刷新语言设置
        lang_manager.refresh_language()
        
        # 更新路径标签和按钮
        for widget in self.findChildren(QLabel):
            if widget.text() == "安装路径" or widget.text() == "Install Path":
                widget.setText(lang_manager.get("install_path"))
        
        # 更新UI元素文本
        self.browse_button.setText(lang_manager.get("browse"))
        self.start_install_button.setText(lang_manager.get("start_install"))
        self.create_env_button.setText(lang_manager.get("create_environment"))
        self.install_pytorch_button.setText(lang_manager.get("install_pytorch"))
        self.install_comfyui_button.setText(lang_manager.get("install_comfyui"))
        self.test_start_button.setText(lang_manager.get("test_start"))
    
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
        self.start_install_button.setEnabled(False)
        self.create_env_button.setEnabled(False)
        self.install_pytorch_button.setEnabled(False)
        self.install_comfyui_button.setEnabled(False)
        self.test_start_button.setEnabled(False)
    
    def _enable_buttons(self):
        """启用所有按钮"""
        self.start_install_button.setEnabled(True)
        self.create_env_button.setEnabled(True)
        self.install_pytorch_button.setEnabled(True)
        self.install_comfyui_button.setEnabled(True)
        self.test_start_button.setEnabled(True)
    
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
            self.install_log.append(f"{lang_manager.get('browse_path_failed')}: {str(e)}")
    
    def update_path(self, new_path):
        """更新路径"""
        try:
            self.install_path = new_path
            self.path_edit.setText(self.install_path)
            self.logger.info(f"更新路径为: {self.install_path}")
        except Exception as e:
            self.logger.error(f"更新路径失败: {e}")
    
    def save_path(self):
        """保存安装路径"""
        try:
            # 保存路径
            if self.save_install_path(self.install_path):
                self.logger.info(f"保存安装路径: {self.install_path}")
                self.install_log.append(f"{lang_manager.get('save_path_success').format(path=self.install_path)}")
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
            else:
                self.install_log.append(lang_manager.get("save_path_failed"))
        except Exception as e:
            self.logger.error(f"保存路径失败: {e}")
            self.install_log.append(f"{lang_manager.get('save_path_failed')}: {str(e)}")
    
    def start_install(self):
        """开始安装"""
        # 检查点击是否有效
        if not self.is_click_valid("start_install"):
            return
            
        try:
            self.logger.info("开始安装")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 清空日志
            self.install_log.setPlainText("开始安装...\n")
            
            # 停止之前的线程（如果存在）
            if self.installation_thread and self.installation_thread.isRunning():
                self.installation_thread.terminate()
                self.installation_thread.wait()
            
            # 创建并启动完整安装线程
            self.installation_thread = FullInstallThread(self.install_path)
            self.installation_thread.update_progress.connect(self.update_progress)
            self.installation_thread.update_log.connect(self.update_log)
            self.installation_thread.installation_finished.connect(self.installation_finished)
            self.installation_thread.start()
        except Exception as e:
            self.logger.error(f"安装失败: {e}")
            self.install_log.setPlainText(f"安装失败: {str(e)}")
            self._enable_buttons()
            self._reset_progress()
    
    def create_env(self):
        """创建环境"""
        # 检查点击是否有效
        if not self.is_click_valid("create_env"):
            return
            
        try:
            self.logger.info("开始创建环境")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 清空日志
            self.install_log.setPlainText("开始创建环境...\n")
            
            # 停止之前的线程（如果存在）
            if self.installation_thread and self.installation_thread.isRunning():
                self.installation_thread.terminate()
                self.installation_thread.wait()
            
            # 创建并启动安装线程
            self.installation_thread = CreateEnvThread(self.install_path)
            self.installation_thread.update_progress.connect(self.update_progress)
            self.installation_thread.installation_finished.connect(self.installation_finished)
            self.installation_thread.start()
        except Exception as e:
            self.logger.error(f"创建环境失败: {e}")
            self.install_log.setPlainText(f"创建环境失败: {str(e)}")
            self._enable_buttons()
            self._reset_progress()
    
    def install_pytorch(self):
        """安装显卡PyTorch"""
        # 检查点击是否有效
        if not self.is_click_valid("install_pytorch"):
            return
            
        try:
            self.logger.info("开始安装显卡PyTorch")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 清空日志
            self.install_log.setPlainText("开始安装显卡PyTorch...\n")
            
            # 停止之前的线程（如果存在）
            if self.installation_thread and self.installation_thread.isRunning():
                self.installation_thread.terminate()
                self.installation_thread.wait()
            
            # 创建并启动安装线程
            self.installation_thread = InstallPyTorchThread(self.install_path)
            self.installation_thread.update_progress.connect(self.update_progress)
            self.installation_thread.update_log.connect(self.update_log)
            self.installation_thread.installation_finished.connect(self.installation_finished)
            self.installation_thread.start()
        except Exception as e:
            self.logger.error(f"安装显卡PyTorch失败: {e}")
            self.install_log.setPlainText(f"安装显卡PyTorch失败: {str(e)}")
            self._enable_buttons()
            self._reset_progress()
    
    def install_comfyui(self):
        """安装ComfyUI"""
        # 检查点击是否有效
        if not self.is_click_valid("install_comfyui"):
            return
            
        try:
            self.logger.info("开始安装ComfyUI")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 清空日志
            self.install_log.setPlainText("开始安装ComfyUI...\n")
            
            # 停止之前的线程（如果存在）
            if self.installation_thread and self.installation_thread.isRunning():
                self.installation_thread.terminate()
                self.installation_thread.wait()
            
            # 创建并启动安装线程
            self.installation_thread = InstallComfyUIThread(self.install_path)
            self.installation_thread.update_progress.connect(self.update_progress)
            self.installation_thread.update_log.connect(self.update_log)
            self.installation_thread.installation_finished.connect(self.installation_finished)
            self.installation_thread.start()
        except Exception as e:
            self.logger.error(f"安装ComfyUI失败: {e}")
            self.install_log.setPlainText(f"安装ComfyUI失败: {str(e)}")
            self._enable_buttons()
            self._reset_progress()
    
    def test_start(self):
        """测试启动"""
        # 检查点击是否有效
        if not self.is_click_valid("test_start"):
            return
            
        try:
            self.logger.info("开始测试启动")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 清空日志
            self.install_log.setPlainText("开始测试启动...\n")
            
            # 停止之前的线程（如果存在）
            if self.installation_thread and self.installation_thread.isRunning():
                self.installation_thread.terminate()
                self.installation_thread.wait()
            
            # 创建并启动启动线程
            self.installation_thread = StartComfyUIThread(self.install_path)
            self.installation_thread.update_progress.connect(self.update_progress)
            self.installation_thread.update_log.connect(self.update_log)
            self.installation_thread.installation_finished.connect(self.installation_finished)
            self.installation_thread.start()
        except Exception as e:
            self.logger.error(f"测试启动失败: {e}")
            self.install_log.setPlainText(f"测试启动失败: {str(e)}")
            self._enable_buttons()
            self._reset_progress()
    
    def update_progress(self, value, message):
        """更新进度"""
        try:
            # 更新进度条
            self.progress_bar.setValue(value)
            # 更新日志
            self.install_log.append(message)
            # 记录日志
            self.logger.info(f"安装进度: {value}% - {message}")
        except Exception as e:
            self.logger.error(f"更新进度失败: {e}")
    
    def update_log(self, message):
        """更新日志"""
        try:
            # 更新日志
            self.install_log.append(message)
            # 记录日志
            self.logger.info(f"安装日志: {message}")
        except Exception as e:
            self.logger.error(f"更新日志失败: {e}")
    
    def installation_finished(self, results):
        """安装完成"""
        try:
            self.logger.info("操作完成")
            # 启用所有按钮
            self._enable_buttons()
            
            # 重置进度条
            self._reset_progress()
            
            # 显示安装结果
            if results.get("status") == "success":
                self.install_log.append("\n操作成功！")
                self.logger.info("操作成功")
            else:
                error_message = results.get("message", "未知错误")
                self.install_log.append(f"\n操作失败: {error_message}")
                self.logger.error(f"操作失败: {error_message}")
        except Exception as e:
            self.logger.error(f"处理操作结果失败: {e}")
            self.install_log.append(f"处理操作结果失败: {str(e)}")
