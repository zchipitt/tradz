# Tradz 多源交易信号系统 - 详细使用指南

## 目录

1. [系统概述](#1-系统概述)
2. [安装配置](#2-安装配置)
3. [配置详解](#3-配置详解)
4. [运行系统](#4-运行系统)
5. [信号解读](#5-信号解读)
6. [定时任务](#6-定时任务)
7. [故障排除](#7-故障排除)
8. [高级用法](#8-高级用法)
9. [Claude AI 报告生成](#9-claude-ai-报告生成)
10. [Web 仪表盘](#10-web-仪表盘)
11. [数据库与实体解析](#11-数据库与实体解析)

---

## 1. 系统概述

### 1.1 功能简介

Tradz 是一个多源数据聚合的自动化交易信号系统，使用 4 维评分体系和 Claude AI 生成专业级分析报告。

#### 核心数据源

| 功能模块 | 说明 | 数据延迟 |
|---------|------|---------|
| 📈 **美股监控** | 通过 yfinance 获取美国股票数据 | 15-20分钟 |
| 💰 **加密货币监控** | 通过 ccxt 获取主流加密货币数据 | 实时 |
| 🏛️ **国会议员交易** | House/Senate 交易披露 | ~45天 |
| 🏦 **对冲基金 13F** | SEC EDGAR 机构持仓 | 季度，~45天 |
| 🎰 **Polymarket** | 预测市场赔率 | 实时 |
| 📰 **新闻聚合** | Yahoo Finance + NewsAPI | 实时 |
| 📋 **SEC 年报** | 10-K, 10-Q, 8-K 文件 | 实时 |

#### 4 维信号评分

| 维度 | 说明 | 数据来源 |
|-----|------|---------|
| 📊 **异常评分** | 价格/成交量/波动率的 Z-score 偏离 | 市场数据 |
| 🎯 **催化剂评分** | 新闻、SEC 文件、预测市场事件 | 多源信息 |
| 💸 **资金流评分** | 国会交易、13F 机构资金流 | 披露数据 |
| ✅ **置信度评分** | 数据质量和跨源验证 | 质量指标 |

#### 智能报告

| 功能模块 | 说明 |
|---------|------|
| 🤖 **Claude AI 报告** | 使用 Claude Code CLI + MCP Skills 生成高质量报告 |
| 🔍 **实时搜索** | Claude 使用 Tavily 搜索最新新闻 |
| 📊 **跨源分析** | 识别多数据源之间的关联模式 |
| 🎯 **信号生成** | 基于 4 维评分体系 |
| 📧 **邮件报告** | 通过 SMTP 发送每日报告 |
| 🔒 **模拟运行** | 支持 dry-run 模式测试 |

#### 数据基础设施

| 功能模块 | 说明 |
|---------|------|
| 🗄️ **DuckDB 数据库** | 实体、观察、事件、信号的持久化存储 |
| 🔗 **实体解析** | Ticker/CIK/公司名称映射，支持 SEC 数据同步 |
| 📋 **事实表** | 为 LLM 叙事生成提供确定性事实 |

#### Web 仪表盘

| 功能模块 | 说明 |
|---------|------|
| 🖥️ **React 仪表盘** | 交互式信号可视化界面 |
| 🔌 **FastAPI 后端** | 信号、数据源和报告的 REST API |
| 🔄 **实时刷新** | 手动和自动数据刷新功能 |

#### 券商集成（可选）

| 功能模块 | 说明 |
|---------|------|
| 💼 **IBKR** | Interactive Brokers 账户持仓追踪 |

### 1.2 系统架构

```
tradz/
├── config.yaml              # 监控列表、数据源和阈值配置
├── .env                     # API 密钥和 SMTP 凭据（不要提交到 Git！）
├── .env.example             # 环境变量模板
├── requirements.txt         # Python 依赖
├── prompts/                 # Claude 提示词模板
│   ├── report_system.md     # 系统提示词（定义分析师角色）
│   └── report_user.md       # 用户提示词模板（包含数据占位符）
├── data/                    # 聚合的原始数据（每日 JSON）
│   ├── YYYY-MM-DD.json      # 每日聚合数据
│   └── tradz.duckdb         # DuckDB 数据库
├── reports/                 # 生成的报告目录
│   ├── YYYY-MM-DD.json      # 原始信号数据
│   └── YYYY-MM-DD.md        # Markdown 报告
├── logs/                    # 日志目录（定时任务使用）
├── scripts/
│   ├── nightly.sh           # 主执行脚本
│   ├── local_up.sh          # 一键启动后端+前端
│   ├── local_down.sh        # 一键停止
│   ├── verify_db.py         # 数据库验证
│   ├── verify_entities.py   # 实体解析验证
│   ├── verify_signals.py    # 信号生成验证
│   └── verify_facts.py      # 事实生成验证
├── api/                     # FastAPI 后端
│   ├── main.py              # API 入口
│   ├── config.py            # API 配置
│   ├── routers/             # API 路由
│   │   ├── signals.py       # 信号接口
│   │   ├── sources.py       # 数据源接口
│   │   └── reports.py       # 报告接口
│   ├── schemas/             # Pydantic 模型
│   └── services/            # 业务逻辑
│       ├── signal_service.py
│       ├── aggregator_service.py
│       └── cache_service.py
├── frontend/                # React 仪表盘
│   ├── src/
│   │   ├── App.tsx          # 根组件
│   │   ├── pages/           # 页面组件
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Sources.tsx
│   │   │   └── UsageGuide.tsx
│   │   ├── components/      # UI 组件
│   │   └── hooks/           # React 钩子
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   └── USAGE_GUIDE_CN.md    # 本文件
└── src/tradz/
    ├── run_nightly.py       # 主入口程序
    ├── aggregator.py        # 多源数据聚合器
    ├── database.py          # DuckDB 数据库层
    ├── models.py            # 数据模型（Entity, Observation, Event, Signal）
    ├── entity_resolver.py   # 实体解析
    ├── scoring.py           # 4 维信号评分
    ├── signals.py           # 信号生成逻辑
    ├── claude_reporter.py   # Claude Code CLI 集成
    ├── report.py            # 模板报告渲染（备用）
    ├── emailer.py           # 邮件发送器
    ├── reporting/
    │   └── fact_generator.py # 事实表生成
    └── sources/
        ├── equities.py      # yfinance 数据源
        ├── crypto.py        # ccxt 数据源
        ├── congress.py      # 国会议员交易
        ├── hedgefunds.py    # 对冲基金 13F
        ├── polymarket.py    # Polymarket 预测市场
        ├── news.py          # 新闻聚合
        ├── sec_filings.py   # SEC 年报
        └── brokers/
            ├── base.py      # 券商基类
            └── ibkr.py      # IBKR 集成
```

### 1.3 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     Tradz 工作流程                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: 加载配置                                               │
│  - config.yaml (监控列表、阈值)                                  │
│  - .env (API 密钥、SMTP 凭据)                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: 聚合多源数据 (DataAggregator)                           │
│  ├── 股票数据 (yfinance)                                        │
│  ├── 加密货币 (ccxt)                                            │
│  ├── 国会议员交易 (Capitol Trades API)                          │
│  ├── 对冲基金 13F (SEC EDGAR)                                   │
│  ├── Polymarket 赔率                                            │
│  ├── 新闻聚合 (Yahoo Finance + NewsAPI)                         │
│  ├── SEC 年报 (10-K, 10-Q, 8-K)                                 │
│  └── [可选] 券商持仓 (IBKR)                                      │
│  输出: data/YYYY-MM-DD.json                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: 实体解析 (EntityResolver)                               │
│  - 同步 SEC 股票代码映射                                          │
│  - 解析 Ticker/CIK/公司名称                                       │
│  - 存储到 DuckDB entities 表                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: 生成 4 维信号评分 (Scorer)                              │
│  - 异常评分 (anomaly_score): Z-score 偏离                        │
│  - 催化剂评分 (catalyst_score): 新闻、SEC、Polymarket            │
│  - 资金流评分 (flow_score): 国会、13F                            │
│  - 置信度评分 (confidence_score): 数据质量                       │
│  输出: 综合关注度 attention_score                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: 报告生成                                                │
│  ┌──────────────────────┐    ┌──────────────────────┐           │
│  │  Claude Code CLI     │ OR │  Template Fallback   │           │
│  │  (--dangerously-     │    │  (report.py)         │           │
│  │   skip-permissions)  │    │                      │           │
│  │  + MCP Skills        │    │                      │           │
│  │    - tavily-search   │    │                      │           │
│  │    - filesystem      │    │                      │           │
│  │    - sequential-     │    │                      │           │
│  │      thinking        │    │                      │           │
│  └──────────────────────┘    └──────────────────────┘           │
│  输出: reports/YYYY-MM-DD.md, reports/YYYY-MM-DD.json           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: 发送邮件 (EmailSender)                                  │
│  - SMTP 发送 (或 DRY_RUN 模式跳过)                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 安装配置

### 2.1 系统要求

- **Python**: 3.8+
- **Node.js**: 18+（用于前端和 Claude Code CLI）
- **操作系统**: macOS / Linux / Windows
- **网络**: 稳定的互联网连接

### 2.2 安装步骤

```bash
# 步骤 1: 进入项目目录
cd /path/to/tradz

# 步骤 2: 创建虚拟环境（如果还没有）
python3 -m venv .venv

# 步骤 3: 激活虚拟环境
source .venv/bin/activate    # macOS/Linux
# 或者
.venv\Scripts\activate       # Windows

# 步骤 4: 安装 Python 依赖
pip install -r requirements.txt

# 步骤 5: 安装 Claude Code CLI（可选，用于 AI 报告）
npm install -g @anthropic-ai/claude-code

# 步骤 6: 复制环境变量模板
cp .env.example .env

# 步骤 7: 编辑 .env 填写 API 密钥
vim .env  # 或使用你喜欢的编辑器
```

### 2.3 验证安装

```bash
# 激活环境
source .venv/bin/activate

# 检查 Python 依赖
python3 -c "import yfinance; import ccxt; import pandas; import duckdb; print('✅ Python 依赖安装成功')"

# 检查 Claude CLI（可选）
claude --version && echo '✅ Claude Code CLI 安装成功'

# 验证数据库
python3 scripts/verify_db.py
```

### 2.4 快速测试

```bash
# 模拟运行（不发送邮件）
./scripts/nightly.sh

# 或直接运行 Python 脚本
python3 -m src.tradz.run_nightly --skip-email
```

---

## 3. 配置详解

### 3.1 环境变量配置 (.env)

```bash
# 复制模板文件
cp .env.example .env

# 编辑 .env 文件
vim .env
```

**必填配置项：**

| 变量名 | 说明 | 示例值 |
|-------|------|--------|
| `DRY_RUN` | 模拟模式（1=不发送邮件，0=发送邮件） | `1` |
| `SMTP_HOST` | 邮件服务器地址 | `smtp.gmail.com` |
| `SMTP_PORT` | 邮件服务器端口 | `587` |
| `SMTP_USER` | 邮箱用户名 | `your@gmail.com` |
| `SMTP_PASS` | 邮箱密码/应用专用密码 | `xxxx-xxxx-xxxx` |
| `SMTP_FROM` | 发件人地址 | `your@gmail.com` |
| `SMTP_TO` | 收件人地址 | `your@gmail.com` |

**可选配置项（增强功能）：**

| 变量名 | 说明 | 示例值 |
|-------|------|--------|
| `ANTHROPIC_API_KEY` | Claude API 密钥 | `sk-ant-api03-...` |
| `NEWSAPI_KEY` | NewsAPI 密钥（增强新闻聚合） | `abc123...` |
| `SEC_USER_AGENT` | SEC EDGAR 请求标识 | `YourName your@email.com` |

**Gmail 配置说明：**

1. 登录 Gmail 账户
2. 启用两步验证：`设置 → 安全性 → 两步验证`
3. 生成应用专用密码：
   - 访问 https://myaccount.google.com/apppasswords
   - 选择"邮件"和"Mac"
   - 复制生成的 16 位密码到 `SMTP_PASS`

**常用邮件服务器配置：**

| 服务商 | SMTP_HOST | SMTP_PORT | 备注 |
|--------|-----------|-----------|------|
| Gmail | smtp.gmail.com | 587 | 需要应用专用密码 |
| QQ邮箱 | smtp.qq.com | 587 | 需要授权码 |
| 163邮箱 | smtp.163.com | 465 | 需要授权码 |
| Outlook | smtp.office365.com | 587 | 普通密码 |

### 3.2 监控列表配置 (config.yaml)

**股票监控：**

```yaml
equities:
  tickers:
    # 科技巨头
    - AAPL    # 苹果
    - MSFT    # 微软
    - GOOGL   # 谷歌
    - NVDA    # 英伟达
    - META    # Meta
    - TSLA    # 特斯拉
    - AMZN    # 亚马逊

    # 金融板块
    - JPM     # 摩根大通
    - GS      # 高盛
    - BAC     # 美国银行

    # ETF 指数
    - SPY     # 标普500 ETF
    - QQQ     # 纳斯达克 ETF
```

**加密货币监控：**

```yaml
crypto:
  exchange: "binance"  # 交易所（binance/coinbase/kraken）
  pairs:
    - BTC/USDT    # 比特币
    - ETH/USDT    # 以太坊
    - SOL/USDT    # Solana
    - BNB/USDT    # 币安币
```

### 3.3 信号阈值配置

```yaml
thresholds:
  # 价格变动阈值
  day_return_high: 5.0      # 日涨跌幅 >5% 视为强信号
  day_return_moderate: 3.0  # 日涨跌幅 >3% 视为中等信号
  week_return_high: 10.0    # 周涨跌幅 >10% 视为强信号
  week_return_moderate: 5.0 # 周涨跌幅 >5% 视为中等信号

  # 波动率阈值
  volatility_spike_high: 50.0     # 波动率增加 >50% 视为高波动
  volatility_spike_moderate: 25.0 # 波动率增加 >25% 视为中等波动

  # 成交量阈值（相对于30日均量）
  volume_high: 2.0      # 成交量 >2倍均值视为异常
  volume_moderate: 1.5  # 成交量 >1.5倍均值视为较高
```

### 3.4 数据源配置

**国会议员交易：**

```yaml
congress:
  enabled: true
  lookback_days: 30    # 获取过去 30 天的交易
  min_amount: 15000    # 最小交易金额阈值 ($)
```

**对冲基金 13F：**

```yaml
hedgefunds:
  enabled: true
  min_position_change_pct: 25.0  # 持仓变化超过 25% 才显示
  notable_funds:
    - "0001067983"  # Berkshire Hathaway
    - "0001350694"  # Citadel Advisors
    - "0001336528"  # Renaissance Technologies
    # ... 更多基金 CIK
```

**Polymarket 预测市场：**

```yaml
polymarket:
  enabled: true
  categories:
    - Economics
    - Crypto
    - Business
    - Politics
  max_markets: 20
```

**新闻聚合：**

```yaml
news:
  enabled: true
  max_articles_per_ticker: 10
  # NewsAPI 密钥在 .env 中配置
```

**SEC 年报：**

```yaml
sec_filings:
  enabled: true
  form_types:
    - 10-K  # 年报
    - 10-Q  # 季报
    - 8-K   # 重大事件
```

**券商集成（IBKR）：**

```yaml
broker:
  enabled: false  # 需要 TWS/Gateway 运行时设为 true
  type: ibkr
  host: "127.0.0.1"
  port: 7497      # TWS paper: 7497, TWS live: 7496
  client_id: 1
```

### 3.5 Claude 配置

```yaml
claude:
  enabled: true
  timeout: 300               # 超时时间（秒）
  skip_permissions: true     # 自动化运行时跳过权限确认
  fallback_to_template: true # Claude 失败时使用模板生成
```

---

## 4. 运行系统

### 4.1 命令行参数

```bash
python3 -m src.tradz.run_nightly [OPTIONS]
```

| 参数 | 说明 |
|-----|------|
| `--use-claude` | 强制使用 Claude 生成报告 |
| `--template-only` | 强制使用模板生成（跳过 Claude） |
| `--skip-email` | 跳过邮件发送 |

**使用示例：**

```bash
# 标准运行（自动选择报告生成方式）
python3 -m src.tradz.run_nightly

# 强制使用 Claude
python3 -m src.tradz.run_nightly --use-claude

# 仅使用模板（快速测试）
python3 -m src.tradz.run_nightly --template-only

# 跳过邮件发送（本地测试）
python3 -m src.tradz.run_nightly --skip-email

# 组合使用
python3 -m src.tradz.run_nightly --template-only --skip-email
```

### 4.2 一键启动/停止

```bash
# 启动环境（后端 8002 + 前端 5173）
./scripts/local_up.sh

# 停止环境
./scripts/local_down.sh
```

### 4.3 模拟运行（推荐首次使用）

```bash
# 确保 .env 中 DRY_RUN=1
# 运行脚本
./scripts/nightly.sh
```

**预期输出：**

```
================================================================================
🚀 Starting nightly trading signal generation (Multi-Source)
================================================================================
✅ Configuration loaded from config.yaml
✅ Environment variables loaded from .env
📅 Report date: 2026-01-19
✅ Claude Code CLI available
================================================================================
📊 Step 1: Aggregating data from all sources...
================================================================================
✅ Equities: Fetched 14/14 tickers
✅ Crypto: Fetched 10/10 pairs
✅ Congress trades: 25 recent trades
✅ Hedge fund 13F: 3 filings found
✅ Polymarket: 15 markets
✅ News: 45 articles
✅ SEC filings: 8 filings
✅ Data aggregated and saved to data/2026-01-19.json
   Sources fetched: 7
   Equities: 14
   Congress watchlist matches: 3
================================================================================
🔗 Step 2: Resolving entities...
================================================================================
✅ Entities synced from SEC
✅ Resolved 14 tickers to entity IDs
================================================================================
🎯 Step 3: Generating 4-dimensional signals...
================================================================================
✅ Generated 24 signals with 4D scoring
   Top by attention_score: NVDA (82.5), TSLA (78.3), BTC/USDT (75.1)
================================================================================
📝 Step 4: Generating report with Claude Code CLI...
================================================================================
✅ Report generated (8523 chars)
✅ Signals JSON saved to reports/2026-01-19.json
================================================================================
📧 Step 5: Sending email...
================================================================================
✅ Dry-run completed successfully
================================================================================
🎉 Nightly signal generation completed successfully!
================================================================================
Report files:
  - Data: data/2026-01-19.json
  - Database: data/tradz.duckdb
  - JSON: reports/2026-01-19.json
  - Markdown: reports/2026-01-19.md
  - Generated by: Claude Code CLI
================================================================================
```

### 4.4 查看生成的报告

```bash
# 查看报告目录
ls -la reports/

# 查看今天的 Markdown 报告
cat reports/$(date +%Y-%m-%d).md

# 查看今天的 JSON 数据
cat reports/$(date +%Y-%m-%d).json

# 查看聚合的原始数据
cat data/$(date +%Y-%m-%d).json | python3 -m json.tool | head -100
```

### 4.5 正式发送邮件

```bash
# 编辑 .env，设置 DRY_RUN=0
vim .env

# 重新运行
./scripts/nightly.sh
```

---

## 5. 信号解读

### 5.1 4 维信号评分

每个信号在 4 个维度上评分（各 0-100）：

| 维度 | 说明 | 数据来源 |
|-----|------|---------|
| **异常评分 (Anomaly)** | 价格/成交量/波动率的统计偏离 | Z-score 计算 |
| **催化剂评分 (Catalyst)** | 外部驱动事件的强度 | 新闻、SEC、Polymarket |
| **资金流评分 (Flow)** | 资金/仓位变动信号 | 国会交易、13F |
| **置信度评分 (Confidence)** | 数据质量和验证程度 | 多源覆盖、新鲜度 |

### 5.2 综合关注度评分

```
attention_score = anomaly × 0.30 + catalyst × 0.30 + flow × 0.25 + confidence × 0.15
```

| 分数区间 | 信号强度 | 建议操作 |
|---------|---------|---------|
| 80-100 | 🔴 极强 | 重点关注，可能有重大事件 |
| 65-79 | 🟠 强 | 值得关注 |
| 50-64 | 🟡 中等 | 保持观察 |
| 0-49 | 🟢 弱 | 正常波动，无需特别关注 |

### 5.3 各维度评分因素

**异常评分 (Anomaly)：**

| 因素 | 条件 | 影响 |
|------|------|------|
| 价格 Z-score | 偏离历史均值 | 主要因素 (50%) |
| 成交量 Z-score | 偏离历史均量 | 次要因素 (30%) |
| 波动率变化 | 7日 vs 30日波动率 | 辅助因素 (20%) |

**催化剂评分 (Catalyst)：**

| 因素 | 权重 | 说明 |
|------|------|------|
| SEC 8-K 文件 | +30 | 重大事件披露 |
| SEC 10-K/10-Q | +20 | 年报/季报 |
| Polymarket 变化 | +15 | 预测市场信号 |
| 新闻报道 | +10 | 每篇相关新闻 |

**资金流评分 (Flow)：**

| 因素 | 条件 | 加分 |
|------|------|------|
| 国会成员买入 | 新鲜度加权 | +15 |
| 国会成员卖出 | 新鲜度加权 | -10 |
| 13F 持仓变化 | 季度数据 | +5 |

**置信度评分 (Confidence)：**

| 因素 | 条件 | 加分 |
|------|------|------|
| 数据完整性 | >30天历史数据 | +10 |
| 无数据缺失 | 无 NaN 值 | +10 |
| 多源覆盖 | 每个额外数据源 | +5 |
| 高质量观察 | freshness>0.8, quality>0.8 | +5 |

### 5.4 报告内容解读

每日报告包含以下部分：

1. **Executive Summary** - 3-6 个关键要点
2. **Top Signals by Attention Score** - 综合评分最高的信号
3. **Top Equity Signals** - 排名前 5 的股票信号
4. **Top Crypto Signals** - 排名前 5 的加密货币信号
5. **Information Arbitrage** - 国会交易、对冲基金动向、预测市场信号
6. **News Highlights** - 重要新闻摘要
7. **Watchlist Heatmap** - 所有监控资产的热力图
8. **Caveats & Data Quality** - 数据质量说明
9. **What to Verify Tomorrow** - 次日跟踪事项

---

## 6. 定时任务

### 6.1 macOS 配置 (launchd)

**步骤 1：创建 plist 文件**

```bash
mkdir -p ~/Library/LaunchAgents
```

创建文件 `~/Library/LaunchAgents/com.tradz.nightly.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tradz.nightly</string>

    <key>ProgramArguments</key>
    <array>
        <string>/path/to/tradz/scripts/nightly.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/path/to/tradz/logs/launchd.log</string>

    <key>StandardErrorPath</key>
    <string>/path/to/tradz/logs/launchd-error.log</string>

    <key>WorkingDirectory</key>
    <string>/path/to/tradz</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
```

> **注意**：请将 `/path/to/tradz` 替换为实际项目路径

**步骤 2：创建日志目录并加载**

```bash
# 创建日志目录
mkdir -p /path/to/tradz/logs

# 加载定时任务
launchctl load ~/Library/LaunchAgents/com.tradz.nightly.plist

# 验证是否加载成功
launchctl list | grep tradz
```

**步骤 3：常用管理命令**

```bash
# 卸载定时任务
launchctl unload ~/Library/LaunchAgents/com.tradz.nightly.plist

# 手动触发运行
launchctl start com.tradz.nightly

# 查看日志
tail -f /path/to/tradz/logs/launchd.log
```

### 6.2 Linux 配置 (cron)

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天早上 6:30 运行）
30 6 * * * /path/to/tradz/scripts/nightly.sh >> /path/to/tradz/logs/cron.log 2>&1
```

**常用 cron 表达式：**

| 表达式 | 含义 |
|--------|------|
| `30 6 * * *` | 每天 6:30 |
| `0 7 * * 1-5` | 工作日 7:00 |
| `0 18 * * *` | 每天 18:00 |
| `0 */6 * * *` | 每 6 小时 |

---

## 7. 故障排除

### 7.1 常见问题

#### 问题：ModuleNotFoundError: No module named 'yfinance'

```bash
# 解决方案
source .venv/bin/activate
pip install -r requirements.txt
```

#### 问题：SMTP authentication failed

**检查清单：**

1. 确认使用的是应用专用密码，而非账户密码
2. 检查 SMTP_HOST 和 SMTP_PORT 是否正确
3. 先用 DRY_RUN=1 测试其他组件

#### 问题：Failed to fetch data for ticker XYZ

**可能原因：**

1. 网络连接问题
2. ticker 代码无效
3. yfinance API 限流

**解决方案：**

1. 检查 ticker 代码是否正确
2. 从 config.yaml 移除问题 ticker
3. 稍后重试（限流会自动重置）

#### 问题：No exchange found (加密货币)

**解决方案：**

1. 在 config.yaml 中更换交易所（尝试 'coinbase' 或 'kraken'）
2. 检查交易所状态：https://status.binance.com

#### 问题：Claude CLI not found

```bash
# 安装 Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version

# 如果使用 nvm，确保 node 在 PATH 中
which node
which claude
```

#### 问题：Claude report generation failed

**可能原因：**

1. ANTHROPIC_API_KEY 未设置或无效
2. 网络问题
3. API 配额用尽

**解决方案：**

1. 检查 .env 中的 ANTHROPIC_API_KEY
2. 系统会自动降级到模板生成（如果启用了 fallback_to_template）

#### 问题：DuckDB 数据库问题

```bash
# 验证数据库架构
python3 scripts/verify_db.py

# 验证实体解析
python3 scripts/verify_entities.py

# 验证信号生成
python3 scripts/verify_signals.py

# 验证事实生成
python3 scripts/verify_facts.py
```

### 7.2 日志查看

```bash
# 查看最近运行日志
tail -100 logs/launchd.log

# 查看错误日志
tail -100 logs/launchd-error.log

# 实时监控日志
tail -f logs/launchd.log

# 查看后端日志（local_up.sh 启动时）
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log
```

### 7.3 手动测试各模块

```bash
# 激活环境
source .venv/bin/activate

# 测试 yfinance
python3 -c "import yfinance as yf; print(yf.Ticker('AAPL').info.get('shortName'))"

# 测试 ccxt
python3 -c "import ccxt; print(ccxt.binance().fetch_ticker('BTC/USDT')['last'])"

# 测试 DuckDB
python3 -c "import duckdb; print(duckdb.connect(':memory:').execute('SELECT 1').fetchone())"

# 测试 Claude CLI
claude -p "Say hello" --output-format text
```

---

## 8. 高级用法

### 8.1 自定义监控列表

编辑 `config.yaml` 添加新的股票或加密货币：

```yaml
equities:
  tickers:
    - AAPL
    - TSLA
    - AMD     # 新增
    - INTC    # 新增

crypto:
  pairs:
    - BTC/USDT
    - ETH/USDT
    - LINK/USDT  # 新增
```

### 8.2 调整信号灵敏度

**减少信号数量（更严格）：**

```yaml
thresholds:
  day_return_high: 7.0      # 从 5.0 提高到 7.0
  volume_high: 3.0          # 从 2.0 提高到 3.0
```

**增加信号数量（更敏感）：**

```yaml
thresholds:
  day_return_high: 3.0      # 从 5.0 降低到 3.0
  volume_high: 1.5          # 从 2.0 降低到 1.5
```

### 8.3 数据源说明

| 数据源 | 延迟 | 限制 | 适用场景 |
|--------|------|------|---------|
| **yfinance** | 15-20分钟 | 免费层有限流 | 日终分析 |
| **ccxt (Binance)** | 接近实时 | 依赖交易所 API | 日常趋势分析 |
| **国会议员交易** | ~45天 | 免费公开 API | 内部人交易跟踪 |
| **对冲基金 13F** | 季度，~45天 | SEC EDGAR 免费 | 机构持仓变化 |
| **Polymarket** | 实时 | 免费 API | 事件驱动信号 |
| **NewsAPI** | 实时 | 免费层 100次/天 | 新闻情绪 |
| **SEC 年报** | 实时 | SEC EDGAR 免费 | 基本面分析 |

> ⚠️ **重要提示**：本系统使用免费数据源，不应作为交易决策的唯一依据。请始终通过其他渠道验证信号。

### 8.4 添加自定义对冲基金

查找基金 CIK：
1. 访问 https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany
2. 搜索基金名称
3. 复制 10 位 CIK（包含前导零）

```yaml
hedgefunds:
  notable_funds:
    - "0001067983"  # Berkshire Hathaway
    - "0001234567"  # 你添加的新基金
```

### 8.5 安全最佳实践

1. **永远不要提交 `.env` 文件** - 包含密码信息
2. **使用应用专用密码** - 不要使用主账户密码
3. **定期轮换凭据** - 定期更换密码
4. **限制权限** - 使用专用于自动化的邮箱账户
5. **监控异常** - 检查邮箱账户是否有可疑活动
6. **API 密钥安全** - 不要在代码或日志中硬编码 API 密钥

---

## 9. Claude AI 报告生成

### 9.1 安装 Claude Code CLI

```bash
# 安装 Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version

# 在 .env 中配置 API 密钥
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### 9.2 工作原理

Claude AI 报告生成流程：

```
┌─────────────────────────────────────────────────────────────────┐
│  1. 数据准备                                                     │
│     Python 脚本聚合所有数据源 → data/YYYY-MM-DD.json            │
│     生成事实表 (FactTable) → 确定性数值                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 构建 Prompt                                                  │
│     - 加载 prompts/report_system.md (系统提示词)                 │
│     - 加载 prompts/report_user.md (用户提示词模板)               │
│     - 填充数据摘要和事实表                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 调用 Claude CLI                                              │
│     claude -p "..." --dangerously-skip-permissions              │
│            --output-format text                                  │
│     ↳ 完全自动化，无需人工确认                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Claude 使用 MCP Skills                                       │
│     - tavily-search: 搜索每个信号的最新新闻                      │
│     - filesystem: 读取历史报告进行趋势对比                       │
│     - sequential-thinking: 复杂的多步分析推理                   │
│     - fetch: 获取网页内容                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. 输出报告                                                     │
│     生成高质量 Markdown 报告 → reports/YYYY-MM-DD.md            │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 可用的 MCP Skills

| Skill | 用途 | 示例 |
|-------|------|------|
| **tavily-search** | 搜索每个信号的最新新闻 | 搜索 "NVDA stock news today" |
| **filesystem** | 读取历史报告进行趋势对比 | 读取上周报告对比信号变化 |
| **sequential-thinking** | 复杂的多步分析推理 | 分析多个信号之间的关联 |
| **fetch** | 获取网页内容 | 获取公司公告页面内容 |

### 9.4 Prompt 自定义

编辑 `prompts/` 目录下的文件自定义报告风格：

**`prompts/report_system.md`** - 系统提示词

定义分析师角色、报告结构、分析框架：

```markdown
You are an expert financial analyst...

## Report Structure
1. Executive Summary (3-6 bullet points)
2. Top Signals Analysis
3. Information Arbitrage Insights
...
```

**`prompts/report_user.md`** - 用户提示词模板

包含数据占位符，运行时自动填充：

```markdown
Generate a trading signals report for {date}.

## Data Summary
{data_summary}

## Full Data Path
{data_path}
...
```

### 9.5 Fallback 机制

当 Claude 不可用时，系统自动降级到模板生成：

```yaml
# config.yaml
claude:
  enabled: true
  fallback_to_template: true  # Claude 失败时使用模板
```

触发 Fallback 的情况：
- Claude CLI 未安装
- ANTHROPIC_API_KEY 未设置
- API 调用超时（默认 300 秒）
- API 返回错误

### 9.6 报告质量对比

| 方面 | 模板生成 | Claude 生成 |
|------|---------|-------------|
| Executive Summary | 固定格式，罗列数字 | 智能提炼，突出关键发现 |
| 信号解读 | "上涨 5%" | "受并购传闻影响，成交量创 3 个月新高" |
| 跨源关联 | 无 | "议员 X 买入 NFLX，同期 Polymarket 显示..." |
| 新闻验证 | 无 | 使用 Tavily 搜索最新新闻并引用 |
| 风险提示 | 固定文案 | 根据具体情况动态生成 |
| 历史对比 | 无 | 读取历史报告，分析趋势变化 |

### 9.7 自动化运行说明

`--dangerously-skip-permissions` 标志的作用：

- 跳过所有权限确认对话框
- 允许 Claude 自动使用所有已配置的 MCP Skills
- 适用于 cron/launchd 等无人值守的自动化场景

**安全注意事项**：
- 此标志赋予 Claude 完全的工具访问权限
- 仅在受信任的环境中使用
- 确保 Claude 只能访问必要的文件和目录

---

## 10. Web 仪表盘

### 10.1 系统要求

- **Node.js**: 18+（用于前端开发）
- **npm**: 9+

### 10.2 一键启动

```bash
# 启动后端 (8002) + 前端 (5173)
./scripts/local_up.sh

# 停止所有服务
./scripts/local_down.sh
```

### 10.3 手动启动后端 API

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动 FastAPI 服务（开发模式）
uvicorn api.main:app --reload --port 8002

# 或指定主机（允许局域网访问）
uvicorn api.main:app --reload --host 0.0.0.0 --port 8002
```

API 文档地址：
- **Swagger UI**: http://localhost:8002/api/docs
- **ReDoc**: http://localhost:8002/api/redoc

### 10.4 手动启动前端

```bash
# 进入前端目录
cd frontend

# 首次运行：安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端地址：http://localhost:5173

### 10.5 API 端点

| 端点 | 方法 | 说明 |
|-----|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/signals/` | GET | 获取所有信号 |
| `/api/signals/refresh` | POST | 刷新信号数据 |
| `/api/sources/` | GET | 获取数据源状态 |
| `/api/sources/{source}` | GET | 获取特定数据源 |
| `/api/reports/` | GET | 获取报告列表 |
| `/api/reports/{date}` | GET | 获取特定日期报告 |

### 10.6 仪表盘功能

**Dashboard 页面**：
- 信号概览卡片
- 顶级股票信号列表（含 4 维评分）
- 顶级加密货币信号列表
- 信号评分可视化

**Sources 页面**：
- 各数据源状态监控
- 数据获取时间显示
- 错误状态显示

**使用指南页面**：
- 交互式可折叠文档
- 系统概述和安装配置
- 信号解读和故障排除
- Claude AI 报告生成说明

### 10.7 生产部署

```bash
# 构建前端静态文件
cd frontend
npm run build

# 构建产物在 frontend/dist/ 目录

# 生产环境启动 API
uvicorn api.main:app --host 0.0.0.0 --port 8002 --workers 4
```

---

## 11. 数据库与实体解析

### 11.1 DuckDB 数据库

Tradz 使用 DuckDB 作为本地分析数据库，存储在 `data/tradz.duckdb`。

**数据库表结构：**

| 表名 | 说明 |
|------|------|
| `entities` | 实体表（Ticker/CIK/公司名称映射） |
| `observations` | 观察表（各数据源的原始数据点） |
| `events` | 事件表（聚合相关观察的故事） |
| `signals` | 信号表（每日 4 维评分输出） |
| `event_observations` | 事件-观察关联表 |
| `run_history` | 运行历史（用于可观测性） |

**验证数据库：**

```bash
python3 scripts/verify_db.py
```

### 11.2 实体解析

EntityResolver 负责将不同数据源的数据对齐到统一的实体 ID：

```bash
# 同步 SEC 股票代码映射
python3 scripts/verify_entities.py
```

**功能：**
- 从 SEC 同步 Ticker/CIK/公司名称
- 解析文本中的实体（如 $AAPL）
- 为每个实体分配唯一 UUID

### 11.3 数据模型

**Entity（实体）：**
```python
@dataclass
class Entity:
    id: UUID
    entity_type: EntityType  # ticker, cik, person, fund, market
    ticker: str
    cik: str
    name: str
    aliases: List[str]
```

**Observation（观察）：**
```python
@dataclass
class Observation:
    id: UUID
    source: SourceType  # equities, crypto, congress, etc.
    entity_id: UUID
    entity_ticker: str
    effective_at: datetime
    observed_at: datetime
    freshness_score: float  # 0-1
    quality_score: float    # 0-1
    summary: str
    payload: Dict
```

**Signal（信号）：**
```python
@dataclass
class Signal:
    id: UUID
    signal_date: datetime
    entity_id: UUID
    ticker: str
    asset_type: str  # equity, crypto
    
    # 4 维评分 (0-100)
    anomaly_score: float
    catalyst_score: float
    flow_score: float
    confidence_score: float
    
    # 综合评分
    @property
    def attention_score(self) -> float:
        return (anomaly * 0.30 + catalyst * 0.30 + 
                flow * 0.25 + confidence * 0.15)
```

### 11.4 事实表 (FactTable)

为 LLM 报告生成提供确定性事实：

```python
@dataclass
class FactTableEntry:
    fact_id: str
    category: str  # price, volume, news, filing, score, metric
    ticker: str
    value: Any
    unit: str  # %, $, x, 0-100
    source_url: str
    timestamp: datetime
```

**用途：**
- LLM 必须引用事实表中的数值
- 防止 LLM 编造不存在的数字
- 确保报告的准确性和可追溯性

---

## 快速参考卡

```bash
# ===== 日常命令 =====

# 手动运行（模拟模式）
./scripts/nightly.sh

# 手动运行（跳过邮件）
python3 -m src.tradz.run_nightly --skip-email

# 仅使用模板生成（快速）
python3 -m src.tradz.run_nightly --template-only --skip-email

# 查看今日报告
cat reports/$(date +%Y-%m-%d).md

# 查看今日聚合数据
cat data/$(date +%Y-%m-%d).json | python3 -m json.tool | less

# 查看定时任务状态 (macOS)
launchctl list | grep tradz

# 查看日志
tail -f logs/launchd.log

# ===== 配置命令 =====

# 编辑监控列表
vim config.yaml

# 编辑邮件配置
vim .env

# ===== Web 仪表盘 =====

# 一键启动
./scripts/local_up.sh

# 一键停止
./scripts/local_down.sh

# 手动启动 API 后端（终端 1）
uvicorn api.main:app --reload --port 8002

# 手动启动前端（终端 2）
cd frontend && npm run dev

# 构建前端生产版本
cd frontend && npm run build

# ===== 验证脚本 =====

# 验证数据库
python3 scripts/verify_db.py

# 验证实体解析
python3 scripts/verify_entities.py

# 验证信号生成
python3 scripts/verify_signals.py

# 验证事实生成
python3 scripts/verify_facts.py

# ===== 故障排查 =====

# 重新安装依赖
source .venv/bin/activate && pip install -r requirements.txt

# 测试数据获取
python3 -c "import yfinance as yf; print(yf.Ticker('AAPL').history(period='1d'))"

# 测试 Claude CLI
claude -p "Hello" --output-format text

# 重启定时任务 (macOS)
launchctl unload ~/Library/LaunchAgents/com.tradz.nightly.plist
launchctl load ~/Library/LaunchAgents/com.tradz.nightly.plist
```

---

## 附录

### A. 文件输出说明

| 文件 | 路径 | 说明 |
|------|------|------|
| 聚合数据 | `data/YYYY-MM-DD.json` | 所有数据源的原始聚合数据 |
| DuckDB 数据库 | `data/tradz.duckdb` | 实体、观察、事件、信号的持久化存储 |
| 信号 JSON | `reports/YYYY-MM-DD.json` | 信号评分和排名数据 |
| Markdown 报告 | `reports/YYYY-MM-DD.md` | 可读的报告文件 |
| 日志 | `logs/launchd.log` | 定时任务日志 |
| 后端日志 | `logs/backend.log` | API 后端日志 |
| 前端日志 | `logs/frontend.log` | 前端开发服务器日志 |

### B. 环境变量完整列表

| 变量 | 必需 | 说明 |
|------|------|------|
| `DRY_RUN` | 是 | 1=模拟模式，0=正式发送邮件 |
| `SMTP_HOST` | 是 | 邮件服务器地址 |
| `SMTP_PORT` | 是 | 邮件服务器端口 |
| `SMTP_USER` | 是 | 邮箱用户名 |
| `SMTP_PASS` | 是 | 邮箱密码/应用专用密码 |
| `SMTP_FROM` | 否 | 发件人地址（默认 SMTP_USER） |
| `SMTP_TO` | 否 | 收件人地址（默认 SMTP_USER） |
| `ANTHROPIC_API_KEY` | 否 | Claude API 密钥 |
| `NEWSAPI_KEY` | 否 | NewsAPI 密钥 |
| `SEC_USER_AGENT` | 否 | SEC EDGAR 请求标识 |

### C. 联系与支持

如有任何问题，请：

1. 查看本文档的故障排除章节
2. 运行验证脚本检查各组件
3. 检查 `logs/` 目录中的日志文件
4. 逐一测试各个模块定位问题

---

*最后更新：2026-01-19*
