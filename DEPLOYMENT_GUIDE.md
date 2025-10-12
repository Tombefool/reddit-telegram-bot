# 🚀 Reddit Telegram Bot 部署指南

## 📋 部署检查清单

### ✅ 已完成
- [x] 项目代码完成
- [x] Git 仓库初始化
- [x] 代码提交到本地仓库
- [x] Telegram Bot 创建和测试
- [x] Gemini API 集成和测试

### 🔄 需要手动完成

#### 1. 创建 GitHub 仓库
1. 访问 [GitHub](https://github.com)
2. 点击 "New repository"
3. 仓库名称: `reddit-telegram-bot`
4. 描述: `Reddit Telegram 自动推送机器人`
5. 设置为 Public（免费使用 GitHub Actions）
6. 不要初始化 README（我们已经有了）
7. 点击 "Create repository"

#### 2. 推送代码到 GitHub
```bash
# 添加远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/reddit-telegram-bot.git

# 推送代码
git branch -M main
git push -u origin main
```

#### 3. 配置 GitHub Secrets
1. 进入仓库页面
2. 点击 "Settings" 标签
3. 左侧菜单选择 "Secrets and variables" → "Actions"
4. 点击 "New repository secret" 添加以下三个 Secrets：

| Secret 名称 | 值 | 说明 |
|------------|-----|------|
| `TELEGRAM_BOT_TOKEN` | `8277624200:AAFbcpacMXFq5Mesj4agPO95-o5zuKWifpQ` | Telegram Bot Token |
| `CHAT_ID` | `8160481050` | Telegram 聊天 ID |
| `GEMINI_API_KEY` | `AIzaSyBmEIjAe1LQAudfj-rRr5QDj0zcCpZpg2Y` | Gemini API Key |

#### 4. 启用 GitHub Actions
1. 进入仓库的 "Actions" 标签
2. 如果提示启用 Actions，点击 "I understand my workflows, go ahead and enable them"
3. 查看 "Daily Reddit Bot" 工作流

#### 5. 测试部署
1. 在 Actions 页面找到 "Daily Reddit Bot" 工作流
2. 点击 "Run workflow" 按钮
3. 选择 "main" 分支
4. 点击 "Run workflow" 开始测试
5. 等待运行完成，检查是否成功

#### 6. 验证自动运行
- 工作流会在每天北京时间 09:00（UTC 01:00）自动运行
- 可以在 Actions 页面查看运行历史和日志

## 🔧 故障排除

### 常见问题

1. **GitHub Actions 运行失败**
   - 检查 Secrets 是否正确配置
   - 查看 Actions 日志中的错误信息
   - 确保仓库是 Public（免费账户限制）

2. **Telegram 消息发送失败**
   - 验证 Bot Token 和 Chat ID 是否正确
   - 确保机器人已添加到聊天中

3. **Reddit 数据抓取失败**
   - 检查网络连接
   - Reddit API 可能有临时限制

## 📱 预期结果

成功部署后，你会在 Telegram 中收到类似以下格式的消息：

```
🔔 每日 Reddit 财经要闻 (股票 & 加密货币)

【r/stocks】
1️⃣ [Tesla stock analysis shows strong Q4 performance](https://reddit.com/...)
⭐ 评分: 1234
💬 特斯拉第四季度业绩强劲，分析师看好长期前景...

【r/cryptocurrency】
2️⃣ [Bitcoin reaches new all-time high](https://reddit.com/...)
⭐ 评分: 5678
💬 比特币在机构采用推动下创历史新高...

📅 更新时间: 2025-01-12 09:00 (UTC+8)
🤖 由 Reddit API 提供 | Gemini 智能摘要
```

## 🎉 部署完成

完成上述步骤后，你的 Reddit Telegram Bot 将：
- 每天北京时间 09:00 自动运行
- 抓取 Reddit 财经板块热门帖子
- 使用 Gemini API 生成中文摘要
- 推送到你的 Telegram 聊天

享受你的自动化 Reddit 财经资讯推送服务！
