# 📁 项目结构说明

## 🎯 核心文件

### 主程序
- **`main.py`** - 主程序入口（推荐使用）
  - 功能最全，集成所有模块
  - 支持多源数据抓取
  - 包含 AI 摘要和智能过滤
  - 用于 GitHub Actions 部署

- **`main_comprehensive_final.py`** - 备用程序
  - 功能完整，结构清晰
  - 用于 Render 部署
  - 包含健康监控和缓存管理

### 功能模块
- **`reddit_fetcher.py`** - Reddit 数据抓取
- **`telegram_sender.py`** - Telegram 消息发送
- **`summarizer.py`** - AI 文本摘要（Gemini API）
- **`social_fetcher.py`** - 社交媒体抓取（YouTube、Nitter）
- **`us_china_news_fetcher.py`** - 中美关系新闻专题
- **`international_relations_fetcher.py`** - 国际关系动态
- **`truth_social_fetcher.py`** - Truth Social 抓取
- **`truth_social_playwright.py`** - Truth Social Playwright 抓取

## ⚙️ 配置文件

### 环境配置
- **`env.example`** - 环境变量示例（已优化）
- **`requirements.txt`** - Python 依赖

### 数据源配置
- **`sources.json`** - 新闻源配置
- **`us_china_sources.py`** - 中美关系新闻源

### 部署配置
- **`.github/workflows/daily.yml`** - GitHub Actions 工作流
- **`render.yaml`** - Render 部署配置
- **`run_bot.sh`** - 运行脚本

## 🧪 测试文件

- **`test_minimal.py`** - 最小化测试
- **`test_apnews.py`** - AP News 测试
- **`test_gnews.py`** - GNews API 测试
- **`check_sources_health.py`** - 数据源健康检查
- **`deploy_check.py`** - 部署验证

## 📚 文档

- **`README.md`** - 项目主要说明
- **`SOLUTION_SUMMARY.md`** - 解决方案总结
- **`SYSTEM_CAPACITY_ANALYSIS.md`** - 系统承载能力分析
- **`US_CHINA_INTEGRATION_SUMMARY.md`** - 中美关系集成总结
- **`IR_RESEARCH_RECOMMENDATIONS.md`** - 国际关系研究建议
- **`REDDIT_OAUTH_SETUP.md`** - Reddit OAuth 配置指南
- **`TEST_CONFIGURATION.md`** - 测试配置说明
- **`render_deploy.md`** - Render 部署指南

## 🗂️ 数据文件

- **`news_cache.db`** - 新闻缓存数据库
- **`sources_health.db`** - 数据源健康状态数据库
- **`truth_cache.json`** - Truth Social 缓存

## 🚀 使用建议

### 开发环境
```bash
# 使用主程序
python main.py

# 测试功能
python test_minimal.py
```

### 生产环境
- **GitHub Actions**: 使用 `main.py`
- **Render**: 使用 `main_comprehensive_final.py`

### 配置管理
1. 复制 `env.example` 为 `.env`
2. 填写必需的环境变量
3. 可选配置根据需要设置

## 📝 维护说明

### 添加新功能
1. 在相应模块文件中添加功能
2. 在 `main.py` 中集成调用
3. 更新文档说明

### 修改配置
1. 更新 `env.example` 文件
2. 更新相关文档
3. 测试配置有效性

### 部署更新
1. 确保主程序功能正常
2. 更新部署配置文件
3. 测试部署流程
