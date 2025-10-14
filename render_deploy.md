# 🚀 Render 部署指南

## 为什么选择 Render？

相比 GitHub Actions，Render 有以下优势：
- ✅ **更简单**：无需复杂的 YAML 配置
- ✅ **更稳定**：专门为定时任务设计
- ✅ **更直观**：Web 界面管理，实时日志
- ✅ **免费额度**：每月 750 小时免费
- ✅ **自动重启**：任务失败自动重试

## 📋 部署步骤

### 1. 准备代码
确保你的 GitHub 仓库包含：
- `main.py` - 主程序
- `requirements.txt` - Python 依赖
- `render.yaml` - Render 配置文件
- 其他模块文件

### 2. 连接 GitHub 到 Render

1. 访问 [Render Dashboard](https://dashboard.render.com/)
2. 点击 "New +" → "Cron Job"
3. 连接你的 GitHub 仓库
4. 选择 `reddit-telegram-bot` 仓库

### 3. 配置 Cron Job

**基本信息：**
- **Name**: `reddit-telegram-bot`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Schedule**: `0 1 * * *` (每天 UTC 01:00，即北京时间 09:00)

**环境变量：**
在 Environment Variables 部分添加：
- `TELEGRAM_BOT_TOKEN`: `你的 Telegram Bot Token`
- `CHAT_ID`: `你的 Chat ID`
- `GEMINI_API_KEY`: `你的 Gemini API Key` (可选)

### 4. 部署和测试

1. 点击 "Create Cron Job"
2. 等待构建完成
3. 点击 "Manual Trigger" 测试运行
4. 查看 "Logs" 标签页的实时日志

## 🔧 配置说明

### render.yaml 配置
```yaml
services:
  - type: cron
    name: reddit-telegram-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    schedule: "0 1 * * *"  # 每天 UTC 01:00
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: CHAT_ID
        sync: false
      - key: GEMINI_API_KEY
        sync: false
```

### 时间调度
- **Render Cron**: `0 1 * * *` (UTC 01:00)
- **北京时间**: 09:00
- **时区**: Render 使用 UTC，我们代码中已处理时区转换

## 📊 监控和管理

### 实时监控
- **Dashboard**: 查看任务状态和运行历史
- **Logs**: 实时查看运行日志
- **Metrics**: 查看资源使用情况

### 手动操作
- **Manual Trigger**: 手动触发任务
- **Pause/Resume**: 暂停或恢复定时任务
- **Restart**: 重启服务

## 🆚 与 GitHub Actions 对比

| 特性 | GitHub Actions | Render |
|------|----------------|--------|
| 配置复杂度 | 高 (YAML) | 低 (Web界面) |
| 调试难度 | 高 | 低 |
| 稳定性 | 中等 | 高 |
| 免费额度 | 2000分钟/月 | 750小时/月 |
| 实时日志 | 需要下载 | 直接查看 |
| 手动触发 | 支持 | 支持 |

## 🎯 预期结果

部署成功后，你将获得：
- ✅ 每天北京时间 09:00 自动运行
- ✅ 实时日志监控
- ✅ 失败自动重试
- ✅ 简单易用的管理界面

## 🔧 故障排除

### 常见问题

1. **构建失败**
   - 检查 `requirements.txt` 是否正确
   - 查看构建日志中的错误信息

2. **运行时错误**
   - 检查环境变量是否正确设置
   - 查看运行日志中的错误信息

3. **定时任务不运行**
   - 检查 Cron 表达式是否正确
   - 确认服务状态为 "Active"

### 调试步骤

1. 使用 "Manual Trigger" 测试
2. 查看 "Logs" 标签页
3. 检查环境变量设置
4. 验证 Telegram API 连接

## 🎉 开始部署

现在你可以：
1. 访问 [Render Dashboard](https://dashboard.render.com/)
2. 按照上述步骤创建 Cron Job
3. 配置环境变量
4. 测试运行

Render 部署比 GitHub Actions 简单得多，应该能快速解决你的问题！
