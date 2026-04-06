# GitHub Trending Report

GitHub Trending 每日分析推送服务。通过 GitHub Actions 定时抓取 Trending Top 20，用 AI 生成因果链完备的结构化分析报告，推送到企业微信群。

## 特性

- 每天自动抓取 GitHub Trending Top 20（全语言）
- OSSInsight API 优先，自动降级到页面爬取
- AI 生成因果链完备的分析（背景→痛点→现有方案不足→解决思路→时机）
- 企业微信群机器人推送
- Prompt 模板独立管理，方便调优
- 可配置，易扩展

## 配置

### 1. Fork 本仓库

### 2. 设置 Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 |
|---|---|
| `LLM_API_KEY` | OpenAI API key |
| `WECHAT_WEBHOOK_URL` | 企业微信群机器人 Webhook 地址 |

`GITHUB_TOKEN` 由 GitHub Actions 自动提供。

### 3. 自定义配置

编辑 `config.yml` 调整：
- `trending.count` — 分析仓库数量
- `trending.period` — 时间范围
- `llm.model` — AI 模型

### 4. 自定义 Prompt

编辑 `prompts/analyze-repo.txt` 调整分析的角度和格式。

## 手动触发

在 GitHub Actions 页面点击 "Run workflow" 即可手动执行。

## 扩展

新增 job 只需：
1. 在 `.github/workflows/` 加 workflow 文件
2. 在 `prompts/` 加 prompt 模板
3. 在 `scripts/` 加数据源适配（如需要）

## 本地开发

```bash
pip install -r requirements.txt
export LLM_API_KEY=your-key
export WECHAT_WEBHOOK_URL=your-webhook-url
python -m scripts.main
```
