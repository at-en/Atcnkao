# ATcn考试系统升级指南

## 📋 升级概述

本指南将指导您如何安全地将ATcn考试系统从旧版本升级到最新版本，升级过程支持自动备份、回滚和零停机时间部署。

## 🎯 升级特性

- ✅ **自动备份**：升级前自动备份当前版本和数据库
- ✅ **零停机升级**：最小化服务中断时间
- ✅ **自动回滚**：升级失败时自动恢复到原版本
- ✅ **健康检查**：确保新版本正常运行
- ✅ **数据库迁移**：自动处理数据库结构变更

## 🔄 主要变更

### v2.0 版本更新内容：

1. **系统重命名**：从"密评考试题库系统"更名为"ATcn考试系统"
2. **用户管理优化**：
   - 关闭前台注册功能
   - 仅管理员可添加新用户
   - 增加密码修改功能
   - 完善权限控制

3. **管理后台升级**：
   - 全新的选项卡式界面
   - 题库管理功能增强
   - 用户管理功能完善
   - 题库导入功能优化

4. **题库导入改进**：
   - 支持多工作表导入
   - 智能题型识别
   - 重复题目过滤
   - 导入日志记录

## 🛠 升级前准备

### 1. 系统要求检查

确保您的服务器满足以下要求：

```bash
# 检查Python版本（需要3.8+）
python3 --version

# 检查磁盘空间（至少2GB剩余空间）
df -h

# 检查当前系统状态
ps aux | grep main.py
```

### 2. 手动备份重要数据（可选但推荐）

```bash
# 创建手动备份目录
mkdir -p ~/manual_backup_$(date +%Y%m%d)

# 备份数据库
cp ~/question_bank_system_complete_v2/src/database/app.db ~/manual_backup_$(date +%Y%m%d)/

# 备份配置文件（如果有自定义配置）
cp -r ~/question_bank_system_complete_v2/src/static/ ~/manual_backup_$(date +%Y%m%d)/
```

### 3. 获取新版本代码

```bash
# 下载新版本代码
cd ~/
git clone <新版本仓库地址> atcn_upgrade_temp
# 或者上传新版本文件到服务器
```

## 🚀 执行升级

### 步骤1：准备升级环境

```bash
# 进入新版本代码目录
cd ~/atcn_upgrade_temp

# 确认新版本文件完整性
ls -la
# 应该看到: src/ requirements.txt upgrade.py 等文件
```

### 步骤2：执行自动升级

```bash
# 运行升级脚本
python3 upgrade.py

# 查看升级过程（另开终端）
tail -f upgrade.log
```

### 步骤3：升级过程监控

升级脚本会自动执行以下步骤：

1. **查找当前安装** 📍
   ```
   找到当前安装：/home/user/question_bank_system_complete_v2
   ```

2. **创建备份** 💾
   ```
   开始备份当前版本到：/home/user/atcn_backups/atcn_backup_20250101_120000
   备份完成
   ```

3. **停止服务** ⏹️
   ```
   停止当前服务...
   服务已成功停止
   ```

4. **部署新版本** 📦
   ```
   开始部署新版本...
   新版本代码部署完成
   ```

5. **更新依赖** 🔄
   ```
   更新Python依赖...
   依赖更新完成
   ```

6. **数据库迁移** 🗄️
   ```
   检查数据库迁移...
   数据库迁移成功
   ```

7. **启动服务** ▶️
   ```
   启动服务在端口 5000...
   服务启动成功，端口：5000
   ```

8. **健康检查** ✅
   ```
   执行健康检查，端口：5000
   健康检查通过
   🎉 升级成功完成！
   ```

## ✅ 验证升级结果

### 1. 检查系统状态

```bash
# 检查服务是否运行
ps aux | grep main.py

# 检查端口是否监听
netstat -tlnp | grep :5000

# 访问系统
curl http://localhost:5000
```

### 2. 登录系统验证

1. 打开浏览器访问：`http://您的服务器IP:5000`
2. 确认页面标题显示为"ATcn考试系统"
3. 使用管理员账户登录
4. 检查各功能模块是否正常工作

### 3. 功能验证清单

- [ ] 系统名称已更新为"ATcn考试系统"
- [ ] 前台注册按钮已移除
- [ ] 管理员可以在后台添加用户
- [ ] 用户可以修改自己的密码
- [ ] 题库导入功能正常
- [ ] 考试功能正常

## 🔧 故障排除

### 升级失败回滚

如果升级过程中出现问题，脚本会自动回滚：

```
升级过程中出现错误：...
开始回滚...
回滚成功
❌ 升级失败！系统已回滚到原版本。
```

### 手动回滚

如果需要手动回滚到某个备份版本：

```bash
# 查看可用备份
ls -la ~/atcn_backups/

# 手动回滚到指定备份
cd ~/atcn_backups/
./manual_rollback.sh atcn_backup_20250101_120000
```

### 常见问题解决

#### 1. 端口占用问题

```bash
# 查找占用5000端口的进程
lsof -i :5000

# 强制停止进程
kill -9 <进程ID>
```

#### 2. 权限问题

```bash
# 检查文件权限
ls -la ~/question_bank_system_complete_v2/

# 修复权限
chmod +x ~/question_bank_system_complete_v2/src/main.py
```

#### 3. 虚拟环境问题

```bash
# 重新创建虚拟环境
cd ~/question_bank_system_complete_v2/
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📝 升级日志

升级过程的详细日志保存在：

- 升级日志：`upgrade.log`
- 备份位置：`~/atcn_backups/`
- 系统日志：通过 `journalctl` 查看

## 🎉 升级完成后

### 1. 清理工作

```bash
# 删除升级临时文件
rm -rf ~/atcn_upgrade_temp/

# 保留最近3个备份，删除旧备份
cd ~/atcn_backups/
ls -t | tail -n +4 | xargs rm -rf
```

### 2. 系统优化

```bash
# 重启服务以确保稳定性
cd ~/question_bank_system_complete_v2/
./start.sh
```

### 3. 通知用户

向系统用户发送升级完成通知，告知新功能和变更。

## 📞 技术支持

如果在升级过程中遇到问题，请：

1. 查看升级日志：`cat upgrade.log`
2. 检查系统状态：`systemctl status question-bank`
3. 联系技术支持并提供详细的错误信息

---

**⚠️ 重要提醒**：
- 升级前请确保有充足的磁盘空间
- 建议在业务低峰期进行升级
- 升级过程中请勿手动干预
- 如有疑问请先在测试环境验证 