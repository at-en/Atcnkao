#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题库系统一键部署脚本
支持 Windows、macOS、Linux 系统
智能检测环境并自动安装依赖
"""

import os
import sys
import platform
import subprocess
import shutil
import urllib.request
import zipfile
import json
import logging
import time
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Colors:
    """终端颜色类"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class QuestionBankDeployer:
    def __init__(self):
        self.system = platform.system().lower()
        self.python_cmd = self.detect_python()
        self.pip_cmd = self.detect_pip()
        self.has_sudo = self.check_sudo()
        # 确保 project_dir 始终指向 deploy.py 所在的目录
        self.project_dir = Path(__file__).resolve().parent
        self.log_file = self.project_dir / "deploy.log"
        
        # 将日志输出到文件
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(file_handler)

    def print_banner(self):
        """打印欢迎横幅"""
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    题库系统一键部署脚本                        ║
║                  Question Bank System Deployer              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}

{Colors.GREEN}系统信息:{Colors.END}
- 操作系统: {platform.system()} {platform.release()}
- Python版本: {sys.version.split()[0]}
- 架构: {platform.machine()}
- 项目目录: {self.project_dir}
"""
        print(banner)
        logging.info(f"系统信息: OS={platform.system()} {platform.release()}, Python={sys.version.split()[0]}, Arch={platform.machine()}, ProjectDir={self.project_dir}")

    def detect_python(self):
        """检测Python命令"""
        logging.info("检测Python命令...")
        commands = ['python3', 'python', 'py']
        for cmd in commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and 'Python 3' in result.stdout:
                    logging.info(f"找到Python命令: {cmd}")
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        logging.warning("未找到Python 3命令")
        return None

    def detect_pip(self):
        """检测pip命令"""
        logging.info("检测pip命令...")
        if self.python_cmd:
            # 尝试使用 python -m pip
            try:
                result = subprocess.run([self.python_cmd, '-m', 'pip', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logging.info(f"找到pip命令: {self.python_cmd} -m pip")
                    return [self.python_cmd, '-m', 'pip']
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # 尝试直接使用pip命令
        commands = ['pip3', 'pip']
        for cmd in commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logging.info(f"找到pip命令: {cmd}")
                    return [cmd]
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        logging.warning("未找到pip命令")
        return None

    def check_sudo(self):
        """检查是否有sudo权限"""
        logging.info("检查sudo权限...")
        if self.system == 'windows':
            return False
        try:
            result = subprocess.run(['sudo', '-n', 'true'], 
                                  capture_output=True, timeout=5)
            logging.info(f"sudo权限检查结果: {result.returncode == 0}")
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logging.warning("sudo命令未找到或超时")
            return False

    def run_command(self, cmd, description="", use_sudo=False, check=True, cwd=None):
        """执行命令并处理错误"""
        if isinstance(cmd, str):
            cmd = cmd.split()
        
        full_cmd = list(cmd) # 复制一份，避免修改原始列表
        if use_sudo and self.has_sudo and self.system != 'windows':
            full_cmd.insert(0, 'sudo')
        
        cmd_str = ' '.join(str(x) for x in full_cmd) # 确保所有元素都是字符串
        print(f"{Colors.BLUE}执行: {cmd_str}{Colors.END}")
        logging.info(f"执行命令: {cmd_str}")
        
        # 如果未指定 cwd，则使用 project_dir
        if cwd is None:
            cwd = self.project_dir

        try:
            if description:
                print(f"{Colors.YELLOW}{description}...{Colors.END}")
            
            # 确保 cwd 是字符串类型
            process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(cwd))
            stdout, stderr = process.communicate(timeout=300)

            if stdout:
                print(stdout)
                logging.info(f"STDOUT:\n{stdout}")
            
            if process.returncode == 0:
                print(f"{Colors.GREEN}✓ 成功{Colors.END}")
                logging.info(f"命令成功: {cmd_str}")
            else:
                print(f"{Colors.RED}✗ 失败 (返回码: {process.returncode}){Colors.END}")
                logging.error(f"命令失败 (返回码: {process.returncode}): {cmd_str}")
                if stderr:
                    print(f"{Colors.RED}错误信息: {stderr}{Colors.END}")
                    logging.error(f"STDERR:\n{stderr}")
                if check:
                    raise subprocess.CalledProcessError(process.returncode, cmd_str, stdout=stdout, stderr=stderr)
            
            return process
            
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            print(f"{Colors.RED}✗ 命令执行超时: {cmd_str}{Colors.END}")
            logging.error(f"命令超时: {cmd_str}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
            return None
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}✗ 命令执行失败: {e.cmd}{Colors.END}")
            logging.error(f"命令执行失败: {e.cmd}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
            if e.stderr:
                print(f"{Colors.RED}错误信息: {e.stderr}{Colors.END}")
            return None
        except FileNotFoundError:
            print(f"{Colors.RED}✗ 命令未找到: {cmd[0]}{Colors.END}")
            logging.error(f"命令未找到: {cmd[0]}")
            return None
        except Exception as e:
            print(f"{Colors.RED}✗ 发生未知错误: {e}{Colors.END}")
            logging.error(f"未知错误: {e}", exc_info=True)
            return None

    def install_python(self):
        """安装Python"""
        print(f"{Colors.YELLOW}正在尝试安装Python...{Colors.END}")
        logging.info("尝试安装Python")
        
        if self.system == 'windows':
            print(f"{Colors.RED}Windows系统请手动安装Python 3.8+：{Colors.END}{Colors.UNDERLINE}https://www.python.org/downloads/{Colors.END}")
            logging.error("Windows系统无法自动安装Python")
            return False
        elif self.system == 'darwin':  # macOS
            if not shutil.which('brew'):
                print(f"{Colors.YELLOW}Homebrew未安装，正在安装Homebrew...{Colors.END}")
                logging.info("Homebrew未安装，尝试安装")
                cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                result = self.run_command(cmd, "安装Homebrew", check=False)
                if not result or result.returncode != 0:
                    print(f"{Colors.RED}Homebrew安装失败，请手动安装Python{Colors.END}")
                    logging.error("Homebrew安装失败")
                    return False
            
            result = self.run_command(['brew', 'install', 'python3'], "安装Python3", check=False)
            if result and result.returncode == 0:
                self.python_cmd = self.detect_python()
                return True
            else:
                print(f"{Colors.RED}Python3安装失败，请手动安装{Colors.END}")
                logging.error("Python3 (brew) 安装失败")
                return False
        else:  # Linux
            package_manager = None
            if shutil.which('apt'):
                package_manager = 'apt'
            elif shutil.which('yum'):
                package_manager = 'yum'
            elif shutil.which('dnf'):
                package_manager = 'dnf'
            elif shutil.which('pacman'):
                package_manager = 'pacman'
            
            if package_manager:
                print(f"{Colors.YELLOW}检测到包管理器: {package_manager}{Colors.END}")
                logging.info(f"检测到包管理器: {package_manager}")
                if package_manager == 'apt':
                    self.run_command(['apt', 'update'], "更新包列表", use_sudo=True, check=False)
                    result = self.run_command(['apt', 'install', '-y', 'python3', 'python3-pip', 'python3-venv'], 
                                            "安装Python3及相关工具", use_sudo=True, check=False)
                elif package_manager == 'yum':
                    result = self.run_command(['yum', 'install', '-y', 'python3', 'python3-pip'], 
                                            "安装Python3及相关工具", use_sudo=True, check=False)
                elif package_manager == 'dnf':
                    result = self.run_command(['dnf', 'install', '-y', 'python3', 'python3-pip'], 
                                            "安装Python3及相关工具", use_sudo=True, check=False)
                elif package_manager == 'pacman':
                    result = self.run_command(['pacman', '-S', '--noconfirm', 'python', 'python-pip'], 
                                            "安装Python3及相关工具", use_sudo=True, check=False)
                
                if result and result.returncode == 0:
                    self.python_cmd = self.detect_python()
                    self.pip_cmd = self.detect_pip()
                    return True
                else:
                    print(f"{Colors.RED}Python3安装失败，请手动安装{Colors.END}")
                    logging.error(f"Python3 ({package_manager}) Installation failed")
                    return False
            else:
                print(f"{Colors.RED}未识别的包管理器，请手动安装Python 3.8+{Colors.END}")
                logging.error("未识别的包管理器，无法自动安装Python")
                return False

    def check_dependencies(self):
        """检查系统依赖"""
        print(f"{Colors.CYAN}检查系统依赖...{Colors.END}")
        logging.info("开始检查系统依赖")
        
        # 检查Python
        if not self.python_cmd:
            print(f"{Colors.RED}✗ 未找到Python 3。请确保Python 3.8+已安装并添加到PATH。{Colors.END}")
            logging.warning("Python 3 未找到")
            if input(f"{Colors.YELLOW}是否尝试自动安装Python? (y/n): {Colors.END}").lower() == 'y':
                if not self.install_python():
                    print(f"{Colors.RED}Python自动安装失败，请手动安装后重试。{Colors.END}")
                    return False
                self.python_cmd = self.detect_python()
                if not self.python_cmd:
                    print(f"{Colors.RED}Python安装后仍未检测到，请检查安装日志。{Colors.END}")
                    return False
            else:
                print(f"{Colors.RED}请手动安装Python 3.8+后重试。{Colors.END}")
                return False
        else:
            print(f"{Colors.GREEN}✓ Python: {self.python_cmd} ({sys.version.split()[0]}){Colors.END}")
            logging.info(f"Python检测成功: {self.python_cmd} ({sys.version.split()[0]})")

        # 检查pip
        if not self.pip_cmd:
            print(f"{Colors.RED}✗ 未找到pip。请确保pip已安装。{Colors.END}")
            logging.warning("pip 未找到")
            # 尝试安装pip
            if self.system != 'windows':
                if shutil.which('apt'):
                    self.run_command(['apt', 'install', '-y', 'python3-pip'], "安装pip", use_sudo=True, check=False)
                elif shutil.which('yum'):
                    self.run_command(['yum', 'install', '-y', 'python3-pip'], "安装pip", use_sudo=True, check=False)
            
            self.pip_cmd = self.detect_pip()
            if not self.pip_cmd:
                print(f"{Colors.RED}pip自动安装失败，请手动安装后重试。{Colors.END}")
                logging.error("pip自动安装失败")
                return False
        else:
            pip_cmd_str = ' '.join(self.pip_cmd)
            print(f"{Colors.GREEN}✓ pip: {pip_cmd_str}{Colors.END}")
            logging.info(f"pip检测成功: {pip_cmd_str}")

        return True

    def create_virtual_environment(self):
        """创建虚拟环境"""
        venv_path = self.project_dir / 'venv'
        
        if venv_path.exists():
            print(f"{Colors.GREEN}✓ 虚拟环境已存在{Colors.END}")
            logging.info("虚拟环境已存在")
            return True
        
        print(f"{Colors.YELLOW}创建虚拟环境...{Colors.END}")
        logging.info("开始创建虚拟环境")
        result = self.run_command([self.python_cmd, '-m', 'venv', str(venv_path)], 
                                "创建虚拟环境", cwd=self.project_dir) 
        
        if result and result.returncode == 0:
            print(f"{Colors.GREEN}✓ 虚拟环境创建成功{Colors.END}")
            logging.info("虚拟环境创建成功")
            return True
        else:
            print(f"{Colors.RED}✗ 虚拟环境创建失败。请检查Python安装和权限。{Colors.END}")
            logging.error("虚拟环境创建失败")
            return False

    def get_venv_python(self):
        """获取虚拟环境中的Python路径"""
        venv_path = self.project_dir / 'venv'
        if self.system == 'windows':
            return str(venv_path / 'Scripts' / 'python.exe')
        else:
            return str(venv_path / 'bin' / 'python')

    def get_venv_pip(self):
        """获取虚拟环境中的pip路径"""
        venv_python = self.get_venv_python()
        return [venv_python, '-m', 'pip']

    def install_requirements(self):
        """安装Python依赖"""
        requirements_file = self.project_dir / 'requirements.txt'
        
        if not requirements_file.exists():
            print(f"{Colors.RED}✗ requirements.txt 文件不存在。请确保部署脚本在项目根目录下。{Colors.END}")
            logging.error("requirements.txt 文件未找到")
            return False

        print(f"{Colors.YELLOW}安装Python依赖...{Colors.END}")
        logging.info("开始安装Python依赖")
        venv_pip = self.get_venv_pip()
        
        # 升级pip
        print(f"{Colors.YELLOW}升级pip...{Colors.END}")
        self.run_command(venv_pip + ['install', '--upgrade', 'pip'], "升级pip", check=False, cwd=self.project_dir) 
        
        # 安装依赖
        print(f"{Colors.YELLOW}安装依赖包...{Colors.END}")
        result = self.run_command(venv_pip + ['install', '-r', str(requirements_file)], 
                                "安装依赖包", cwd=self.project_dir) 
        
        if result and result.returncode == 0:
            print(f"{Colors.GREEN}✓ 依赖安装成功{Colors.END}")
            logging.info("依赖安装成功")
            return True
        else:
            print(f"{Colors.RED}✗ 依赖安装失败。请检查requirements.txt文件内容或网络连接。{Colors.END}")
            logging.error("依赖安装失败")
            return False

    def initialize_database(self):
        """初始化数据库"""
        print(f"{Colors.YELLOW}初始化数据库...{Colors.END}")
        logging.info("开始初始化数据库")
        
        venv_python = self.get_venv_python()
        main_py = self.project_dir / 'src' / 'main.py'
        db_file = self.project_dir / 'src' / 'database' / 'app.db'

        if not main_py.exists():
            print(f"{Colors.RED}✗ main.py 文件不存在。请确保项目结构完整。{Colors.END}")
            logging.error("main.py 文件未找到")
            return False
        
        if db_file.exists():
            print(f"{Colors.YELLOW}数据库文件已存在: {db_file}{Colors.END}")
            logging.info("数据库文件已存在")
            user_input = input(f"{Colors.YELLOW}检测到数据库文件已存在，是否覆盖？(y/N): {Colors.END}").lower()
            if user_input == 'y':
                try:
                    os.remove(db_file)
                    print(f"{Colors.GREEN}✓ 已删除旧数据库文件。{Colors.END}")
                    logging.info("已删除旧数据库文件")
                except Exception as e:
                    print(f"{Colors.RED}✗ 删除旧数据库文件失败: {e}{Colors.END}")
                    logging.error(f"删除旧数据库文件失败: {e}")
                    return False
            else:
                print(f"{Colors.YELLOW}跳过数据库初始化。{Colors.END}")
                logging.info("跳过数据库初始化")
                return True # 如果不覆盖，则认为初始化成功

        # 运行数据库初始化（通过导入模块触发）
        # 这里的cwd应该设置为项目根目录，因为init_script中的sys.path.insert(0, '{src_path}')
        # 期望src_path是项目根目录，以便正确导入src.main
        init_script = f"""
