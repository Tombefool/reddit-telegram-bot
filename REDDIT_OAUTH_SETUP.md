# Reddit OAuth 配置指南

## 为什么需要 OAuth？

Reddit 的公开 API 经常返回 403 错误，特别是当请求频率较高时。使用 OAuth 认证可以显著提高成功率。

## 如何获取 Reddit OAuth 凭据

### 1. 创建 Reddit 应用

1. 访问 [Reddit 应用管理页面](https://www.reddit.com/prefs/apps)
2. 点击 "Create App" 或 "Create Another App"
3. 填写应用信息：
   - **Name**: `Reddit News Bot` (或任何你喜欢的名称)
   - **App type**: 选择 `script`
   - **Description**: `A bot to fetch news from Reddit` (可选)
   - **About URL**: 留空
   - **Redirect URI**: `http://localhost:8080` (必须填写，但不会被使用)

### 2. 获取凭据

创建应用后，你会看到：
- **Client ID**: 在应用名称下方的一串字符
- **Client Secret**: 在 "secret" 字段中的长字符串

### 3. 配置环境变量

在你的 `.env` 文件中添加：

```bash
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
```

### 4. 测试配置

运行以下命令测试 OAuth 是否工作：

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
from reddit_fetcher import get_reddit_oauth_token
token = get_reddit_oauth_token()
print('OAuth Token:', 'Success' if token else 'Failed')
"
```

## 注意事项

- OAuth token 有效期为 1 小时，系统会自动刷新
- 如果仍然遇到 403 错误，可能是 Reddit 的临时限制
- 建议设置合理的请求间隔，避免被限流

## 故障排除

### 常见错误

1. **"invalid_client"**: 检查 Client ID 和 Secret 是否正确
2. **"unauthorized_client"**: 确保应用类型设置为 "script"
3. **403 错误持续**: 可能需要等待一段时间或使用代理

### 备用方案

如果 OAuth 配置困难，系统会：
1. 自动回退到公开 API
2. 使用多种 User-Agent 轮换
3. 实现重试机制
4. 依赖 YouTube 和 Truth Social 作为主要内容源
