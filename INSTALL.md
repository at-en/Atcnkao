# 密评考试题库系统 - 安装指南

## 系统要求

### 最低配置
- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8 或更高版本
- **内存**: 512MB RAM
- **存储**: 100MB 可用空间
- **网络**: 用于下载依赖包

### 推荐配置
- **操作系统**: Windows 11, macOS 12+, Ubuntu 20.04+
- **Python**: 3.9 或更高版本
- **内存**: 1GB RAM
- **存储**: 500MB 可用空间

## 一键安装（推荐）

### 1. 下载项目
```bash
# 如果有git
git clone <项目地址>
cd question_bank_system

# 或者下载压缩包并解压
```

### 2. 运行部署脚本
```bash
# Linux/macOS
python3 deploy.py

# Windows
python deploy.py
```

部署脚本会自动：
- 检测系统环境
- 安装Python依赖
- 创建虚拟环境
- 初始化数据库
- 创建启动脚本
- 运行测试

### 3. 启动系统
部署完成后，使用以下方式启动：

**Linux/macOS:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

**手动启动:**
```bash
cd question_bank_system
source venv/bin/activate  # Windows: venv\Scripts\activate
python src/main.py
```

## 手动安装

如果一键安装失败，可以按照以下步骤手动安装：

### 1. 检查Python环境
```bash
python3 --version  # 确保版本 >= 3.8
pip3 --version     # 确保pip可用
```

### 2. 创建虚拟环境
```bash
cd question_bank_system
python3 -m venv venv
```

### 3. 激活虚拟环境
```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 4. 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 初始化数据库
```bash
python src/main.py
# 首次运行会自动创建数据库和管理员账户
```

## 验证安装

### 1. 访问系统
打开浏览器访问: http://localhost:5000

### 2. 登录测试
使用默认管理员账户登录：
- 用户名: `admin`
- 密码: `admin123`

### 3. 功能检查
- [ ] 主页正常显示
- [ ] 用户登录成功
- [ ] 管理后台可访问
- [ ] 题库导入界面显示

## 常见问题解决

### Python相关问题

**问题**: `python3: command not found`
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip

# macOS (使用Homebrew)
brew install python3
```

**问题**: `pip install` 失败
```bash
# 升级pip
python3 -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 清理缓存
pip cache purge
```

### 权限问题

**问题**: Linux下权限不足
```bash
# 给脚本执行权限
chmod +x deploy.py
chmod +x start.sh

# 如果需要安装系统包
sudo python3 deploy.py
```

### 端口问题

**问题**: 端口5000被占用
```bash
# 查看端口占用
netstat -tulpn | grep :5000
lsof -i :5000

# 修改端口（编辑 src/main.py）
app.run(host='0.0.0.0', port=8000, debug=True)
```

### 数据库问题

**问题**: 数据库初始化失败
```bash
# 删除数据库文件重新初始化
rm src/database/app.db
python src/main.py
```

**问题**: 表结构错误
```bash
# 备份数据（如果需要）
cp src/database/app.db src/database/app.db.backup

# 重新创建数据库
rm src/database/app.db
python src/main.py
```

### 依赖问题

**问题**: 某些包安装失败
```bash
# 单独安装失败的包
pip install flask
pip install sqlalchemy
pip install pandas
pip install openpyxl

# 使用conda（如果有）
conda install flask sqlalchemy pandas openpyxl
```

## 生产环境部署

### 使用Gunicorn（推荐）
```bash
# 安装Gunicorn
pip install gunicorn

# 启动应用
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

### 使用Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 系统服务配置
```bash
# 复制服务文件
sudo cp question-bank.service /etc/systemd/system/

# 启用服务
sudo systemctl enable question-bank
sudo systemctl start question-bank

# 查看状态
sudo systemctl status question-bank
```

## 数据备份

### 备份数据库
```bash
# 备份SQLite数据库
cp src/database/app.db backup/app_$(date +%Y%m%d).db
```

### 备份配置
```bash
# 备份整个项目
tar -czf question_bank_backup_$(date +%Y%m%d).tar.gz question_bank_system/
```

## 更新系统

### 更新代码
```bash
# 停止服务
sudo systemctl stop question-bank

# 更新代码
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl start question-bank
```

### 数据库迁移
如果有数据库结构变更，需要手动处理数据迁移。

## 卸载系统

### 停止服务
```bash
sudo systemctl stop question-bank
sudo systemctl disable question-bank
```

### 删除文件
```bash
# 删除项目目录
rm -rf question_bank_system/

# 删除服务文件
sudo rm /etc/systemd/system/question-bank.service
```

## 技术支持

如果遇到问题，请：
1. 查看本文档的常见问题部分
2. 检查系统日志和错误信息
3. 确认系统环境符合要求
4. 联系技术支持

---

**祝您安装顺利！**