import sys
sys.path.insert(0, '{self.project_dir}')
from src.main import app
with app.app_context():
    from src.models.user import db, User
    from src.models.question import Question
    from src.models.exam import ExamRecord, AnswerRecord, WrongQuestion
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@example.com', role='ADMIN')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("默认管理员账户已创建: admin/admin123")
    print("数据库初始化完成")
"""
        
        result = self.run_command([venv_python, '-c', init_script], "执行数据库初始化脚本", cwd=self.project_dir) 
        
        if result and result.returncode == 0:
            print(f"{Colors.GREEN}✓ 数据库初始化成功{Colors.END}")
            logging.info("数据库初始化成功")
            return True
        else:
            print(f"{Colors.RED}✗ 数据库初始化失败。请检查日志文件 (deploy.log) 获取详细错误信息。{Colors.END}")
            logging.error("数据库初始化失败")
            return False

    def create_startup_scripts(self):
        """创建启动脚本"""
        print(f"{Colors.YELLOW}创建启动脚本...{Colors.END}")
        logging.info("开始创建启动脚本")
        
        # Windows启动脚本
        if self.system == 'windows':
            start_script = self.project_dir / 'start.bat'
            with open(start_script, 'w', encoding='utf-8') as f:
                f.write(f"""@echo off
cd /d "{self.project_dir}"
call venv\\Scripts\\activate
python src\\main.py
pause
""")
            print(f"{Colors.GREEN}✓ 创建了 start.bat{Colors.END}")
            logging.info("创建 start.bat")
        
        # Unix启动脚本
        start_script = self.project_dir / 'start.sh'
        with open(start_script, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/bash
cd "{self.project_dir}"
source venv/bin/activate
python src/main.py
""")
        
        # 设置执行权限
        if self.system != 'windows':
            os.chmod(start_script, 0o755)
            print(f"{Colors.GREEN}✓ 创建了 start.sh{Colors.END}")
            logging.info("创建 start.sh")

    def create_service_file(self):
        """创建系统服务文件（Linux）"""
        if self.system != 'linux':
            return
        
        print(f"{Colors.YELLOW}创建系统服务文件 (可选)...{Colors.END}")
        logging.info("开始创建系统服务文件")
        
        service_content = f"""[Unit]
Description=Question Bank System
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={self.project_dir}
Environment=PATH={self.project_dir}/venv/bin
ExecStart={self.project_dir}/venv/bin/python {self.project_dir}/src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        service_file = self.project_dir / 'question-bank.service'
        try:
            with open(service_file, 'w', encoding='utf-8') as f:
                f.write(service_content)
            print(f"{Colors.GREEN}✓ 创建了 {service_file.name}{Colors.END}")
            logging.info(f"创建 {service_file.name}")
            print(f"{Colors.CYAN}要将应用安装为系统服务，请手动执行以下命令:{Colors.END}")
            print(f"  {Colors.BOLD}sudo cp {service_file} /etc/systemd/system/{Colors.END}")
            print(f"  {Colors.BOLD}sudo systemctl enable question-bank{Colors.END}")
            print(f"  {Colors.BOLD}sudo systemctl start question-bank{Colors.END}")
            logging.info("系统服务文件创建成功，提示用户手动安装")
        except Exception as e:
            print(f"{Colors.RED}✗ 创建系统服务文件失败: {e}{Colors.END}")
            logging.error(f"创建系统服务文件失败: {e}")

    def test_installation(self):
        """测试安装"""
        print(f"{Colors.YELLOW}测试安装...{Colors.END}")
        logging.info("开始测试安装")
        
        venv_python = self.get_venv_python()

        test_script = f"""
