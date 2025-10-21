# Reddit Telegram 自动推送机器人

🤖 一个轻量级的 Python 项目，每天北京时间 09:00 自动抓取 Reddit 股票和加密货币板块的热门帖子，通过 Telegram 机器人推送。

## ✨ 功能特性

- 🔄 **自动定时推送**: 每天北京时间 09:00 自动运行
- 📊 **多板块抓取**: 覆盖 stocks、wallstreetbets、investing、cryptocurrency、bitcoin 等热门板块
- 🤖 **智能摘要**: 支持 Gemini API 生成中文摘要（可选）
- 📱 **Telegram 推送**: 格式化消息推送到指定 Telegram 群组/频道
- ☁️ **免费部署**: 使用 Render Cron Job，稳定可靠
- 🛡️ **稳定可靠**: 包含错误处理和重试机制

## 📋 前置要求

- Render 账号（免费）
- Telegram 账号
- （可选）Google Gemini API Key

## 🚀 快速开始

### 1. Fork 或 Clone 仓库

```bash
git clone https://github.com/your-username/reddit-telegram-bot.git
cd reddit-telegram-bot
```

### 2. 创建 Telegram Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示设置机器人名称和用户名
4. 保存获得的 Bot Token

**你的 Bot Token**: `8277624200:AAFbcpacMXFq5Mesj4agPO95-o5zuKWifpQ`
**你的 Chat ID**: `8160481050`

### 3. 配置 GitHub Secrets

在 GitHub 仓库中设置以下 Secrets：

1. 进入仓库 → Settings → Secrets and variables → Actions
2. 点击 "New repository secret" 添加：

| Secret 名称 | 值 | 说明 |
|------------|-----|------|
| `TELEGRAM_BOT_TOKEN` | `8277624200:AAFbcpacMXFq5Mesj4agPO95-o5zuKWifpQ` | Telegram Bot Token |
| `CHAT_ID` | `8160481050` | Telegram 聊天 ID |
| `GEMINI_API_KEY` | `AIzaSyBmEIjAe1LQAudfj-rRr5QDj0zcCpZpg2Y` | Gemini API Key |

### 4. 启用 GitHub Actions

1. 确保仓库的 Actions 功能已启用
2. 推送代码到 GitHub
3. 进入 Actions 页面查看工作流状态

### 5. 测试运行

1. 进入 Actions 页面
2. 选择 "Daily Reddit Bot" 工作流
3. 点击 "Run workflow" 手动触发测试

## 📁 项目结构

```
reddit-telegram-bot/
├── 核心程序
│   ├── main.py                    # 主程序入口（推荐使用）
│   └── main_comprehensive_final.py # 备用程序（Render 部署）
├── 功能模块
│   ├── reddit_fetcher.py          # Reddit 数据抓取
│   ├── telegram_sender.py         # Telegram 消息发送
│   ├── summarizer.py              # AI 文本摘要
│   ├── social_fetcher.py          # 社交媒体抓取
│   ├── us_china_news_fetcher.py   # 中美关系新闻
│   └── international_relations_fetcher.py # 国际关系动态
├── 配置文件
│   ├── requirements.txt           # Python 依赖
│   ├── env.example               # 环境变量示例
│   ├── sources.json              # 数据源配置
│   └── render.yaml               # Render 部署配置
├── 部署文件
│   ├── .github/workflows/daily.yml # GitHub Actions
│   └── run_bot.sh                # 运行脚本
├── 测试文件
│   ├── test_minimal.py           # 最小化测试
│   └── check_sources_health.py   # 源健康检查
└── 文档
    ├── README.md                 # 项目说明
    └── 各种分析报告
```

## 🔧 本地开发

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `env.example` 为 `.env` 并填入你的配置：

```bash
cp env.example .env
```

编辑 `.env` 文件：

```env
TELEGRAM_BOT_TOKEN=8277624200:AAFbcpacMXFq5Mesj4agPO95-o5zuKWifpQ
CHAT_ID=8160481050
GEMINI_API_KEY=AIzaSyBmEIjAe1LQAudfj-rRr5QDj0zcCpZpg2Y
```

