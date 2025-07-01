# 密评考试题库系统

一个功能完整的在线考试系统，支持Excel题库导入、Web端做题、用户管理、自动判分、错题本等功能。

## 功能特性

- **题库管理**: 支持Excel文件一键导入题库，支持示例文件格式。
- **Web端做题**: 用户可以在Web界面进行在线做题。
- **自动判分**: 系统自动对用户的答题进行判分，并提供详细结果。
- **错题本**: 自动记录用户做错的题目，方便用户复习和巩固。
- **多用户管理**: 支持ADMIN（管理员）和USER（普通用户）两种角色，实现多用户注册、登录和权限管理。
- **随机抽题**: 支持按题型（多选、判断、单选）和数量进行随机抽题，例如共140题，其中多选60、判断20、单选60。
- **百分制计分**: 采用百分制计分方式。
- **AI解析接口**: 预留AI解析接口，方便后期接入大语言模型，提供题目解析功能。
- **一键部署**: 提供智能一键部署脚本，支持Windows、macOS、Linux系统，自动检测操作系统、Python环境，并处理依赖安装、虚拟环境创建、数据库初始化等。

## 部署指南

### 1. 获取项目

请确保您已下载完整的项目文件。

### 2. 运行部署脚本

进入项目根目录（`question_bank_system`），找到 `deploy.py` 脚本。

**Linux/macOS:**

```bash
cd /path/to/your/question_bank_system
chmod +x deploy.py
./deploy.py
```

**Windows:**

打开命令提示符（CMD）或PowerShell，进入项目根目录，然后运行：

```bash
cd C:\path\to\your\question_bank_system
python deploy.py
```

部署脚本将引导您完成以下步骤：

- **系统依赖检查**: 检查Python (3.8+) 和 pip 是否安装。
- **虚拟环境创建**: 为项目创建一个独立的Python虚拟环境。
- **依赖安装**: 自动安装 `requirements.txt` 中列出的所有Python依赖。
- **数据库初始化**: 初始化SQLite数据库，并创建默认管理员账户（admin/admin123）。
- **启动脚本生成**: 生成 `start.sh` (Linux/macOS) 或 `start.bat` (Windows) 启动脚本。
- **系统服务文件 (Linux)**: 可选生成 `question-bank.service` 文件，方便在Linux上作为系统服务运行。

### 3. 启动应用

部署成功后，您可以通过以下方式启动应用：

**Linux/macOS:**

```bash
./start.sh
```

**Windows:**

双击 `start.bat` 文件，或在命令行运行：

```bash
start.bat
```

或者手动启动：

```bash
cd /path/to/your/question_bank_system
source venv/bin/activate  # Windows: venv\Scripts\activate
python src/main.py
```

### 4. 访问应用

应用启动后，在浏览器中访问：

`http://localhost:5000`

如果部署在服务器上，请将 `localhost` 替换为服务器的IP地址或域名。

### 5. 默认管理员账户

- **用户名**: `admin`
- **密码**: `admin123`

**重要提示**: 首次登录后请务必修改默认管理员密码。

## 使用说明

### 题库导入

1. 使用管理员账户登录系统。
2. 进入管理后台。
3. 上传您的Excel题库文件。请确保Excel文件格式符合系统要求（具体格式请参考示例文件或系统提示）。

### 做题与判分

普通用户登录后，可以选择开始考试，系统将根据配置随机抽取题目。完成答题后，系统将自动判分并记录成绩。

### 错题本

系统会自动记录用户做错的题目，用户可以在错题本中查看并进行针对性练习。

## 注意事项

- **端口占用**: 确保5000端口未被占用。如果需要修改端口，请编辑 `src/main.py` 文件中的 `app.run()` 函数。
- **网络配置**: 如果您的服务器同时支持IPv4和IPv6，系统默认监听所有可用接口。若遇到访问问题，请检查防火墙设置或尝试在 `src/main.py` 中将 `app.run(host=\'0.0.0.0\', port=5000)` 修改为 `app.run(host=\'::\', port=5000)` (仅IPv6) 或 `app.run(host=\'0.0.0.0\', port=5000)` (仅IPv4)。
- **日志文件**: 部署和运行日志将记录在 `deploy.log` 文件中，方便排查问题。

## 贡献

欢迎对本项目提出建议和贡献！