import sys
sys.path.insert(0, '{self.project_dir}')
try:
    from src.main import app
    print("✓ 应用导入成功")
    
    # 测试数据库连接和默认管理员账户
    with app.app_context():
        from src.models.user import db, User
        # 尝试查询用户，如果表不存在会抛出异常
        users = User.query.all()
        admin_exists = User.query.filter_by(username='admin').first() is not None
        print(f"✓ 数据库连接成功，用户数: {{len(users)}}, 管理员账户存在: {{admin_exists}}")
    
    print("✓ 所有测试通过")
except Exception as e:
    print(f"✗ 测试失败: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
        
        result = self.run_command([venv_python, '-c', test_script], "运行安装测试", cwd=self.project_dir) 
        
        if result and result.returncode == 0:
            print(f"{Colors.GREEN}✓ 安装测试通过{Colors.END}")
            logging.info("安装测试通过")
            return True
        else:
            print(f"{Colors.RED}✗ 安装测试失败。请检查日志文件 (deploy.log) 获取详细错误信息。{Colors.END}")
            logging.error("安装测试失败")
            return False

    def print_usage_instructions(self):
        """打印使用说明"""
        instructions = f"""
{Colors.GREEN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                        安装完成！                            ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}

{Colors.CYAN}启动方式:{Colors.END}
"""
        
        if self.system == 'windows':
            instructions += f"  双击运行: {self.project_dir}\\start.bat\n"
        
        instructions += f"""  命令行启动: {self.project_dir}/start.sh
  手动启动: 
    cd {self.project_dir}
    source venv/bin/activate  # Windows: venv\\Scripts\\activate
    python src/main.py

{Colors.CYAN}访问地址:{Colors.END}
  http://localhost:5000  (如果部署在服务器上，请使用服务器IP或域名)

{Colors.CYAN}默认管理员账户:{Colors.END}
  用户名: admin
  密码: admin123

{Colors.CYAN}题库导入:{Colors.END}
  1. 使用管理员账户登录
  2. 进入管理后台
  3. 上传Excel题库文件

{Colors.YELLOW}注意事项:{Colors.END}
  - 确保5000端口未被占用。如果需要修改端口，请编辑 `src/main.py` 文件。
  - 题库Excel文件格式需要符合系统要求，详见 `USER_GUIDE.md`。
  - 建议在生产环境中修改默认管理员密码。
  - 详细日志请查看 `deploy.log` 文件。
  - {Colors.BOLD}网络配置提示:{Colors.END} 如果您的服务器同时支持IPv4和IPv6，系统默认监听所有可用接口。若遇到访问问题，请检查防火墙设置或尝试在 `src/main.py` 中将 `app.run(host='0.0.0.0', port=5000)` 修改为 `app.run(host='::', port=5000)` (仅IPv6) 或 `app.run(host='0.0.0.0', port=5000)` (仅IPv4)。

{Colors.GREEN}祝您使用愉快！{Colors.END}
"""
        print(instructions)
        logging.info("部署完成，打印使用说明")

    def deploy(self):
        """主部署流程"""
        try:
            self.print_banner()
            
            # 检查依赖
            if not self.check_dependencies():
                print(f"{Colors.RED}依赖检查失败，部署终止。请查看deploy.log获取详细信息。{Colors.END}")
                return False
            
            # 创建虚拟环境
            if not self.create_virtual_environment():
                print(f"{Colors.RED}虚拟环境创建失败，部署终止。请查看deploy.log获取详细信息。{Colors.END}")
                return False
            
            # 安装依赖
            if not self.install_requirements():
                print(f"{Colors.RED}依赖安装失败，部署终止。请查看deploy.log获取详细信息。{Colors.END}")
                return False
            
            # 初始化数据库
            if not self.initialize_database():
                print(f"{Colors.RED}数据库初始化失败，部署终止。请查看deploy.log获取详细信息。{Colors.END}")
                return False
            
            # 创建启动脚本
            self.create_startup_scripts()
            
            # 创建服务文件（Linux）
            self.create_service_file()
            
            # 测试安装
            if not self.test_installation():
                print(f"{Colors.RED}安装测试失败，请检查配置和deploy.log。{Colors.END}")
                return False
            
            # 打印使用说明
            self.print_usage_instructions()
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}部署被用户中断。{Colors.END}")
            logging.info("部署被用户中断")
            return False
        except Exception as e:
            print(f"{Colors.RED}部署过程中发生未知错误: {e}{Colors.END}")
            logging.error(f"部署过程中发生未知错误: {e}", exc_info=True)
            print(f"{Colors.RED}请查看deploy.log文件获取详细错误信息。{Colors.END}")
            return False

def main():
    """主函数"""
    deployer = QuestionBankDeployer()
    success = deployer.deploy()
    
    if success:
        print(f"\n{Colors.GREEN}部署成功完成！{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}部署失败，请检查错误信息和deploy.log文件并重试。{Colors.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()

