# 🔧 测试配置说明

## 📱 测试消息控制

### 问题
GitHub Actions 每天都会发送测试消息到你的 Telegram，可能会打扰到你。

### 解决方案

#### 1. 禁用测试消息（推荐）
在 GitHub Secrets 中添加：
```
SEND_TEST_MESSAGE=false
```

#### 2. 调整运行频率
已修改为每周一运行一次，而不是每天：
- **之前**: 每天 09:00（北京时间）
- **现在**: 每周一 09:00（北京时间）

#### 3. 完全禁用自动运行
如果你想完全禁用自动运行，可以：
1. 进入 GitHub 仓库的 "Actions" 页面
2. 找到 "Daily Reddit Bot" 工作流
3. 点击 "Disable workflow"

## ⚙️ 当前配置

### 运行频率
- **自动运行**: 每天 09:00 和 18:00（北京时间）
- **手动触发**: 支持在 Actions 页面手动运行

### 测试消息
- **默认**: 禁用测试消息发送
- **启用**: 设置 `SEND_TEST_MESSAGE=true`

### 内容推送
- **Truth Social**: 特朗普最新动态
- **YouTube**: 默认频道内容
- **Reddit**: 财经板块（如果可用）

## 🛠️ 自定义配置

### 修改运行时间
编辑 `.github/workflows/daily.yml`：
```yaml
schedule:
  - cron: '0 1 * * *'   # 09:00 北京时间
  - cron: '0 10 * * *'  # 18:00 北京时间
  - cron: '0 1 * * 1'   # 每周一 09:00
  - cron: '0 1 1 * *'   # 每月1号 09:00
```

### 启用测试消息
在 GitHub Secrets 中设置：
```
SEND_TEST_MESSAGE=true
```

### 完全静默运行
设置以下环境变量：
```
SEND_TEST_MESSAGE=false
DRY_RUN=1  # 仅测试，不发送任何消息
```

## 📊 运行状态检查

你可以在以下位置查看运行状态：
1. **GitHub Actions**: 仓库的 "Actions" 标签页
2. **Telegram**: 只有内容推送消息（测试消息已禁用）
3. **日志**: Actions 页面查看详细日志

## 🔄 恢复设置

如果需要恢复之前的设置：
1. 将 `SEND_TEST_MESSAGE` 设置为 `true`
2. 将 cron 表达式改回 `'0 1 * * *'`（每天运行）
