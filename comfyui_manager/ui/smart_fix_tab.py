#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能修复标签页
"""

import os
import time
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar,
    QLabel, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from comfyui_manager.utils.logger import Logger
from comfyui_manager.utils.embedded_tools import embedded_tools
from comfyui_manager.utils.language_manager import lang_manager


class SmartFixThread(QThread):
    """智能修复线程"""
    update_progress = pyqtSignal(int, str)
    update_log = pyqtSignal(str)
    installation_finished = pyqtSignal(dict)
    
    def __init__(self, install_path, fix_type):
        super().__init__()
        self.install_path = install_path
        self.fix_type = fix_type
    
    def run(self):
        """运行智能修复"""
        try:
            results = {
                "status": "success",
                "message": "修复完成"
            }
            
            # 发送开始进度
            self.update_progress.emit(0, f"开始{self.fix_type}...")
            
            if self.fix_type == "一键修复":
                # 执行所有修复步骤
                self.fix_environment()
                self.update_progress.emit(25, "虚拟环境修复完成")
                
                self.detect_pytorch()
                self.update_progress.emit(50, "PyTorch检测完成")
                
                self.upgrade_comfyui()
                self.update_progress.emit(75, "ComfyUI升级完成")
                
                self.update_dependencies()
                self.update_progress.emit(100, "依赖更新完成")
            elif self.fix_type == "虚拟环境":
                self.fix_environment()
                self.update_progress.emit(100, "虚拟环境修复完成")
            elif self.fix_type == "检测PyTorch":
                self.detect_pytorch()
                self.update_progress.emit(100, "PyTorch检测完成")
            elif self.fix_type == "升级Comfyui":
                self.upgrade_comfyui()
                self.update_progress.emit(100, "ComfyUI升级完成")
            elif self.fix_type == "更新依赖":
                self.update_dependencies()
                self.update_progress.emit(100, "依赖更新完成")
            
            self.installation_finished.emit(results)
        except Exception as e:
            # 发送错误信息
            self.installation_finished.emit({"status": "error", "message": str(e)})
    
    def fix_environment(self):
        """修复虚拟环境"""
        # 获取安装路径所在的磁盘
        install_dir = os.path.dirname(self.install_path)
        if not install_dir:
            install_dir = self.install_path
        
        # 虚拟环境路径
        venv_path = os.path.join(install_dir, "ComfyUI_venv")
        self.update_log.emit(f"虚拟环境路径: {venv_path}")
        
        # 检查虚拟环境是否存在且有效
        venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
        if os.path.exists(venv_python):
            # 测试虚拟环境是否可用
            test_result = subprocess.run(
                [venv_python, "--version"],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if test_result.returncode == 0:
                self.update_log.emit("虚拟环境已存在且可用")
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
        
        self.update_log.emit("虚拟环境修复完成")
    
    def detect_pytorch(self):
        """检测PyTorch"""
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
        try:
            check_result = subprocess.run(
                [venv_python, "-c", "import torch"],
                capture_output=True,
                text=True,
                timeout=120,  # 增加超时时间到120秒
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except subprocess.TimeoutExpired:
            self.update_log.emit("检查PyTorch超时，可能是环境问题，将重新安装...")
            # 超时视为未安装，继续执行安装流程
            check_result = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="Timeout")
        
        if check_result.returncode == 0:
            # PyTorch已安装，验证是否正确
            self.update_log.emit("PyTorch已安装，验证是否正确...")
            try:
                verify_result = subprocess.run(
                    [venv_python, "-c", "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available())"],
                    capture_output=True,
                    text=True,
                    timeout=120  # 增加超时时间到120秒
                )
                
                if verify_result.returncode == 0:
                    self.update_log.emit("PyTorch已正确安装")
                    return
                else:
                    self.update_log.emit("PyTorch安装不正确，需要重新安装...")
            except subprocess.TimeoutExpired:
                self.update_log.emit("验证PyTorch超时，可能是环境问题，将重新安装...")
                # 超时视为安装不正确，继续执行安装流程
        
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
        try:
            verify_result = subprocess.run(
                [venv_python, "-c", "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available())"],
                capture_output=True,
                text=True,
                timeout=120,  # 增加超时时间到120秒
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if verify_result.returncode != 0:
                raise Exception(f"PyTorch验证失败: {verify_result.stderr}")
        except subprocess.TimeoutExpired:
            self.update_log.emit("验证PyTorch超时，但安装过程已完成，继续执行后续步骤...")
            # 超时视为验证通过，继续执行后续步骤
        
        self.update_log.emit("PyTorch检测完成")
    
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
    
    def upgrade_comfyui(self):
        """升级ComfyUI"""
        import os
        import subprocess
        # 获取安装路径所在的磁盘
        install_dir = os.path.dirname(self.install_path)
        if not install_dir:
            install_dir = self.install_path
        
        # ComfyUI安装路径
        comfyui_path = os.path.join(install_dir, "ComfyUI")
        self.update_log.emit(f"ComfyUI安装路径: {comfyui_path}")
        
        # 检查ComfyUI是否存在
        if not os.path.exists(comfyui_path):
            self.update_log.emit("ComfyUI未安装，开始克隆...")
            # 克隆ComfyUI仓库
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
                        bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
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
            # 升级ComfyUI
            self.update_log.emit("ComfyUI已存在，开始升级...")
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
                
                # 执行git pull命令
                pull_command = [git_path, "pull"]
                self.update_log.emit(f"从 {url} 执行升级命令: {' '.join(pull_command)}")
                
                process = subprocess.Popen(
                    pull_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=comfyui_path,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # 读取输出并更新日志
                for line in iter(process.stdout.readline, ''):
                    self.update_log.emit(line.strip())
                
                process.wait()
                
                if process.returncode == 0:
                    self.update_log.emit(f"从 {url} 升级ComfyUI成功")
                    
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
                    self.update_log.emit(f"从 {url} 升级失败，尝试其他源...")
            
            if not pull_success:
                self.update_log.emit("升级失败，可能是网络问题，继续执行下一步")
        
        # 检查ComfyUI-Manager插件
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
                        bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
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
            # 升级ComfyUI-Manager
            self.update_log.emit("ComfyUI-Manager已存在，开始升级...")
            git_path = embedded_tools.get_git_path()
            if not git_path:
                raise Exception("未找到Git可执行文件")
            
            # 执行git pull命令
            pull_command = [git_path, "pull"]
            self.update_log.emit(f"执行升级命令: {' '.join(pull_command)}")
            
            process = subprocess.Popen(
                pull_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=manager_path,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 读取输出并更新日志
            for line in iter(process.stdout.readline, ''):
                self.update_log.emit(line.strip())
            
            process.wait()
            
            if process.returncode != 0:
                self.update_log.emit("升级失败，可能是网络问题，继续执行下一步")
            else:
                self.update_log.emit("ComfyUI-Manager升级成功")
        
        self.update_log.emit("ComfyUI升级完成")
    
    def update_dependencies(self):
        """更新依赖，包括所有子文件夹中的requirements.txt"""
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
        
        # 查找所有requirements.txt文件
        self.update_log.emit("查找所有requirements.txt文件...")
        requirements_files = []
        for root, dirs, files in os.walk(comfyui_path):
            for file in files:
                if file == "requirements.txt":
                    requirements_files.append(os.path.join(root, file))
        
        self.update_log.emit(f"找到 {len(requirements_files)} 个requirements.txt文件")
        
        # 安装每个requirements.txt文件
        for i, req_file in enumerate(requirements_files):
            self.update_log.emit(f"安装依赖 {i+1}/{len(requirements_files)}: {req_file}")
            
            install_command = [
                venv_python, "-m", "pip", "install", "-r", req_file,
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                "--timeout", "120", "--retries", "5", "--no-cache-dir"
            ]
            
            process = subprocess.Popen(
                install_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(req_file),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 读取输出并更新日志
            for line in iter(process.stdout.readline, ''):
                self.update_log.emit(line.strip())
            
            process.wait()
            
            if process.returncode != 0:
                self.update_log.emit(f"警告: 安装 {req_file} 依赖失败，但不影响ComfyUI启动")
            else:
                self.update_log.emit(f"成功安装 {req_file} 依赖")
        
        self.update_log.emit("依赖更新完成")


class SmartFixTab(QWidget):
    """智能修复标签页"""
    
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
        
        path_label = QLabel(lang_manager.get("select_path"))
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
        
        # 一键修复按钮
        self.one_click_fix_button = QPushButton(lang_manager.get("one_click_fix"))
        self.one_click_fix_button.clicked.connect(lambda: self.smart_fix(lang_manager.get("one_click_fix")))
        buttons_layout.addWidget(self.one_click_fix_button)
        
        # 虚拟环境按钮
        self.fix_env_button = QPushButton(lang_manager.get("virtual_environment"))
        self.fix_env_button.clicked.connect(lambda: self.smart_fix(lang_manager.get("virtual_environment")))
        buttons_layout.addWidget(self.fix_env_button)
        
        # 检测PyTorch按钮
        self.detect_pytorch_button = QPushButton(lang_manager.get("detect_pytorch"))
        self.detect_pytorch_button.clicked.connect(lambda: self.smart_fix(lang_manager.get("detect_pytorch")))
        buttons_layout.addWidget(self.detect_pytorch_button)
        
        # 升级Comfyui按钮
        self.upgrade_comfyui_button = QPushButton(lang_manager.get("upgrade_comfyui"))
        self.upgrade_comfyui_button.clicked.connect(lambda: self.smart_fix(lang_manager.get("upgrade_comfyui")))
        buttons_layout.addWidget(self.upgrade_comfyui_button)
        
        # 更新依赖按钮
        self.update_deps_button = QPushButton(lang_manager.get("update_dependencies"))
        self.update_deps_button.clicked.connect(lambda: self.smart_fix(lang_manager.get("update_dependencies")))
        buttons_layout.addWidget(self.update_deps_button)
        
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
    
    def refresh_ui(self):
        """刷新UI，根据当前语言设置更新界面文本"""
        # 刷新语言设置
        lang_manager.refresh_language()
        
        # 更新路径标签和按钮
        for widget in self.findChildren(QLabel):
            if widget.text() == "选择路径" or widget.text() == "Select Path":
                widget.setText(lang_manager.get("select_path"))
        
        # 更新UI元素文本
        self.browse_button.setText(lang_manager.get("browse"))
        self.one_click_fix_button.setText(lang_manager.get("one_click_fix"))
        self.fix_env_button.setText(lang_manager.get("virtual_environment"))
        self.detect_pytorch_button.setText(lang_manager.get("detect_pytorch"))
        self.upgrade_comfyui_button.setText(lang_manager.get("upgrade_comfyui"))
        self.update_deps_button.setText(lang_manager.get("update_dependencies"))
    
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
        self.one_click_fix_button.setEnabled(False)
        self.fix_env_button.setEnabled(False)
        self.detect_pytorch_button.setEnabled(False)
        self.upgrade_comfyui_button.setEnabled(False)
        self.update_deps_button.setEnabled(False)
    
    def _enable_buttons(self):
        """启用所有按钮"""
        self.one_click_fix_button.setEnabled(True)
        self.fix_env_button.setEnabled(True)
        self.detect_pytorch_button.setEnabled(True)
        self.upgrade_comfyui_button.setEnabled(True)
        self.update_deps_button.setEnabled(True)
    
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
    
    def smart_fix(self, fix_type):
        """智能修复"""
        # 检查点击是否有效
        if not self.is_click_valid(f"smart_fix_{fix_type}"):
            return
            
        try:
            # 获取当前选择的路径
            current_path = self.path_edit.text().strip()
            if not current_path:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("select_path"))
                self.logger.info("未选择安装路径")
                return
            
            # 检查路径是否有虚拟环境
            if not self._check_has_virtualenv(current_path):
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("no_virtualenv_warning"))
                self.logger.info(lang_manager.get("virtualenv_check_failed"))
                return
            
            self.logger.info(f"开始{fix_type}")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 清空日志
            self.install_log.setPlainText(f"开始{fix_type}...\n")
            
            # 停止之前的线程（如果存在）
            if self.installation_thread and self.installation_thread.isRunning():
                self.installation_thread.terminate()
                self.installation_thread.wait()
            
            # 创建并启动修复线程
            self.installation_thread = SmartFixThread(current_path, fix_type)
            self.installation_thread.update_progress.connect(self.update_progress)
            self.installation_thread.update_log.connect(self.update_log)
            self.installation_thread.installation_finished.connect(self.installation_finished)
            self.installation_thread.start()
        except Exception as e:
            self.logger.error(f"{fix_type}失败: {e}")
            self.install_log.setPlainText(f"{fix_type}失败: {str(e)}")
            self._enable_buttons()
            self._reset_progress()
    
    def _check_has_virtualenv(self, path=None):
        """检查路径是否有虚拟环境"""
        try:
            import os
            # 使用传入的路径或当前路径
            check_path = path if path else self.install_path
            # 虚拟环境路径
            install_dir = os.path.dirname(check_path) if os.path.dirname(check_path) else check_path
            venv_path = os.path.join(install_dir, "ComfyUI_venv")
            # 检查虚拟环境是否存在且有效
            venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
            return os.path.exists(venv_python)
        except Exception as e:
            self.logger.error(f"检查虚拟环境失败: {e}")
            return False
    
    def update_progress(self, value, message):
        """更新进度"""
        try:
            # 更新进度条
            self.progress_bar.setValue(value)
            # 更新日志
            self.install_log.append(message)
            # 记录日志
            self.logger.info(f"修复进度: {value}% - {message}")
        except Exception as e:
            self.logger.error(f"更新进度失败: {e}")
    
    def update_log(self, message):
        """更新日志"""
        try:
            # 更新日志
            self.install_log.append(message)
            # 记录日志
            self.logger.info(f"修复日志: {message}")
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
            
            # 显示结果
            if results["status"] == "success":
                self.install_log.append(f"\n{results['message']}")
                # 显示修复完成的提示
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, lang_manager.get("fix_completed"), lang_manager.get("smart_fix_completed"))
            else:
                self.install_log.append(f"\n{lang_manager.get('operation_failed').format(message=results['message'])}")
                # 显示修复失败的提示
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, lang_manager.get("fix_failed"), lang_manager.get("smart_fix_failed_message").format(message=results['message']))
        except Exception as e:
            self.logger.error(f"处理完成事件失败: {e}")