### 运行测试

```bash
python main.py
```

## 📱 消息格式示例

```
🔔 每日 Reddit 财经要闻 (股票 & 加密货币)

【r/stocks】
1️⃣ [Tesla stock analysis shows strong Q4 performance](https://reddit.com/r/stocks/...)
⭐ 评分: 1234
💬 特斯拉第四季度业绩强劲，分析师看好长期前景...

【r/bitcoin】
2️⃣ [Bitcoin reaches new all-time high amid institutional adoption](https://reddit.com/r/bitcoin/...)
⭐ 评分: 5678
💬 比特币在机构采用推动下创历史新高...

📅 更新时间: 2025-01-12 09:00 (UTC+8)
🤖 由 Reddit API 提供 | Gemini 可选摘要
```

## ⚙️ 配置说明

### 目标板块

默认抓取以下 Reddit 板块：
- `stocks` - 股票讨论
- `wallstreetbets` - 华尔街赌注
- `investing` - 投资讨论
- `cryptocurrency` - 加密货币
- `bitcoin` - 比特币

### 运行时间

- **GitHub Actions**: 每天 UTC 01:00（北京时间 09:00）
- **手动触发**: 支持在 Actions 页面手动运行

### Gemini API（可选）

如果设置了 `GEMINI_API_KEY`，机器人会使用 Gemini API 生成中文摘要。否则使用简单文本截断。

获取 Gemini API Key：
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建新的 API Key
3. 添加到 GitHub Secrets

## 🛠️ 自定义配置

### 修改目标板块

编辑 `main.py` 中的 `get_target_subreddits()` 函数：

```python
def get_target_subreddits():
    return [
        'stocks',
        'wallstreetbets', 
        'investing',
        'cryptocurrency',
        'bitcoin',
        'your_custom_subreddit'  # 添加自定义板块
    ]
```

### 修改运行时间

编辑 `.github/workflows/daily.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC 01:00 = 北京时间 09:00
```

### 修改帖子数量

编辑 `main.py` 中的 `fetch_multiple_subreddits()` 调用：

```python
posts = fetch_multiple_subreddits(subreddits, posts_per_subreddit=3)  # 每个板块3个帖子
```

## 🔍 故障排除

### 常见问题

1. **Telegram 消息发送失败**
   - 检查 Bot Token 是否正确
   - 确认 Chat ID 是否正确
   - 确保机器人已添加到群组/频道

2. **Reddit 数据抓取失败**
   - 检查网络连接
   - Reddit API 可能有临时限制

3. **GitHub Actions 运行失败**
   - 检查 Secrets 配置
   - 查看 Actions 日志

### 获取 Chat ID

如果不知道 Chat ID，可以：

1. **方法一（推荐）**: 直接向机器人发送消息
   - 在 Telegram 中搜索 `@Redditjaredbot`
   - 点击 "START" 开始对话
   - 发送任意消息（如 "hello"）
   - 然后运行以下命令获取 Chat ID：
   ```bash
   curl "https://api.telegram.org/bot8277624200:AAFbcpacMXFq5Mesj4agPO95-o5zuKWifpQ/getUpdates"
   ```
   - 在返回的 JSON 中查找 `"chat":{"id":数字}` 字段

2. **方法二**: 使用 Python 脚本
   ```python
   import requests
   response = requests.get('https://api.telegram.org/bot8277624200:AAFbcpacMXFq5Mesj4agPO95-o5zuKWifpQ/getUpdates')
   print(response.json())
   ```

3. **方法三**: 如果是群组，需要先将机器人添加到群组，然后发送消息

## 📊 监控和日志

- GitHub Actions 提供详细的运行日志
- 每次运行都会显示成功/失败状态
- 支持手动触发进行测试

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- Reddit API 提供数据支持
- Telegram Bot API 提供消息推送
- Google Gemini API 提供智能摘要（可选）
- GitHub Actions 提供免费自动化服务

---

**注意**: 本项目仅用于学习和个人使用，请遵守 Reddit 和 Telegram 的使用条款。
