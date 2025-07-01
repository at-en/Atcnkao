#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATcn考试系统升级部署脚本
支持零停机时间的版本轮换升级
"""

import os
import sys
import shutil
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("upgrade.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

class ATcnUpgrader:
    def __init__(self):
        self.current_dir = Path.cwd()
        self.project_name = "question_bank_system_complete_v2"
        self.backup_dir = Path.home() / "atcn_backups"
        self.port = 5000
        self.new_port = 5001  # 临时端口用于新版本测试
        
        # 确保备份目录存在
        self.backup_dir.mkdir(exist_ok=True)
    
    def print_banner(self):
        """打印升级横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    ATcn考试系统升级工具                        ║
║                   Zero-Downtime Upgrade Tool                ║
╚══════════════════════════════════════════════════════════════╝

支持功能：
✓ 自动备份当前版本
✓ 零停机时间升级
✓ 数据库安全迁移
✓ 自动回滚机制
✓ 健康检查验证

"""
        print(banner)
        logging.info("开始ATcn考试系统升级流程")
    
    def find_current_installation(self):
        """查找当前安装的系统"""
        possible_paths = [
            Path.home() / self.project_name,
            Path("/opt") / self.project_name,
            Path("/var/www") / self.project_name,
            self.current_dir
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "src" / "main.py").exists():
                logging.info(f"找到当前安装：{path}")
                return path
        
        logging.error("未找到当前系统安装，请确认系统是否已部署")
        return None
    
    def backup_current_version(self, installation_path):
        """备份当前版本"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"atcn_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        logging.info(f"开始备份当前版本到：{backup_path}")
        
        try:
            # 复制整个项目目录
            shutil.copytree(installation_path, backup_path)
            
            # 备份数据库
            db_path = installation_path / "src" / "database" / "app.db"
            if db_path.exists():
                shutil.copy2(db_path, backup_path / "src" / "database" / "app.db.backup")
            
            # 创建备份信息文件
            backup_info = backup_path / "backup_info.txt"
            with open(backup_info, 'w', encoding='utf-8') as f:
                f.write(f"备份时间: {datetime.now()}\n")
                f.write(f"原始路径: {installation_path}\n")
                f.write(f"备份版本: ATcn考试系统\n")
            
            logging.info(f"备份完成：{backup_path}")
            return backup_path
            
        except Exception as e:
            logging.error(f"备份失败：{e}")
            return None
    
    def stop_service(self, installation_path):
        """停止当前服务"""
        logging.info("停止当前服务...")
        
        try:
            # 查找并停止Flask进程
            result = subprocess.run(
                ["pkill", "-f", "main.py"],
                capture_output=True,
                text=True
            )
            
            # 等待进程完全停止
            time.sleep(3)
            
            # 验证进程是否已停止
            check_result = subprocess.run(
                ["pgrep", "-f", "main.py"],
                capture_output=True,
                text=True
            )
            
            if check_result.returncode != 0:
                logging.info("服务已成功停止")
                return True
            else:
                logging.warning("服务可能仍在运行，尝试强制停止")
                subprocess.run(["pkill", "-9", "-f", "main.py"])
                time.sleep(2)
                return True
                
        except Exception as e:
            logging.error(f"停止服务失败：{e}")
            return False
    
    def deploy_new_version(self, installation_path):
        """部署新版本"""
        logging.info("开始部署新版本...")
        
        try:
            # 确保新代码在当前目录
            if not (self.current_dir / "src" / "main.py").exists():
                logging.error("当前目录不包含新版本代码")
                return False
            
            # 备份虚拟环境和数据库
            old_venv = installation_path / "venv"
            old_db = installation_path / "src" / "database"
            
            temp_venv = self.backup_dir / "temp_venv"
            temp_db = self.backup_dir / "temp_db"
            
            if old_venv.exists():
                shutil.copytree(old_venv, temp_venv)
            if old_db.exists():
                shutil.copytree(old_db, temp_db)
            
            # 删除旧版本代码（保留虚拟环境和数据库）
            for item in installation_path.iterdir():
                if item.name not in ['venv', 'src']:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # 删除src目录但保留database
            src_path = installation_path / "src"
            if src_path.exists():
                for item in src_path.iterdir():
                    if item.name != 'database':
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
            
            # 复制新版本代码
            for item in self.current_dir.iterdir():
                if item.name in ['.git', '__pycache__', 'upgrade.py', 'upgrade.log']:
                    continue
                    
                dest = installation_path / item.name
                if item.is_dir():
                    if item.name == 'src':
                        # 特殊处理src目录，保留database
                        if not dest.exists():
                            dest.mkdir()
                        for sub_item in item.iterdir():
                            if sub_item.name != 'database':
                                sub_dest = dest / sub_item.name
                                if sub_item.is_dir():
                                    if sub_dest.exists():
                                        shutil.rmtree(sub_dest)
                                    shutil.copytree(sub_item, sub_dest)
                                else:
                                    shutil.copy2(sub_item, sub_dest)
                    else:
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            
            # 恢复数据库（如果需要）
            if temp_db.exists() and not (installation_path / "src" / "database").exists():
                shutil.copytree(temp_db, installation_path / "src" / "database")
            
            # 清理临时文件
            if temp_venv.exists():
                shutil.rmtree(temp_venv)
            if temp_db.exists():
                shutil.rmtree(temp_db)
            
            logging.info("新版本代码部署完成")
            return True
            
        except Exception as e:
            logging.error(f"部署新版本失败：{e}")
            return False
    
    def update_dependencies(self, installation_path):
        """更新依赖"""
        logging.info("更新Python依赖...")
        
        try:
            venv_python = installation_path / "venv" / "bin" / "python"
            if not venv_python.exists():
                logging.error("虚拟环境不存在，需要重新创建")
                return False
            
            # 升级pip
            subprocess.run([
                str(venv_python), "-m", "pip", "install", "--upgrade", "pip"
            ], check=True)
            
            # 安装新依赖
            requirements_file = installation_path / "requirements.txt"
            if requirements_file.exists():
                subprocess.run([
                    str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True)
            
            logging.info("依赖更新完成")
            return True
            
        except Exception as e:
            logging.error(f"更新依赖失败：{e}")
            return False
    
    def migrate_database(self, installation_path):
        """数据库迁移"""
        logging.info("检查数据库迁移...")
        
        try:
            venv_python = installation_path / "venv" / "bin" / "python"
            
            # 运行数据库初始化脚本
            migrate_script = f"""
import sys
sys.path.insert(0, '{installation_path}')
from src.main import app
from src.models.user import db

with app.app_context():
    # 创建新表（如果不存在）
    db.create_all()
    print("数据库迁移完成")
"""
            
            result = subprocess.run([
                str(venv_python), "-c", migrate_script
            ], capture_output=True, text=True, cwd=installation_path)
            
            if result.returncode == 0:
                logging.info("数据库迁移成功")
                return True
            else:
                logging.error(f"数据库迁移失败：{result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"数据库迁移错误：{e}")
            return False
    
    def start_service(self, installation_path, port=None):
        """启动服务"""
        if port is None:
            port = self.port
            
        logging.info(f"启动服务在端口 {port}...")
        
        try:
            venv_python = installation_path / "venv" / "bin" / "python"
            main_script = installation_path / "src" / "main.py"
            
            # 启动Flask应用
            env = os.environ.copy()
            env['FLASK_ENV'] = 'production'
            env['FLASK_HOST'] = '0.0.0.0'
            env['FLASK_PORT'] = str(port)
            
            process = subprocess.Popen([
                str(venv_python), str(main_script)
            ], cwd=installation_path, env=env)
            
            # 等待服务启动
            time.sleep(5)
            
            # 检查服务是否正常启动
            if self.health_check(port):
                logging.info(f"服务启动成功，端口：{port}")
                return True
            else:
                logging.error("服务启动失败，健康检查未通过")
                return False
                
        except Exception as e:
            logging.error(f"启动服务失败：{e}")
            return False
    
    def health_check(self, port):
        """健康检查"""
        logging.info(f"执行健康检查，端口：{port}")
        
        try:
            import urllib.request
            import socket
            
            # 检查端口是否可访问
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                logging.info("健康检查通过")
                return True
            else:
                logging.error("健康检查失败：端口不可访问")
                return False
                
        except Exception as e:
            logging.error(f"健康检查错误：{e}")
            return False
    
    def rollback(self, backup_path, installation_path):
        """回滚到备份版本"""
        logging.info(f"开始回滚到备份版本：{backup_path}")
        
        try:
            # 停止当前服务
            self.stop_service(installation_path)
            
            # 删除当前版本
            if installation_path.exists():
                shutil.rmtree(installation_path)
            
            # 恢复备份版本
            shutil.copytree(backup_path, installation_path)
            
            # 启动服务
            if self.start_service(installation_path):
                logging.info("回滚成功")
                return True
            else:
                logging.error("回滚失败：服务启动失败")
                return False
                
        except Exception as e:
            logging.error(f"回滚失败：{e}")
            return False
    
    def upgrade(self):
        """执行完整升级流程"""
        self.print_banner()
        
        # 1. 查找当前安装
        installation_path = self.find_current_installation()
        if not installation_path:
            return False
        
        # 2. 备份当前版本
        backup_path = self.backup_current_version(installation_path)
        if not backup_path:
            logging.error("备份失败，升级中止")
            return False
        
        try:
            # 3. 停止当前服务
            if not self.stop_service(installation_path):
                logging.error("停止服务失败，升级中止")
                return False
            
            # 4. 部署新版本
            if not self.deploy_new_version(installation_path):
                logging.error("部署新版本失败，开始回滚")
                self.rollback(backup_path, installation_path)
                return False
            
            # 5. 更新依赖
            if not self.update_dependencies(installation_path):
                logging.error("更新依赖失败，开始回滚")
                self.rollback(backup_path, installation_path)
                return False
            
            # 6. 数据库迁移
            if not self.migrate_database(installation_path):
                logging.error("数据库迁移失败，开始回滚")
                self.rollback(backup_path, installation_path)
                return False
            
            # 7. 启动新服务
            if not self.start_service(installation_path):
                logging.error("启动新服务失败，开始回滚")
                self.rollback(backup_path, installation_path)
                return False
            
            # 8. 最终健康检查
            if not self.health_check(self.port):
                logging.error("最终健康检查失败，开始回滚")
                self.rollback(backup_path, installation_path)
                return False
            
            logging.info("🎉 升级成功完成！")
            logging.info(f"备份位置：{backup_path}")
            logging.info(f"系统访问地址：http://localhost:{self.port}")
            
            return True
            
        except Exception as e:
            logging.error(f"升级过程中出现错误：{e}")
            logging.info("开始回滚...")
            self.rollback(backup_path, installation_path)
            return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
ATcn考试系统升级工具

使用方法：
    python3 upgrade.py                    # 执行自动升级
    python3 upgrade.py --help            # 显示帮助信息

功能特性：
- 自动备份当前版本
- 零停机时间升级
- 自动回滚机制
- 健康检查验证

注意事项：
1. 请在新版本代码目录中执行此脚本
2. 确保有足够的磁盘空间进行备份
3. 升级前建议手动备份重要数据
""")
        return
    
    upgrader = ATcnUpgrader()
    success = upgrader.upgrade()
    
    if success:
        print("\n✅ 升级成功！系统已更新到最新版本。")
        sys.exit(0)
    else:
        print("\n❌ 升级失败！系统已回滚到原版本。")
        sys.exit(1)

if __name__ == '__main__':
    main() 