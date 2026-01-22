# PRD: Tradz vNext — 事件驱动的每日自动简报与可执行交易建议

## 文档信息

| 字段 | 值 |
|------|-----|
| 版本 | v1.8 |
| 日期 | 2026-01-21 |
| 产品模块 | Today（Signal Inbox + Daily Brief）、Events（事件详情/追踪）、Reports（报告档案与对比）、Pipeline（事件生成与证据链） |
| 目标用户 | 小团队内部交易研究者 |
| 技术栈 | React + TanStack Query + Tailwind + FastAPI + DuckDB + Claude CLI / OpenRouter |

---

## Introduction / 概述

### 愿景："Borderline Unfair"

用户每天早上打开系统，看到的不是一堆 ticker 分数，而是：

1. **"今天值得注意的事情"** — 跨资产（Equity/Crypto/Polymarket）的事件列表
2. **多源证据链** — 国会交易 / 13F / Polymarket / 新闻 / SEC / X 情绪 / 市场数据
3. **可执行建议** — Trade Idea 或 Research Plan，包含：
   - 结论是什么
   - 证据来自哪里
   - 失效条件是什么
   - 明天该验证什么
4. **持续追踪** — 系统记得"这事还没完"，自动更新进展

**核心价值主张**：用户不再需要早上 6 点盯 15 个标签页 — 一份完整简报直接生成。

### 示例场景

系统发现某位议员在买 Netflix → 同时 Polymarket 上 Warner Bros 并购赔率跳变 → 3 周后并购案公布。用户通过系统提前获得信号，实现信息优势。

### 核心概念定义

| 概念 | 定义 |
|------|------|
| **Event ↔ Signal** | 1 Event = N Signals（聚合），少量 Signal 可跨 Event（如宏观主题影响多个事件）。Signal 是重要中间层，不能废弃。 |
| **Observation** | 原始数据点 + 必须经过实体映射处理 + 部分是 delta 变化（如价格变动） |
| **标题生成** | 模板生成 + LLM 润色 |
| **多主题事件** | Primary Event + Secondary/Topic Sub-events 层级结构 |

---

## Goals / 目标

### 产品目标（Objectives）

| ID | 目标 | 描述 |
|----|------|------|
| O1 | Signal Inbox 真正产出事件 | Today 页面每天产出可读、可操作的事件列表（跨资产） |
| O2 | Daily Brief 自动生成 | 包含 executive summary、top events、trade/research ideas、open loops |
| O3 | 事件可审计 | 任何结论都能回溯到 FactTable + Observations（链接/原始片段/时间） |
| O4 | 事件可追踪 | 支持事件状态机与"比较昨天"（新增/升级/降级/解决） |

### 成功指标（Key Results）

**P0 核心指标**

| ID | 指标 | 目标值 |
|----|------|--------|
| M1 | 每日 Active Events 数量 | >= 3 个，每个关联 >=2 observations 或 >=1 强催化剂 |
| M2 | Daily Brief 生成成功率 | >= 95%（Claude 失败必须 fallback 到模板） |
| M3 | 证据可审计一致性 | 100%（卡片证据计数 = 点击后证据列表） |

**P1 体验指标**

| ID | 指标 | 目标值 |
|----|------|--------|
| M4 | Compare Yesterday 差异显示 | 能显示新增/变化事件 + 变化原因 + 证据 |
| M5 | 获取"今日重点"所需点击数 | <= 3（理想：0-1） |

---

## AC 标准模板

所有 User Story 的 Acceptance Criteria 遵循以下模板：

```markdown
**Acceptance Criteria:**

**功能验证：**
- [ ] [具体功能点 1]
- [ ] [具体功能点 2]

**边界条件：**
- [ ] [边界情况 1]
- [ ] [边界情况 2]

**错误处理：**
- [ ] [错误场景 1 → 期望行为]
- [ ] [错误场景 2 → 期望行为]

**示例（输入/输出）：**
[具体的 mock 数据]

**测试要求：**
- [ ] Unit tests 覆盖所有正常路径
- [ ] Unit tests 覆盖所有边界条件
- [ ] Unit tests 覆盖所有错误场景
- [ ] 测试覆盖率 >= [X]%（针对本 story 新增代码）
- [ ] Typecheck/lint passes
- [ ] **[UI story]** Verify in browser using dev-browser skill
```

---

## User Stories / 用户故事

### Epic 1: 事件生成引擎（P0）

#### US-001a: Observation 入库与实体映射

**Description:** As a 数据管道, I need 将各数据源的原始数据转化为标准化 Observation 并完成实体映射 so that 后续聚合逻辑能正确关联数据。

**Acceptance Criteria:**

**功能验证：**
- [ ] 每个数据源（Congress/13F/News/SEC/Polymarket/Market）产出的数据都转化为 Observation 记录
- [ ] Observation 必须包含字段：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `id` | UUID | 主键 |
  | `source_type` | enum | congress/13f/news/sec/polymarket/market |
  | `entity_id` | UUID, nullable | FK to entities，映射失败时为 NULL |
  | `entity_mapping_confidence` | float | 0-1，映射置信度 |
  | `observed_at` | timestamp | 数据发生时间 |
  | `ingested_at` | timestamp | 入库时间 |
  | `title` | string(200) | 简短描述 |
  | `summary` | string(2000) | 详细摘要 |
  | `source_url` | string(500) | 原始链接 |
  | `raw_payload` | JSON | 原始数据，上限 100KB |
  | `fact_entries` | JSON array | 提取的结构化事实 |
  | `payload_truncated` | boolean | 是否被截断 |

- [ ] 实体映射规则按数据源执行：
  | 数据源 | 映射方式 | 默认 confidence |
  |--------|----------|-----------------|
  | Congress | ticker 直接匹配 | 1.0 |
  | 13F | CIK → ticker | 1.0 |
  | News | NER 提取 + fuzzy match | 0.7-0.95 |
  | SEC Filing | CIK 直接匹配 | 1.0 |
  | Polymarket | 关键词 → watchlist | 0.5-0.9 |
  | Market | ticker 直接匹配 | 1.0 |

**边界条件：**
- [ ] entity_id 映射失败 → `entity_id = NULL`, `confidence = 0`，仍入库但标记 `unmapped`
- [ ] 同一原始数据涉及多个 entity → 创建 N 条 observation，共享同一 `raw_payload` 引用
- [ ] raw_payload > 100KB → 截断至 100KB，`payload_truncated = true`
- [ ] observed_at 早于 90 天 → 仍入库但标记 `historical = true`
- [ ] 同一 `source_type + source_url + observed_at` 重复 → 跳过，不报错

**错误处理：**
- [ ] 数据源 API 超时（>30s）→ 记录到 `run_history.errors[]`，继续处理其他源
- [ ] 数据源返回空数据 → 记录 warning，不视为错误
- [ ] 实体映射服务超时（>5s）→ 使用 `entity_id = NULL`，记录 warning
- [ ] JSON 解析失败 → 跳过该条记录，记录 error 含原始数据片段（前 500 字符）
- [ ] 数据库写入失败 → 重试 3 次（间隔 1s/2s/4s），仍失败则整体任务失败

**示例（输入/输出）：**

```python
# 输入：Congress 交易原始数据
input_congress = {
    "politician": "Nancy Pelosi",
    "ticker": "NVDA",
    "transaction_type": "purchase",
    "amount": "$1,000,001 - $5,000,000",
    "transaction_date": "2026-01-15",
    "source_url": "https://capitoltrades.com/trades/12345"
}

# 输出：Observation 记录
expected_observation = {
    "id": "obs-uuid-001",
    "source_type": "congress",
    "entity_id": "entity-nvda-001",  # 假设 NVDA 已在 entities 表
    "entity_mapping_confidence": 1.0,
    "observed_at": "2026-01-15T00:00:00Z",
    "ingested_at": "2026-01-21T08:30:00Z",  # 运行时间
    "title": "Pelosi purchased NVDA ($1M-$5M)",
    "summary": "Rep. Nancy Pelosi (D-CA) disclosed purchase of NVIDIA Corp (NVDA) shares valued between $1,000,001 and $5,000,000 on 2026-01-15.",
    "source_url": "https://capitoltrades.com/trades/12345",
    "raw_payload": input_congress,
    "fact_entries": [
        {"fact_type": "trade_amount_min", "value": 1000001, "unit": "USD"},
        {"fact_type": "trade_amount_max", "value": 5000000, "unit": "USD"},
        {"fact_type": "politician_name", "value": "Nancy Pelosi"},
        {"fact_type": "politician_party", "value": "D"},
        {"fact_type": "transaction_type", "value": "purchase"}
    ],
    "payload_truncated": False
}

# 边界案例：映射失败
input_news_unmapped = {
    "headline": "Tech stocks rally on AI optimism",
    "content": "The technology sector saw gains...",  # 无明确 ticker
    "published_at": "2026-01-20T14:00:00Z"
}

expected_unmapped = {
    "id": "obs-uuid-002",
    "source_type": "news",
    "entity_id": None,  # 映射失败
    "entity_mapping_confidence": 0,
    "title": "Tech stocks rally on AI optimism",
    # ... 其他字段
}
```

**测试要求：**

| 测试类型 | 覆盖场景 | 文件位置 |
|----------|----------|----------|
| Unit | 每个数据源的正常映射（6 个源 × 正常 case） | `tests/unit/test_observation_mapper.py` |
| Unit | 每个数据源的映射失败 case | 同上 |
| Unit | 边界条件：payload 截断、重复检测、历史数据 | 同上 |
| Unit | 错误处理：超时、JSON 解析失败、DB 写入失败 | 同上 |
| Integration | 完整 pipeline: 原始数据 → observation 入库 | `tests/integration/test_observation_pipeline.py` |

- [ ] Unit tests 覆盖所有 6 个数据源的正常映射
- [ ] Unit tests 覆盖所有边界条件（至少 5 个 case）
- [ ] Unit tests 覆盖所有错误场景（至少 4 个 case）
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes (`mypy src/tradz/observation_mapper.py`)
- [ ] Lint passes (`ruff check src/tradz/`)

---

#### US-001b: Event 聚合逻辑（基于 entity + 时间窗 + 主题）

**Description:** As a 数据管道, I need 将同一实体的相关 observations 聚合成 Event so that 用户看到的是"一件事"而非零散数据点。

**Acceptance Criteria:**

**功能验证：**
- [ ] 聚合规则：同一 `entity_id` + 时间窗口内（默认 72h，可配置）的 observations 归入同一 Event
- [ ] Event schema 包含必填字段：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `id` | UUID | 主键 |
  | `primary_entity_id` | UUID | 主关联实体 |
  | `secondary_entity_ids` | UUID[] | 次要关联实体（如并购双方） |
  | `event_type` | enum | 见 US-001c |
  | `status` | enum | new/ongoing/stale/resolved/dismissed |
  | `parent_event_id` | UUID, nullable | 父事件（用于 Primary/Secondary 层级） |
  | `title` | string(200) | 事件标题 |
  | `attention_score` | float | 0-100 综合分数 |
  | `anomaly_score` | float | 0-100 |
  | `catalyst_score` | float | 0-100 |
  | `flow_score` | float | 0-100 |
  | `confidence_score` | float | 0-100 |
  | `observation_count` | int | 关联 observation 数量 |
  | `signal_ids` | UUID[] | 关联的 signal IDs |
  | `start_at` | timestamp | 首个 observation 时间 |
  | `last_update_at` | timestamp | 最新 observation 时间 |
  | `created_at` | timestamp | 事件创建时间 |

- [ ] Event ↔ Observation 关联存储在 `event_observations` 表
- [ ] Event ↔ Signal 关联：1 Event 聚合 N Signals（通过 `signal_ids` 字段）
- [ ] 少量 Signal 可跨 Event：当 Signal 涉及宏观主题时，可关联多个 Event

**聚合算法：**
```python
def aggregate_observations_to_events(observations: List[Observation]) -> List[Event]:
    """
    1. 按 entity_id 分组
    2. 每组内按 observed_at 排序
    3. 滑动窗口：如果相邻 observation 间隔 > 72h，拆分为新 Event
    4. 对每个 Event：
       - 生成标题（模板）
       - 计算分数（从关联 Signals 聚合）
       - 确定类型（见 US-001c）
    """
```

- [ ] 增量聚合：pipeline 运行时，新 observation 优先归入现有 Active Event，而非创建新 Event
- [ ] 归并条件：现有 Event 的 `last_update_at` 在 72h 窗口内 且 `status` 为 new/ongoing

**Primary/Secondary 事件层级：**
- [ ] 当同一 entity 同时有多个不同主题（通过 `event_type` 判断）时：
  - 创建 1 个 Primary Event（`parent_event_id = NULL`）
  - 创建 N 个 Secondary Events（`parent_event_id = primary.id`）
- [ ] Primary Event 的分数 = max(所有 Secondary Events 的分数)
- [ ] UI 默认展示 Primary Event，可展开查看 Secondary

**边界条件：**
- [ ] 单个 Event 关联 observation 数量上限 = 200，超出时按 `observed_at` 保留最新 200 条
- [ ] 单个 entity 同时存在的 Active Events 上限 = 5（按 attention_score 保留 Top 5）
- [ ] observation 的 `entity_id = NULL` → 不参与聚合，存入 `orphan_observations` 视图供人工 review
- [ ] 时间窗口跨越周末/节假日 → 窗口自动延长（如 72h 变为 72h + 休市时间）

**错误处理：**
- [ ] 聚合过程中 DB 写入失败 → 回滚当前批次，记录 error，不影响已有 Events
- [ ] Signal 关联失败（Signal 不存在）→ 记录 warning，Event 仍创建但 `signal_ids` 为空
- [ ] 分数计算异常（除零等）→ 使用默认分数 50，标记 `score_fallback = true`

**示例（输入/输出）：**

```python
# 输入：3 条 NVDA 相关 observations（72h 内）
observations = [
    {"id": "obs-1", "entity_id": "nvda", "source_type": "congress",
     "observed_at": "2026-01-15T10:00:00Z", "title": "Pelosi bought NVDA"},
    {"id": "obs-2", "entity_id": "nvda", "source_type": "news",
     "observed_at": "2026-01-16T08:00:00Z", "title": "NVDA announces new chip"},
    {"id": "obs-3", "entity_id": "nvda", "source_type": "market",
     "observed_at": "2026-01-16T16:00:00Z", "title": "NVDA +8% on volume spike"},
]

# 输出：1 个 Event
expected_event = {
    "id": "evt-001",
    "primary_entity_id": "nvda",
    "event_type": "mixed",  # 多源
    "status": "new",
    "parent_event_id": None,
    "title": "NVDA: Congress买入 + 新品发布 + 价格异动",  # 模板生成
    "observation_count": 3,
    "start_at": "2026-01-15T10:00:00Z",
    "last_update_at": "2026-01-16T16:00:00Z",
    # 分数从 Signals 聚合
}

# 边界案例：同一 entity 的 observations 跨越 72h 窗口
observations = [
    {"id": "obs-1", "entity_id": "aapl", "observed_at": "2026-01-10T10:00:00Z"},
    {"id": "obs-2", "entity_id": "aapl", "observed_at": "2026-01-15T10:00:00Z"},  # 间隔 5 天
]

# 输出：2 个独立 Events
expected_events = [
    {"id": "evt-001", "observation_ids": ["obs-1"], "start_at": "2026-01-10"},
    {"id": "evt-002", "observation_ids": ["obs-2"], "start_at": "2026-01-15"},
]
```

**测试要求：**

| 测试类型 | 覆盖场景 | 文件位置 |
|----------|----------|----------|
| Unit | 基本聚合：同 entity + 72h 内 → 1 Event | `tests/unit/test_event_aggregator.py` |
| Unit | 窗口拆分：间隔 > 72h → 多 Events | 同上 |
| Unit | 增量归并：新 obs 归入现有 Event | 同上 |
| Unit | Primary/Secondary 层级创建 | 同上 |
| Unit | 边界：200 obs 上限、5 Active Events 上限 | 同上 |
| Unit | 错误处理：DB 失败回滚、分数计算异常 | 同上 |
| Integration | 完整 pipeline: observations → events | `tests/integration/test_event_aggregation.py` |

- [ ] Unit tests 覆盖聚合算法所有分支
- [ ] Unit tests 覆盖 Primary/Secondary 层级逻辑
- [ ] Unit tests 覆盖所有边界条件
- [ ] Unit tests 覆盖所有错误场景
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes

---

#### US-001c: Event 类型自动分类

**Description:** As a 数据管道, I need 自动为 Event 分配类型 so that 用户能快速理解事件性质。

**Acceptance Criteria:**

**功能验证：**
- [ ] Event 类型枚举定义：
  | 类型 | 说明 | 判定条件 |
  |------|------|----------|
  | `market_anomaly` | 纯市场异常 | 仅有 market 源，且 anomaly_score >= 70 |
  | `catalyst_news` | 新闻驱动 | 有 news 源，catalyst_score >= 60 |
  | `catalyst_filing` | SEC 文件驱动 | 有 sec 源（8-K/10-K/10-Q） |
  | `flow_congress` | 国会披露驱动 | 有 congress 源 |
  | `flow_13f` | 机构持仓驱动 | 有 13f 源 |
  | `prediction_shift` | Polymarket 概率变动 | 有 polymarket 源，概率变化 >= 10% |
  | `mixed` | 多源混合 | 涉及 >= 2 种不同类型的源 |

- [ ] 类型判定优先级（当满足多个条件时）：
  1. `mixed`（多源时强制为 mixed）
  2. `catalyst_filing`（SEC 文件优先级最高）
  3. `flow_congress`
  4. `flow_13f`
  5. `catalyst_news`
  6. `prediction_shift`
  7. `market_anomaly`（默认兜底）

- [ ] 类型存储在 `events.event_type` 字段
- [ ] 类型变更记录：当新 observation 导致类型变化时，记录到 `event_type_history` 表

**边界条件：**
- [ ] 所有 observation 的 entity_mapping_confidence < 0.5 → `event_type = 'uncertain'`，需人工确认
- [ ] 仅有 1 个 observation 且来自 news → 需 confidence >= 0.7 才分类为 `catalyst_news`，否则为 `uncertain`

**错误处理：**
- [ ] 类型判定逻辑异常 → 默认为 `market_anomaly`，标记 `type_fallback = true`

**示例：**

```python
# Case 1: 单一来源 - Congress
observations = [{"source_type": "congress", ...}]
expected_type = "flow_congress"

# Case 2: 多源混合
observations = [
    {"source_type": "congress", ...},
    {"source_type": "news", ...},
]
expected_type = "mixed"

# Case 3: SEC 文件优先
observations = [
    {"source_type": "sec", "raw_payload": {"form_type": "8-K"}},
    {"source_type": "news", ...},
]
expected_type = "mixed"  # 多源，但 SEC 在描述中优先展示
```

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | 每种单一类型的判定（7 种） |
| Unit | 多源 mixed 类型判定 |
| Unit | 优先级冲突时的判定 |
| Unit | 边界：低置信度 → uncertain |
| Unit | 类型变更历史记录 |

- [ ] Unit tests 覆盖所有 7 种类型的判定逻辑
- [ ] Unit tests 覆盖 mixed 类型的各种组合
- [ ] 本 story 新增代码测试覆盖率 >= 95%
- [ ] Typecheck passes
- [ ] Lint passes

---

#### US-001d: Event 标题生成（模板 + LLM 润色）

**Description:** As a 研究者, I want 每个 Event 有清晰的标题 so that 我能快速理解事件内容。

**Acceptance Criteria:**

**功能验证：**
- [ ] 标题生成采用两阶段策略：
  1. **模板生成**（必须成功）：基于 entity + event_type + top observation
  2. **LLM 润色**（可选，失败时用模板结果）：将模板标题润色为更自然的表达

- [ ] 模板规则：
  | event_type | 模板 | 示例 |
  |------------|------|------|
  | `market_anomaly` | `{ticker}: {direction}{change}% 异动 (成交量 {volume_ratio}x)` | `NVDA: +8.5% 异动 (成交量 3.2x)` |
  | `catalyst_news` | `{ticker}: {headline_summary}` | `TSLA: 马斯克宣布新工厂计划` |
  | `catalyst_filing` | `{ticker}: {form_type} 披露 - {filing_summary}` | `AAPL: 8-K 披露 - CEO 变更` |
  | `flow_congress` | `{ticker}: {politician} {action} (${amount})` | `NVDA: Pelosi 买入 ($1M-$5M)` |
  | `flow_13f` | `{ticker}: {fund_name} {action} {change}%` | `META: Bridgewater 增持 +45%` |
  | `prediction_shift` | `{market_question}: 概率 {old}% → {new}%` | `Fed 2026 降息: 概率 30% → 55%` |
  | `mixed` | `{ticker}: {source_count} 源信号 ({top_sources})` | `NVDA: 3 源信号 (Congress+News+Market)` |

**LLM 抽象层设计：**
- [ ] 创建 `LLMProvider` 抽象接口：
  ```python
  from abc import ABC, abstractmethod
  from typing import Optional

  class LLMProvider(ABC):
      @abstractmethod
      def generate(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
          """返回生成的文本，失败时返回 None"""
          pass

  class ClaudeCLIProvider(LLMProvider):
      """通过 Claude CLI 调用（当前方案）"""
      pass

  class OpenRouterProvider(LLMProvider):
      """通过 OpenRouter API 调用（支持多模型）"""
      def __init__(self, api_key: str, model: str = "anthropic/claude-3-haiku"):
          pass

  class MockProvider(LLMProvider):
      """用于测试的 Mock Provider"""
      def __init__(self, responses: dict[str, str]):
          self.responses = responses  # prompt_hash -> response

      def generate(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
          return self.responses.get(hash(prompt), f"Mock: {prompt[:50]}...")
  ```

- [ ] 配置文件 `config.yaml` 支持切换 provider：
  ```yaml
  llm:
    provider: "openrouter"  # claude_cli | openrouter | mock
    openrouter:
      api_key: "${OPENROUTER_API_KEY}"  # 从环境变量读取
      model: "anthropic/claude-3-haiku"  # 便宜且快
      timeout: 10
      max_retries: 2
    claude_cli:
      timeout: 30
    mock:
      enabled_in_test: true
  ```

- [ ] 标题润色 prompt：
  ```
  将以下交易事件标题润色为更自然、信息密度高的中文表达（不超过 50 字）：
  原标题：{template_title}
  关键事实：{fact_entries}
  要求：保留所有关键数字，不添加原文没有的信息
  ```

- [ ] 标题长度限制：200 字符，超出时截断并加 `...`
- [ ] 标题存储：`events.title`（最终）、`events.title_template`（模板原文）、`events.title_source`（'template' | 'llm'）

**边界条件：**
- [ ] 模板变量缺失 → 使用 fallback 值（如 `{ticker}` 缺失用 `Unknown`）
- [ ] LLM API 超时（>10s）→ 使用模板结果，`title_source = 'template'`
- [ ] LLM 返回空或超长 → 使用模板结果
- [ ] LLM 返回内容包含模板中没有的数字/事实 → 使用模板结果（防止幻觉）

**错误处理：**
- [ ] 模板渲染失败 → 使用通用模板 `{ticker}: 新事件 ({event_type})`
- [ ] LLM API 失败 → 静默降级到模板，记录 warning，不抛错
- [ ] OpenRouter 额度不足 → 降级到模板，发送告警通知

**测试策略：**

| 测试类型 | Provider | API Key 需求 | 说明 |
|----------|----------|--------------|------|
| **Unit Test** | `MockProvider` | 不需要 | 使用预定义的 mock responses |
| **Integration Test** | `MockProvider` | 不需要 | 测试完整流程，LLM 部分 mock |
| **E2E Test (CI)** | `OpenRouterProvider` | 需要（CI secret） | 可选，用 haiku 模型降低成本 |
| **E2E Test (本地)** | `OpenRouterProvider` 或 `ClaudeCLIProvider` | 需要 | 开发者自行配置 |

**Unit Test 实现示例：**
```python
# tests/unit/test_title_generator.py
import pytest
from tradz.title_generator import TitleGenerator
from tradz.llm_provider import MockProvider

class TestTitleGenerator:
    @pytest.fixture
    def mock_provider(self):
        return MockProvider(responses={
            # 预定义的 prompt -> response 映射
        })

    @pytest.fixture
    def generator(self, mock_provider):
        return TitleGenerator(llm_provider=mock_provider)

    def test_template_generation_congress(self, generator):
        """测试 Congress 类型的模板生成（不涉及 LLM）"""
        event = create_test_event(event_type="flow_congress", ...)

        # 只测试模板生成
        title = generator.generate_template_title(event)

        assert title == "NVDA: Pelosi 买入 ($1M-$5M)"

    def test_llm_polish_success(self, generator, mock_provider):
        """测试 LLM 润色成功场景"""
        mock_provider.responses["hash_of_prompt"] = "佩洛西大手笔买入英伟达"

        title, source = generator.generate_title(event)

        assert source == "llm"
        assert "佩洛西" in title

    def test_llm_timeout_fallback(self, generator, mock_provider):
        """测试 LLM 超时时降级到模板"""
        mock_provider.responses = {}  # 无匹配，模拟失败
        mock_provider.simulate_timeout = True

        title, source = generator.generate_title(event)

        assert source == "template"
        assert title == "NVDA: Pelosi 买入 ($1M-$5M)"

    def test_llm_hallucination_rejection(self, generator, mock_provider):
        """测试 LLM 返回幻觉内容时拒绝使用"""
        # LLM 返回了原文没有的数字
        mock_provider.responses["hash"] = "佩洛西买入英伟达 500 万股"  # 原文没有股数

        title, source = generator.generate_title(event)

        assert source == "template"  # 应该降级
```

**测试要求：**

| 测试类型 | 覆盖场景 | API Key |
|----------|----------|---------|
| Unit | 7 种 event_type 的模板生成 | 不需要 |
| Unit | 模板变量缺失的 fallback | 不需要 |
| Unit | 标题长度截断 | 不需要 |
| Unit | LLM 超时/失败降级（MockProvider） | 不需要 |
| Unit | LLM 幻觉检测与拒绝（MockProvider） | 不需要 |
| Integration | 模板 + LLM 完整流程（MockProvider） | 不需要 |
| E2E (可选) | 真实 LLM 调用 | 需要 OPENROUTER_API_KEY |

- [ ] Unit tests 100% 使用 MockProvider，无需 API key
- [ ] Unit tests 覆盖所有 7 种模板
- [ ] Unit tests 覆盖所有降级场景
- [ ] Unit tests 覆盖幻觉检测逻辑
- [ ] Integration test 验证完整流程（使用 MockProvider）
- [ ] E2E test（可选）验证真实 LLM 调用，需环境变量
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes

**成本控制（使用 OpenRouter）：**
- [ ] 使用 `claude-3-haiku`：约 $0.00025/1K input tokens, $0.00125/1K output tokens
- [ ] 每次标题润色预估：~200 input tokens + ~50 output tokens ≈ $0.0001
- [ ] 每日 100 个事件 ≈ $0.01/天
- [ ] 设置 OpenRouter 月度预算上限（如 $5/月）

---

### Epic 2: Today / Signal Inbox（P0）

#### US-004a: Events API - 事件列表接口

**Description:** As a 前端, I need 获取事件列表的 API so that Signal Inbox 能展示真实数据。

**Acceptance Criteria:**

**功能验证：**
- [ ] 端点：`GET /api/events`
- [ ] Query 参数：
  | 参数 | 类型 | 默认值 | 说明 |
  |------|------|--------|------|
  | `status` | string | `active` | `active` / `resolved` / `dismissed` / `all` |
  | `sort_by` | string | `attention` | `attention` / `anomaly` / `catalyst` / `flow` / `freshness` |
  | `sort_order` | string | `desc` | `asc` / `desc` |
  | `limit` | int | 20 | 1-100 |
  | `offset` | int | 0 | 分页偏移 |
  | `entity_type` | string | `all` | `ticker` / `crypto` / `polymarket` / `all` |

- [ ] Response schema：
  ```typescript
  interface EventsResponse {
    events: Event[];
    total: number;
    has_more: boolean;
    generated_at: string;  // ISO timestamp
  }

  interface Event {
    id: string;
    primary_entity_id: string;
    primary_entity: {
      id: string;
      symbol: string;       // e.g., "NVDA", "BTC/USDT"
      name: string;         // e.g., "NVIDIA Corp"
      entity_type: "ticker" | "crypto" | "polymarket";
    };
    secondary_entities: Entity[];  // 可能为空
    event_type: EventType;
    status: "new" | "ongoing" | "stale" | "resolved" | "dismissed";
    title: string;
    title_template: string;

    // 四维分数
    attention_score: number;   // 0-100
    anomaly_score: number;
    catalyst_score: number;
    flow_score: number;
    confidence_score: number;

    // 证据统计
    observation_counts: {
      congress: number;
      "13f": number;
      news: number;
      sec: number;
      polymarket: number;
      market: number;
      total: number;
    };

    // 时间
    start_at: string;
    last_update_at: string;

    // 用户状态
    pinned: boolean;
    snoozed_until: string | null;

    // 行动标签
    action_label: "act" | "investigate" | "monitor";

    // 最新摘要
    latest_observation_summary: string;

    // 层级
    parent_event_id: string | null;
    child_event_count: number;
  }
  ```

- [ ] `status=active` 返回：`new` + `ongoing`（排除 snoozed 未到期的）
- [ ] 排序 `attention` = `0.3*anomaly + 0.3*catalyst + 0.25*flow + 0.15*confidence`
- [ ] Pinned 事件始终排在最前（在当前排序基础上）

**边界条件：**
- [ ] 无事件时返回空数组 `{ events: [], total: 0, has_more: false }`
- [ ] `limit > 100` → 强制设为 100
- [ ] `offset` 超出范围 → 返回空数组
- [ ] 非法 `status` 值 → 400 错误，明确提示允许的值

**错误处理：**
- [ ] 数据库查询超时（>5s）→ 500 错误，`{ error: "Database timeout", code: "DB_TIMEOUT" }`
- [ ] 数据库连接失败 → 500 错误，`{ error: "Database unavailable", code: "DB_UNAVAILABLE" }`

**示例：**

```bash
# 请求
GET /api/events?status=active&sort_by=attention&limit=10

# 响应 200
{
  "events": [
    {
      "id": "evt-001",
      "primary_entity": { "symbol": "NVDA", "name": "NVIDIA Corp", "entity_type": "ticker" },
      "event_type": "mixed",
      "status": "new",
      "title": "佩洛西买入 NVDA + 新品发布 + 价格异动",
      "attention_score": 85,
      "anomaly_score": 78,
      "catalyst_score": 82,
      "flow_score": 90,
      "confidence_score": 88,
      "observation_counts": { "congress": 1, "news": 2, "market": 1, "total": 4 },
      "action_label": "act",
      "latest_observation_summary": "NVDA +8% on volume spike",
      "pinned": false,
      "snoozed_until": null,
      "start_at": "2026-01-15T10:00:00Z",
      "last_update_at": "2026-01-16T16:00:00Z"
    }
  ],
  "total": 15,
  "has_more": true,
  "generated_at": "2026-01-21T08:30:00Z"
}

# 错误响应 400
GET /api/events?status=invalid

{
  "error": "Invalid status value",
  "code": "INVALID_PARAM",
  "details": { "param": "status", "allowed": ["active", "resolved", "dismissed", "all"] }
}
```

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | 查询参数解析和验证 |
| Unit | 排序逻辑（各字段 + pinned 置顶） |
| Unit | 分页逻辑 |
| Unit | status 过滤（含 snoozed 排除） |
| Integration | 完整 API 调用（mock DB） |
| Integration | 数据库超时处理 |

- [ ] Unit tests 覆盖所有查询参数组合
- [ ] Unit tests 覆盖排序和分页边界
- [ ] Integration tests 覆盖完整 API 流程
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] API 文档更新（OpenAPI/Swagger）

---

#### US-004b: Signal Inbox - 事件列表 UI

**Description:** As a 研究者, I want 在 Today 页面看到事件列表 so that 我能快速浏览今天该关注的事情。

**Acceptance Criteria:**

**功能验证：**
- [ ] 组件位置：Today 页面中部，System Status 下方
- [ ] 组件结构：
  ```
  ┌─────────────────────────────────────────────────┐
  │ Signal Inbox                          [刷新按钮] │
  ├─────────────────────────────────────────────────┤
  │ [Active ▼] [Resolved] [All]    Sort: [Attention ▼] │
  ├─────────────────────────────────────────────────┤
  │ ┌─────────────────────────────────────────────┐ │
  │ │ Event Card 1 (pinned)                    📌 │ │
  │ └─────────────────────────────────────────────┘ │
  │ ┌─────────────────────────────────────────────┐ │
  │ │ Event Card 2                                │ │
  │ └─────────────────────────────────────────────┘ │
  │ ...                                             │
  │ [Load More] 或 无限滚动                          │
  └─────────────────────────────────────────────────┘
  ```

- [ ] Tab 切换：Active（默认）/ Resolved / All
  - Active：显示 new + ongoing（排除 snoozed 未到期）
  - Resolved：显示 resolved + dismissed
  - All：显示全部
- [ ] 排序下拉：Attention（默认）/ Anomaly / Catalyst / Flow / Freshness
- [ ] 分页：初始加载 20 条，点击 "Load More" 或滚动到底部加载更多
- [ ] 刷新按钮：手动刷新列表
- [ ] 自动刷新：每 5 分钟自动刷新（使用 TanStack Query `refetchInterval`）

**状态处理：**
- [ ] Loading 状态：显示 Skeleton 占位符（3 个卡片骨架）
- [ ] Error 状态：显示错误提示 + 重试按钮
  ```
  ┌─────────────────────────────────────────┐
  │  ⚠️ 加载失败                             │
  │  无法获取事件列表，请检查网络连接          │
  │  [重试]                                  │
  └─────────────────────────────────────────┘
  ```
- [ ] Empty 状态（无事件）：
  ```
  ┌─────────────────────────────────────────┐
  │  📭 暂无事件                             │
  │  当前没有需要关注的事件，系统正常运行中    │
  └─────────────────────────────────────────┘
  ```
- [ ] Empty 状态（筛选后无结果）：
  ```
  ┌─────────────────────────────────────────┐
  │  🔍 无匹配结果                           │
  │  当前筛选条件下没有事件，试试其他筛选      │
  │  [清除筛选]                              │
  └─────────────────────────────────────────┘
  ```

**交互细节：**
- [ ] Tab 切换时 URL 同步：`?tab=active` / `?tab=resolved` / `?tab=all`
- [ ] 排序切换时 URL 同步：`?sort=attention`
- [ ] 页面刷新后恢复之前的 tab 和排序状态
- [ ] 点击 Event Card 跳转到详情页：`/events/{eventId}`
- [ ] Pinned 事件显示 📌 图标，置顶显示

**性能要求：**
- [ ] 初始渲染 < 500ms（20 条数据）
- [ ] 列表使用虚拟滚动（当事件 > 50 条时）或分页
- [ ] 图片/头像懒加载

**边界条件：**
- [ ] 事件数量 = 0 → 显示 Empty 状态
- [ ] 事件数量 > 100 → 分页加载，显示 "Load More"
- [ ] 网络断开 → 显示缓存数据 + "离线模式" 提示
- [ ] API 返回部分数据损坏 → 跳过损坏项，显示可用数据

**React 组件结构：**
```typescript
// components/events/SignalInbox.tsx
interface SignalInboxProps {
  className?: string;
}

// 内部状态
// - tab: 'active' | 'resolved' | 'all'
// - sortBy: 'attention' | 'anomaly' | 'catalyst' | 'flow' | 'freshness'
// - events: Event[]
// - isLoading: boolean
// - error: Error | null

// 使用的 hooks
// - useEvents(tab, sortBy) - TanStack Query hook
// - useSearchParams() - URL 状态同步
```

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | Tab 切换逻辑 |
| Unit | 排序下拉逻辑 |
| Unit | URL 状态同步 |
| Unit | Loading/Error/Empty 状态渲染 |
| Component | Event Card 列表渲染（mock data） |
| Component | 分页/Load More 交互 |
| E2E | 完整用户流程（Playwright） |

- [ ] Unit tests 覆盖状态管理逻辑
- [ ] Component tests 覆盖所有 UI 状态（使用 React Testing Library）
- [ ] Component tests 使用 MSW mock API
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] Verify in browser：Tab 切换、排序、Load More、刷新
- [ ] 无障碍检查：键盘导航、屏幕阅读器支持

---

#### US-005: Event Card - 核心信息展示

**Description:** As a 研究者, I want 每个事件卡片展示关键信息 so that 我无需点开详情就能初步判断。

**Acceptance Criteria:**

**功能验证：**
- [ ] 卡片布局（固定高度 ~120px，响应式宽度）：
  ```
  ┌────────────────────────────────────────────────────────────────┐
  │ 📌 [Act]  NVDA · AAPL                              2 小时前 ↗  │
  │ ─────────────────────────────────────────────────────────────  │
  │ 佩洛西买入 NVDA + 新品发布 + 价格异动                           │
  │                                                                │
  │ A ████████░░ 78  C ████████░░ 82  F █████████░ 90  Cf ████████░ 88 │
  │                                                                │
  │ 📰2 📋1 🏛1 📊1                     最新: NVDA +8% on volume spike │
  │                                                     [···]      │
  └────────────────────────────────────────────────────────────────┘
  ```

- [ ] 必须显示的元素：
  | 元素 | 位置 | 说明 |
  |------|------|------|
  | Pin 图标 | 左上角 | 仅 pinned=true 时显示 📌 |
  | 行动标签 | 左上角 | `Act`(红) / `Investigate`(黄) / `Monitor`(灰) |
  | 资产 Chips | 顶部 | ticker/crypto/polymarket 标识，最多显示 3 个，超出显示 `+N` |
  | 时间 | 右上角 | 相对时间（2小时前）+ hover 显示绝对时间 |
  | 跳转图标 | 右上角 | ↗ 点击跳转详情页 |
  | 标题 | 中部 | 最多 2 行，超出省略 |
  | 四维分数条 | 中下部 | A/C/F/Cf 横向进度条 + 数值 |
  | 证据计数 | 底部左 | 📰(news) 📋(sec) 🏛(congress) 🏦(13f) 🎯(poly) 📊(market) |
  | 最新摘要 | 底部中 | 单行，超出省略 |
  | 操作菜单 | 底部右 | `···` 点击展开操作菜单 |

- [ ] 行动标签规则（来自 API，前端只做展示）：
  | 标签 | 颜色 | 条件 |
  |------|------|------|
  | Act | 红色 `#EF4444` | confidence >= 70 且门控通过 |
  | Investigate | 黄色 `#F59E0B` | confidence 50-70 或门控部分通过 |
  | Monitor | 灰色 `#6B7280` | confidence < 50 或仅市场异常 |

- [ ] 四维分数条样式：
  - 高度：8px，圆角
  - 颜色：分数 >= 70 绿色，50-70 黄色，< 50 灰色
  - 宽度：按百分比（score/100）

- [ ] 资产 Chips 样式：
  | entity_type | 背景色 | 示例 |
  |-------------|--------|------|
  | ticker | 蓝色 `#3B82F6` | `NVDA` |
  | crypto | 橙色 `#F97316` | `BTC` |
  | polymarket | 紫色 `#8B5CF6` | `Fed降息` |

- [ ] 证据计数：仅显示 count > 0 的来源，hover 显示具体名称

**交互细节：**
- [ ] 整卡片可点击，跳转到 `/events/{eventId}`
- [ ] 操作菜单（`···`）点击弹出下拉：Pin / Snooze / Dismiss / Resolve
- [ ] Hover 效果：轻微阴影提升 + 背景色变化
- [ ] Pinned 卡片：左边框加粗显示（4px 蓝色）

**边界条件：**
- [ ] 标题过长（> 100 字符）→ 截断 + `...`
- [ ] 无 secondary_entities → 只显示 primary
- [ ] 所有分数都是 0 → 分数条显示为空（灰色背景）
- [ ] observation_counts 全为 0 → 不显示证据计数区域
- [ ] latest_observation_summary 为空 → 显示 "暂无最新动态"

**响应式设计：**
- [ ] 桌面（>1024px）：完整布局
- [ ] 平板（768-1024px）：隐藏部分分数条标签
- [ ] 手机（<768px）：卡片堆叠，分数条改为 2x2 网格

**React 组件接口：**
```typescript
interface EventCardProps {
  event: Event;
  onAction: (eventId: string, action: EventAction) => void;
  onClick: (eventId: string) => void;
  className?: string;
}

type EventAction = 'pin' | 'unpin' | 'snooze' | 'dismiss' | 'resolve';
```

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | Props 渲染正确性 |
| Unit | 行动标签颜色逻辑 |
| Unit | 分数条宽度计算 |
| Unit | 文本截断逻辑 |
| Component | 完整卡片渲染（各种数据组合） |
| Component | 操作菜单交互 |
| Component | 响应式布局 |
| Snapshot | 视觉回归测试 |

- [ ] Component tests 覆盖所有 props 组合
- [ ] Component tests 覆盖操作菜单交互
- [ ] Snapshot tests 防止意外视觉变化
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] Verify in browser：各种数据状态、hover 效果、响应式
- [ ] 无障碍：卡片可聚焦、操作菜单键盘可访问

---

#### US-006: Event Card - 用户操作

**Description:** As a 研究者, I want 对事件执行快捷操作 so that 我能管理自己的关注列表。

**Acceptance Criteria:**

**功能验证：**
- [ ] 操作菜单内容（`···` 点击展开）：
  | 操作 | 图标 | 说明 | 可见条件 |
  |------|------|------|----------|
  | Pin / Unpin | 📌 | 置顶/取消置顶 | 始终可见 |
  | Snooze | 💤 | 暂时隐藏 | status != resolved/dismissed |
  | Dismiss | ❌ | 忽略此事件 | status != resolved/dismissed |
  | Resolve | ✅ | 标记为已处理 | status != resolved/dismissed |

- [ ] Snooze 二级菜单：
  ```
  ┌─────────────┐
  │ 💤 Snooze   │
  │ ├─ 1 小时   │
  │ ├─ 4 小时   │
  │ ├─ 24 小时  │
  │ ├─ 3 天     │
  │ └─ 自定义... │ → 弹出日期选择器
  └─────────────┘
  ```

- [ ] Dismiss 确认对话框：
  ```
  ┌─────────────────────────────────────┐
  │ 确认忽略此事件？                      │
  │                                     │
  │ 事件: 佩洛西买入 NVDA...             │
  │                                     │
  │ 原因（可选）: [________________]     │
  │                                     │
  │ ⚠️ 忽略后不会再次提醒，除非有重大更新   │
  │                                     │
  │           [取消]  [确认忽略]          │
  └─────────────────────────────────────┘
  ```

- [ ] Resolve 确认对话框：
  ```
  ┌─────────────────────────────────────┐
  │ 标记为已处理                         │
  │                                     │
  │ 事件: 佩洛西买入 NVDA...             │
  │                                     │
  │ 处理结果（可选）:                     │
  │ ○ 已交易                            │
  │ ○ 决定不交易                        │
  │ ○ 继续观察                          │
  │ ○ 其他: [________________]          │
  │                                     │
  │           [取消]  [确认]             │
  └─────────────────────────────────────┘
  ```

**API 调用：**
- [ ] 端点：`POST /api/events/{eventId}/actions`
- [ ] Request body：
  ```typescript
  interface EventActionRequest {
    action: 'pin' | 'unpin' | 'snooze' | 'dismiss' | 'resolve';
    snooze_until?: string;      // ISO timestamp, 仅 snooze 时
    dismiss_reason?: string;    // 仅 dismiss 时
    resolve_result?: string;    // 仅 resolve 时
  }
  ```
- [ ] Response：
  ```typescript
  interface EventActionResponse {
    success: boolean;
    event: Event;  // 更新后的事件
  }
  ```

**Optimistic Update：**
- [ ] 操作立即在 UI 生效（不等 API 返回）
- [ ] API 失败时回滚 UI + 显示错误 toast
- [ ] 使用 TanStack Query 的 `useMutation` + `onMutate` + `onError`

**交互细节：**
- [ ] Pin/Unpin：无确认，立即执行
- [ ] Snooze：选择时间后立即执行，卡片淡出动画
- [ ] Dismiss/Resolve：需确认对话框
- [ ] 操作成功后显示 toast：`"已置顶"` / `"已暂停提醒至 XX:XX"` / `"已忽略"` / `"已标记为已处理"`
- [ ] 操作菜单点击外部自动关闭

**边界条件：**
- [ ] 快速连续点击同一操作 → 防抖，只执行一次
- [ ] 网络断开时操作 → 显示 "离线模式，操作将在恢复连接后同步"
- [ ] Snooze 自定义时间选择过去的时间 → 禁止提交，提示 "请选择未来时间"
- [ ] 对已 dismissed 事件再次 dismiss → API 返回 400，UI 显示 "该事件已被忽略"

**错误处理：**
- [ ] API 超时（>5s）→ 回滚 UI + toast "操作超时，请重试"
- [ ] API 返回 404（事件不存在）→ 从列表移除该卡片 + toast "事件已不存在"
- [ ] API 返回 409（并发冲突）→ 刷新列表 + toast "事件状态已变更，已刷新"

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | 操作菜单显示/隐藏逻辑 |
| Unit | Snooze 时间计算 |
| Unit | Optimistic update 逻辑 |
| Unit | 错误回滚逻辑 |
| Component | 确认对话框交互 |
| Component | Toast 显示 |
| Integration | API 调用成功/失败 |
| E2E | 完整操作流程 |

- [ ] Unit tests 覆盖所有操作类型
- [ ] Unit tests 覆盖 optimistic update 和回滚
- [ ] Component tests 覆盖对话框交互
- [ ] Integration tests 使用 MSW mock API
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] Verify in browser：所有操作流程、toast、对话框

---

#### US-007a: System Status API - 数据源健康状态接口

**Description:** As a 前端, I need 获取数据源健康状态的 API so that System Status 组件能展示真实数据。

**Acceptance Criteria:**

**功能验证：**
- [ ] 端点：`GET /api/system/status`
- [ ] Response schema：
  ```typescript
  interface SystemStatusResponse {
    overall_status: 'healthy' | 'degraded' | 'unhealthy';
    last_run_at: string;           // 最近一次 pipeline 运行时间
    next_run_at: string | null;    // 下次计划运行时间

    sources: {
      [key: string]: SourceStatus;  // key: equities, crypto, congress, hedgefunds, polymarket, news, sec
    };

    summary: {
      total_sources: number;
      healthy_sources: number;
      total_observations_today: number;
      total_events_active: number;
    };
  }

  interface SourceStatus {
    name: string;                  // 显示名称
    status: 'healthy' | 'degraded' | 'unhealthy' | 'disabled';
    last_success_at: string | null;
    last_error_at: string | null;
    last_error_message: string | null;
    observations_today: number;
    latency_ms: number | null;     // 最近一次抓取耗时

    // 详细指标（可选）
    details?: {
      records_fetched: number;
      records_failed: number;
      api_quota_remaining?: number;  // 如 NewsAPI
    };
  }
  ```

- [ ] overall_status 判定规则：
  | 状态 | 条件 |
  |------|------|
  | healthy | 所有 enabled 源都是 healthy |
  | degraded | 有 1-2 个源是 degraded/unhealthy，但核心源（equities, news）健康 |
  | unhealthy | 核心源不健康 或 >50% 源不健康 |

- [ ] 单个源 status 判定：
  | 状态 | 条件 |
  |------|------|
  | healthy | 最近 1 小时内成功抓取，无错误 |
  | degraded | 最近 4 小时内成功，但有 warning 或部分失败 |
  | unhealthy | 最近 4 小时内无成功抓取，或连续 3 次失败 |
  | disabled | 在 config 中被禁用 |

**边界条件：**
- [ ] 从未运行过 pipeline → `last_run_at = null`, overall_status = 'unhealthy'
- [ ] 某个源从未启用过 → status = 'disabled'
- [ ] 数据库无 run_history 记录 → 返回默认结构，所有源 unhealthy

**错误处理：**
- [ ] 数据库查询失败 → 500 错误，`{ error: "Unable to fetch status" }`

**示例：**

```json
{
  "overall_status": "degraded",
  "last_run_at": "2026-01-21T06:00:00Z",
  "next_run_at": "2026-01-22T06:00:00Z",
  "sources": {
    "equities": {
      "name": "Equities (yfinance)",
      "status": "healthy",
      "last_success_at": "2026-01-21T06:00:00Z",
      "observations_today": 14,
      "latency_ms": 2500
    },
    "congress": {
      "name": "Congress Trading",
      "status": "degraded",
      "last_success_at": "2026-01-21T06:00:00Z",
      "last_error_at": "2026-01-21T06:00:05Z",
      "last_error_message": "Capitol Trades API rate limited, using cache",
      "observations_today": 3
    },
    "news": {
      "name": "News (NewsAPI)",
      "status": "unhealthy",
      "last_success_at": "2026-01-20T06:00:00Z",
      "last_error_at": "2026-01-21T06:00:00Z",
      "last_error_message": "NewsAPI quota exceeded",
      "observations_today": 0,
      "details": { "api_quota_remaining": 0 }
    }
  },
  "summary": {
    "total_sources": 7,
    "healthy_sources": 5,
    "total_observations_today": 45,
    "total_events_active": 8
  }
}
```

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | overall_status 判定逻辑 |
| Unit | 单个源 status 判定逻辑 |
| Unit | 边界：无数据、首次运行 |
| Integration | 完整 API 调用 |

- [ ] Unit tests 覆盖状态判定逻辑
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] API 文档更新

---

#### US-007b: System Status - 数据源健康状态 UI

**Description:** As a 研究者, I want 看到各数据源的健康状态 so that 我知道今天的数据是否完整。

**Acceptance Criteria:**

**功能验证：**
- [ ] 组件位置：Today 页面顶部
- [ ] 组件布局：
  ```
  ┌─────────────────────────────────────────────────────────────────┐
  │ System Status                               Last run: 2小时前 🔄 │
  ├─────────────────────────────────────────────────────────────────┤
  │ ● Healthy    5/7 sources healthy    45 observations    8 events │
  ├─────────────────────────────────────────────────────────────────┤
  │ 🟢 Equities   🟢 Crypto   🟡 Congress   🟢 13F   🔴 News   🟢 Poly   🟢 SEC │
  │    (14)         (10)        (3)⚠️        (5)      (0)❌      (8)       (5) │
  └─────────────────────────────────────────────────────────────────┘
  ```

- [ ] 状态指示器颜色：
  | 状态 | 颜色 | 图标 |
  |------|------|------|
  | healthy | 绿色 `#22C55E` | 🟢 |
  | degraded | 黄色 `#F59E0B` | 🟡 + ⚠️ |
  | unhealthy | 红色 `#EF4444` | 🔴 + ❌ |
  | disabled | 灰色 `#9CA3AF` | ⚫ |

- [ ] Overall status 显示：
  | 状态 | 文字 | 背景色 |
  |------|------|--------|
  | healthy | `● Healthy` | 浅绿背景 |
  | degraded | `● Degraded` | 浅黄背景 |
  | unhealthy | `● Unhealthy` | 浅红背景 |

- [ ] Hover 显示详情 tooltip：
  ```
  ┌────────────────────────────┐
  │ Congress Trading           │
  │ Status: Degraded           │
  │ Last success: 2小时前       │
  │ Observations: 3            │
  │ ⚠️ Capitol Trades API rate │
  │    limited, using cache    │
  └────────────────────────────┘
  ```

- [ ] 刷新按钮（🔄）：手动刷新状态
- [ ] 自动刷新：每 1 分钟

**状态处理：**
- [ ] Loading：显示 Skeleton
- [ ] Error：显示 "无法获取系统状态" + 重试按钮
- [ ] 展开/折叠：默认折叠只显示 overall，点击展开详情

**交互细节：**
- [ ] 点击单个源名称 → 跳转到 Sources 页对应 panel
- [ ] 点击 "8 events" → 跳转到 Signal Inbox

**边界条件：**
- [ ] 所有源都 disabled → 显示 "未配置数据源"
- [ ] last_run_at 超过 24 小时 → 显示警告 "数据可能已过期"

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | 状态颜色映射 |
| Unit | Overall status 渲染 |
| Component | Tooltip 显示 |
| Component | 展开/折叠交互 |
| Component | 各种状态组合 |

- [ ] Component tests 覆盖所有状态组合
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] Verify in browser：各种状态、tooltip、展开折叠
- [ ] 无障碍：状态信息可被屏幕阅读器读取

---

### Epic 3: 事件详情页（P0）

#### US-008a: Event Detail API - 事件详情数据接口

**Description:** As a 前端, I need 获取事件详情的 API so that Event Detail 页面能展示完整信息。

**Acceptance Criteria:**

**功能验证：**
- [ ] 端点：`GET /api/events/{eventId}`
- [ ] Response schema：
  ```typescript
  interface EventDetailResponse {
    event: EventDetail;
    evidence_timeline: ObservationTimelineEntry[];
    fact_spotlight: FactSpotlight;
    recommendation: Recommendation;
  }

  interface EventDetail {
    // 基础信息（继承自 Event）
    id: string;
    primary_entity: Entity;
    secondary_entities: Entity[];
    event_type: EventType;
    status: EventStatus;
    title: string;
    title_template: string;

    // 分数
    attention_score: number;
    anomaly_score: number;
    catalyst_score: number;
    flow_score: number;
    confidence_score: number;

    // 统计
    observation_counts: ObservationCounts;
    signal_ids: string[];

    // 时间
    start_at: string;
    last_update_at: string;
    created_at: string;

    // 用户状态
    pinned: boolean;
    snoozed_until: string | null;
    dismissed_reason: string | null;

    // 层级
    parent_event_id: string | null;
    child_events: EventSummary[];  // 如果是 Primary Event
  }

  interface ObservationTimelineEntry {
    id: string;
    source_type: string;
    observed_at: string;
    title: string;
    summary: string;
    source_url: string;
    fact_entries: FactEntry[];
    entity_mapping_confidence: number;
  }

  interface FactSpotlight {
    grouped_facts: GroupedFact[];
    relevance_algorithm_version: string;
  }

  interface GroupedFact {
    category: string;  // "市场数据" | "交易活动" | "新闻事件" | "监管文件" | "预测市场"
    facts: FactEntry[];
    relevance_score: number;  // 0-100
  }

  interface FactEntry {
    fact_id: string;
    fact_type: string;
    value: any;
    unit: string | null;
    source_observation_id: string;
    relevance_score: number;
  }

  interface Recommendation {
    type: "trade_idea" | "research_plan";
    content: TradeIdea | ResearchPlan;
    gate_result: GateResult;
  }

  interface TradeIdea {
    recommendation: "做多" | "做空" | "观望";
    entry_range: string | null;
    invalidation: string;  // 必填
    rationale_points: string[];
    supporting_evidence: EvidenceSummary[];
  }

  interface ResearchPlan {
    research_questions: string[];
    watch_points: string[];
    why_not_trade_yet: string;
  }

  interface GateResult {
    passed: boolean;
    confidence: number;
    missing_criteria: string[];
  }
  ```

- [ ] Evidence Timeline 排序：按 `observed_at` 降序（最新在前）
- [ ] FactSpotlight 只包含 relevance_score >= 50 的 facts
- [ ] Recommendation 根据 US-010 的门控逻辑生成

**边界条件：**
- [ ] eventId 不存在 → 404 错误
- [ ] Event 无 observations → `evidence_timeline = []`
- [ ] Event 无 facts → `fact_spotlight.grouped_facts = []`
- [ ] 门控未通过 → `recommendation.type = "research_plan"`

**错误处理：**
- [ ] 数据库查询超时 → 500 错误
- [ ] 门控引擎失败 → 使用默认 Research Plan

**示例：**

```json
{
  "event": {
    "id": "evt-001",
    "primary_entity": { "symbol": "NVDA", "name": "NVIDIA Corp", "entity_type": "ticker" },
    "event_type": "mixed",
    "title": "佩洛西买入 NVDA + 新品发布 + 价格异动",
    "attention_score": 85,
    ...
  },
  "evidence_timeline": [
    {
      "id": "obs-003",
      "source_type": "market",
      "observed_at": "2026-01-21T16:00:00Z",
      "title": "NVDA +8% on volume spike",
      "summary": "Price increased 8.2% with 3.2x average volume",
      "source_url": "https://finance.yahoo.com/quote/NVDA",
      "fact_entries": [
        { "fact_type": "price_change_pct", "value": 8.2, "unit": "%" },
        { "fact_type": "volume_ratio", "value": 3.2, "unit": "x" }
      ]
    },
    ...
  ],
  "fact_spotlight": {
    "grouped_facts": [
      {
        "category": "交易活动",
        "facts": [
          {
            "fact_id": "fact-001",
            "fact_type": "trade_amount_min",
            "value": 1000001,
            "unit": "USD",
            "source_observation_id": "obs-001",
            "relevance_score": 90
          }
        ],
        "relevance_score": 90
      }
    ]
  },
  "recommendation": {
    "type": "trade_idea",
    "content": {
      "recommendation": "做多",
      "entry_range": "$850-$870",
      "invalidation": "跌破$820或Pelosi披露卖出",
      "rationale_points": [
        "国会议员买入信号（Pelosi，1-5M区间）",
        "新品发布催化，预期营收增长",
        "价格+8%突破阻力位，成交量确认"
      ],
      "supporting_evidence": [...]
    },
    "gate_result": {
      "passed": true,
      "confidence": 88,
      "missing_criteria": []
    }
  }
}
```

**测试要求：**
- [ ] Unit tests 覆盖所有响应字段
- [ ] Integration tests 完整 API 调用
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] API 文档更新

---

#### US-008b: Evidence Timeline UI - 证据时间线展示

**Description:** As a 研究者, I want 看到事件的完整证据链 so that 我能理解事件演变过程。

**Acceptance Criteria:**

**功能验证：**
- [ ] 组件布局（三栏）：
  ```
  ┌────────────────────────────────────────────────────────────┐
  │ 筛选器 │         时间线中部        │      右侧详情       │
  ├────────┼───────────────────────────┼─────────────────────┤
  │ [全部] │ ● 2h ago - Market         │  Market Data        │
  │ ☑ 市场  │   NVDA +8% volume spike   │  ─────────────────  │
  │ ☑ 新闻  │   🔗 Yahoo Finance        │  Price: +8.2%       │
  │ ☑ 国会  │                           │  Volume: 3.2x avg   │
  │ ☐ 13F  │ ● 6h ago - News           │  Last: $865.20      │
  │ ☐ SEC  │   NVDA announces new GPU  │  ─────────────────  │
  │ ☐ Poly │   🔗 TechCrunch           │  [View Source ↗]    │
  │        │                           │                     │
  │        │ ● 1d ago - Congress       │                     │
  │        │   Pelosi purchased NVDA   │                     │
  │        │   🔗 Capitol Trades       │                     │
  └────────┴───────────────────────────┴─────────────────────┘
  ```

- [ ] 时间线展示：
  - [ ] 垂直时间线，最新在上
  - [ ] 每条 observation 显示：
    | 元素 | 说明 |
    |------|------|
    | 时间戳 | 相对时间（2h ago）+ hover 显示绝对时间 |
    | 来源图标 | 📊 市场 / 📰 新闻 / 🏛 国会 / 🏦 13F / 📋 SEC / 🎯 Poly |
    | 标题 | 单行，超出省略 |
    | 来源链接 | 点击跳转原始数据 |
  - [ ] 点击某条 observation → 右侧详情面板展开

- [ ] 筛选器功能：
  - [ ] 默认全选
  - [ ] 点击取消选中 → 隐藏对应来源的 observations
  - [ ] 至少保留 1 个来源选中（不能全部取消）

- [ ] 右侧详情面板：
  - [ ] 显示选中 observation 的 fact_entries（格式化展示）
  - [ ] 显示 summary（完整文本）
  - [ ] "View Source" 按钮跳转到 source_url
  - [ ] 如果未选中任何 observation → 显示空状态

**边界条件：**
- [ ] observations = 0 → 显示 "暂无证据"
- [ ] 某个来源 count = 0 → 该筛选项显示为禁用状态
- [ ] source_url 为空 → 隐藏链接图标

**响应式设计：**
- [ ] 桌面：三栏布局
- [ ] 平板：筛选器折叠，时间线 + 详情两栏
- [ ] 手机：单栏，点击时间线项展开详情

**测试要求：**
- [ ] Component tests 覆盖筛选器交互
- [ ] Component tests 覆盖时间线渲染
- [ ] Component tests 覆盖详情面板
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Verify in browser

---

#### US-009a: FactTable Relevance 算法 - 事实相关性评分

**Description:** As a 数据引擎, I need 计算每个 Fact 与事件的相关性 so that Fact Spotlight 只显示最相关的信息。

**Acceptance Criteria:**

**功能验证：**
- [ ] 相关性评分算法（0-100）：
  ```python
  relevance_score = (
      type_weight * 0.4 +
      significance * 0.3 +
      freshness * 0.2 +
      entity_match * 0.1
  ) * 100
  ```

- [ ] 各因子计算规则：
  | 因子 | 计算方式 | 权重 |
  |------|----------|------|
  | **type_weight** | Fact 类型优先级（见下表） | 40% |
  | **significance** | 数值大小的归一化分数 | 30% |
  | **freshness** | 时间衰减（24h内=1.0, 7d内=0.5, >7d=0.2） | 20% |
  | **entity_match** | 是否匹配 primary_entity (1.0) 或 secondary (0.5) | 10% |

- [ ] Fact 类型优先级（type_weight）：
  | fact_type | 优先级分数 | 说明 |
  |-----------|-----------|------|
  | `trade_amount_*` | 1.0 | 交易金额最重要 |
  | `price_change_pct` | 0.9 | 价格变动 |
  | `volume_ratio` | 0.8 | 成交量异常 |
  | `politician_name` | 0.85 | 国会交易关键人物 |
  | `fund_name` | 0.8 | 机构名称 |
  | `form_type` | 0.7 | SEC 文件类型 |
  | `probability_change` | 0.75 | Polymarket 概率 |
  | `headline` | 0.6 | 新闻标题 |
  | 其他 | 0.5 | 默认 |

- [ ] Significance 计算（针对数值类 fact）：
  ```python
  def calculate_significance(fact: FactEntry) -> float:
      if fact.fact_type == "trade_amount_min":
          # 金额越大越重要，归一化到 0-1
          return min(fact.value / 10_000_000, 1.0)  # 1000万为上限
      elif fact.fact_type == "price_change_pct":
          return min(abs(fact.value) / 20, 1.0)  # 20% 为上限
      elif fact.fact_type == "volume_ratio":
          return min(fact.value / 5, 1.0)  # 5x 为上限
      # ... 其他类型
      else:
          return 0.5  # 非数值类默认中等重要性
  ```

- [ ] Freshness 时间衰减：
  ```python
  def calculate_freshness(observed_at: datetime) -> float:
      age_hours = (now - observed_at).total_seconds() / 3600
      if age_hours <= 24:
          return 1.0
      elif age_hours <= 168:  # 7 days
          return 0.5
      else:
          return 0.2
  ```

**边界条件：**
- [ ] Fact 无对应 observation → freshness = 0
- [ ] Fact value 为 NULL → significance = 0
- [ ] 未识别的 fact_type → type_weight = 0.5

**错误处理：**
- [ ] 计算异常（除零等）→ 返回默认分数 50

**示例：**

```python
# 输入：Fact
fact = {
    "fact_type": "trade_amount_min",
    "value": 1_000_001,
    "unit": "USD",
    "source_observation_id": "obs-001"
}

observation = {
    "observed_at": "2026-01-20T10:00:00Z"  # 1天前
}

event = {
    "primary_entity_id": "nvda"
}

# 计算
type_weight = 1.0  # trade_amount_min 最高优先级
significance = min(1_000_001 / 10_000_000, 1.0) = 0.1
freshness = 1.0  # 24h 内
entity_match = 1.0  # 匹配 primary_entity

relevance_score = (1.0*0.4 + 0.1*0.3 + 1.0*0.2 + 1.0*0.1) * 100
               = (0.4 + 0.03 + 0.2 + 0.1) * 100
               = 73

# 输出
{
    "fact_id": "fact-001",
    "relevance_score": 73
}
```

**测试要求：**
- [ ] Unit tests 覆盖所有 fact_type 的 type_weight
- [ ] Unit tests 覆盖 significance 计算（各种数值范围）
- [ ] Unit tests 覆盖 freshness 衰减（24h/7d/>7d）
- [ ] Unit tests 覆盖 entity_match（primary/secondary）
- [ ] 本 story 新增代码测试覆盖率 >= 95%
- [ ] Typecheck passes
- [ ] Lint passes

---

#### US-009b: FactTable Spotlight UI - 关键事实展示

**Description:** As a 研究者, I want 看到事件的关键事实 so that 我能快速理解核心信息。

**Acceptance Criteria:**

**功能验证：**
- [ ] 组件布局：
  ```
  ┌─────────────────────────────────────────────────────────┐
  │ FactTable Spotlight                                     │
  ├─────────────────────────────────────────────────────────┤
  │ 📊 市场数据 (相关性: 85)                                │
  │ ├─ Price Change: +8.2%                                  │
  │ ├─ Volume Ratio: 3.2x                                   │
  │ └─ Last Price: $865.20                                  │
  │                                                         │
  │ 🏛 交易活动 (相关性: 90)                                │
  │ ├─ Politician: Nancy Pelosi                             │
  │ ├─ Amount: $1,000,001 - $5,000,000                     │
  │ └─ Transaction Type: Purchase                           │
  │                                                         │
  │ 📰 新闻事件 (相关性: 70)                                │
  │ └─ Headline: NVDA announces new GPU architecture        │
  └─────────────────────────────────────────────────────────┘
  ```

- [ ] 分组显示：
  - [ ] 按 category 分组（来自 API 的 `grouped_facts`）
  - [ ] 每组显示 category 名称 + 平均相关性分数
  - [ ] 组内 facts 按 relevance_score 降序排列
  - [ ] 只显示 relevance_score >= 50 的 facts

- [ ] Fact 显示格式：
  | fact_type | 显示格式 |
  |-----------|----------|
  | `trade_amount_*` | `$1,000,001 - $5,000,000` |
  | `price_change_pct` | `+8.2%` |
  | `volume_ratio` | `3.2x` |
  | `politician_name` | `Nancy Pelosi` |
  | 其他 | `{value} {unit}` |

- [ ] 相关性分数展示：
  - [ ] >= 80：🟢 高相关
  - [ ] 60-79：🟡 中相关
  - [ ] 50-59：⚪ 低相关
  - [ ] < 50：不显示

**边界条件：**
- [ ] 无 facts（relevance >= 50）→ 显示 "暂无关键事实"
- [ ] 某个 category 无 facts → 不显示该分组

**交互细节：**
- [ ] 点击某个 Fact → 跳转到 Evidence Timeline 对应的 observation
- [ ] Hover 显示完整数据（如果有截断）

**测试要求：**
- [ ] Component tests 覆盖分组渲染
- [ ] Component tests 覆盖格式化显示
- [ ] Component tests 覆盖空状态
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Verify in browser

---

#### US-010: Action Panel - 门控引擎与建议生成

**Description:** As a 决策引擎, I need 根据配置化规则判断是否生成 Trade Idea so that 只有高质量信号才输出可执行建议。

**Acceptance Criteria:**

**功能验证：**
- [ ] 门控配置（`config.yaml`）：
  ```yaml
  trade_idea_gates:
    min_confidence: 70          # 最低置信度
    min_sources: 2              # 最少数据源数量
    required_evidence:
      - type: "market"          # 必须有市场数据
        optional: false
      - type: "flow"            # Congress 或 13F 至少一个
        options: ["congress", "13f"]
        optional: false
    invalidation_required: true # 必须有失效条件

  research_plan_fallback:
    enabled: true
    min_confidence: 50          # Research Plan 最低门槛
  ```

- [ ] 门控逻辑：
  ```python
  def evaluate_gate(event: Event, config: GateConfig) -> GateResult:
      """
      1. 检查 confidence >= min_confidence
      2. 检查数据源数量 >= min_sources
      3. 检查 required_evidence 是否满足
      4. 如果全部通过 → passed=True, 生成 Trade Idea
      5. 如果部分通过 → passed=False, 生成 Research Plan
      """
  ```

- [ ] Trade Idea 生成（门控通过时）：
  - [ ] 必填字段：
    | 字段 | 生成规则 |
    |------|----------|
    | `recommendation` | 基于 flow_score: >60做多, <40做空, else观望 |
    | `invalidation` | 从 FactTable 提取关键反向指标 + LLM 润色 |
    | `rationale_points` | 从 Top 3 observations 提取，3-5条 |
    | `supporting_evidence` | 关联的 observations 摘要 |
  - [ ] 可选字段：
    | 字段 | 生成规则 |
    |------|----------|
    | `entry_range` | 如果有市场数据，计算当前价 ±2% |

- [ ] Research Plan 生成（门控未通过时）：
  - [ ] 必填字段：
    | 字段 | 生成规则 |
    |------|----------|
    | `research_questions` | 识别缺失的证据类型，生成 2-4 个问题 |
    | `watch_points` | 明天应该关注的数据源和指标 |
    | `why_not_trade_yet` | 说明缺失的关键条件 |

**Invalidation 生成规则：**
- [ ] 如果有 Congress 交易 → "议员披露卖出" 或 "跌破关键支撑位"
- [ ] 如果有价格数据 → "跌破 ${price * 0.95}" 或 "涨破 ${price * 1.05}"
- [ ] 如果有 Polymarket → "概率回落至 X% 以下"
- [ ] 使用 LLM 润色为自然语言（可选，失败时用模板）

**边界条件：**
- [ ] confidence < 50 → 不生成任何建议，只显示事件
- [ ] 所有 required_evidence 缺失 → Research Plan，列出所有缺失项
- [ ] invalidation 生成失败 → 使用默认值 "观察关键支撑位破位"

**错误处理：**
- [ ] 门控配置缺失 → 使用默认配置
- [ ] LLM 调用失败 → 使用模板生成

**示例：**

```yaml
# 输入：Event
event:
  attention_score: 85
  confidence_score: 88
  observation_counts:
    congress: 1
    news: 2
    market: 1
    total: 4

# 门控评估
gate_result:
  passed: true
  confidence: 88
  missing_criteria: []

# 输出：Trade Idea
{
  "type": "trade_idea",
  "content": {
    "recommendation": "做多",
    "entry_range": "$850-$870",
    "invalidation": "跌破$820或Pelosi披露卖出",
    "rationale_points": [
      "国会议员Pelosi买入信号（1-5M区间）",
      "新品发布催化，预期营收增长",
      "价格+8%突破阻力位，成交量确认"
    ],
    "supporting_evidence": [...]
  },
  "gate_result": {
    "passed": true,
    "confidence": 88,
    "missing_criteria": []
  }
}

# 门控未通过示例（缺少市场数据）
gate_result:
  passed: false
  confidence: 65
  missing_criteria: ["market"]

# 输出：Research Plan
{
  "type": "research_plan",
  "content": {
    "research_questions": [
      "当前价格和成交量是否确认突破？",
      "该议员的历史交易胜率如何？"
    ],
    "watch_points": [
      "明天关注市场数据（价格、成交量）",
      "验证新品发布的市场反应"
    ],
    "why_not_trade_yet": "缺少市场数据确认，无法判断入场时机"
  },
  "gate_result": {
    "passed": false,
    "confidence": 65,
    "missing_criteria": ["market"]
  }
}
```

**测试要求：**
- [ ] Unit tests 覆盖门控所有规则
- [ ] Unit tests 覆盖 Trade Idea 生成
- [ ] Unit tests 覆盖 Research Plan 生成
- [ ] Unit tests 覆盖 invalidation 生成规则
- [ ] Unit tests 覆盖边界条件
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes

---

#### US-011: Action Panel UI - 建议展示

**Description:** As a 研究者, I want 看到可执行的交易建议或研究计划 so that 我知道该采取什么行动。

**Acceptance Criteria:**

**功能验证：**
- [ ] 组件布局（Trade Idea）：
  ```
  ┌────────────────────────────────────────────────────────┐
  │ 💡 Trade Idea                                          │
  ├────────────────────────────────────────────────────────┤
  │ 建议: 做多 NVDA                                         │
  │ 入场区间: $850 - $870                                   │
  │                                                        │
  │ 核心理由:                                               │
  │ 1. 国会议员Pelosi买入信号（1-5M区间）                    │
  │ 2. 新品发布催化，预期营收增长                            │
  │ 3. 价格+8%突破阻力位，成交量确认                         │
  │                                                        │
  │ ⚠️ 失效条件:                                           │
  │ 跌破$820或Pelosi披露卖出                                │
  │                                                        │
  │ [Copy to Clipboard]  [Add to Watchlist]                │
  └────────────────────────────────────────────────────────┘
  ```

- [ ] 组件布局（Research Plan）：
  ```
  ┌────────────────────────────────────────────────────────┐
  │ 🔍 Research Plan                                       │
  ├────────────────────────────────────────────────────────┤
  │ 待解答:                                                 │
  │ • 当前价格和成交量是否确认突破？                          │
  │ • 该议员的历史交易胜率如何？                             │
  │                                                        │
  │ 明天关注:                                               │
  │ • 市场数据（价格、成交量）                               │
  │ • 验证新品发布的市场反应                                 │
  │                                                        │
  │ ℹ️ 暂不交易原因:                                        │
  │ 缺少市场数据确认，无法判断入场时机                         │
  │                                                        │
  │ [Mark as Open Loop]                                    │
  └────────────────────────────────────────────────────────┘
  ```

- [ ] 显示规则：
  - [ ] `type = "trade_idea"` → 显示 Trade Idea 布局
  - [ ] `type = "research_plan"` → 显示 Research Plan 布局
  - [ ] 失效条件必须突出显示（⚠️ 图标 + 红色背景）

- [ ] 交互功能：
  - [ ] "Copy to Clipboard" → 复制建议内容为纯文本
  - [ ] "Add to Watchlist"（P2）→ 添加到用户关注列表
  - [ ] "Mark as Open Loop" → 将 Research Plan 标记为待追踪（P1）

**边界条件：**
- [ ] `entry_range = null` → 显示 "待确定"
- [ ] `invalidation` 过长 → 换行显示
- [ ] 无建议（confidence < 50）→ 显示 "数据不足，暂无建议"

**响应式设计：**
- [ ] 桌面：固定宽度居中
- [ ] 手机：全宽显示

**测试要求：**
- [ ] Component tests 覆盖 Trade Idea 渲染
- [ ] Component tests 覆盖 Research Plan 渲染
- [ ] Component tests 覆盖 Copy 功能
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Verify in browser

---

#### US-012: Event Detail - 页面级操作

**Description:** As a 研究者, I want 在事件详情页执行操作 so that 我能管理事件状态。

**Acceptance Criteria:**

**功能验证：**
- [ ] 复用 US-006 的操作逻辑：
  - Pin / Unpin
  - Snooze
  - Dismiss
  - Resolve

- [ ] 操作按钮位置：页面右上角，与 Event Card 的 `···` 菜单相同

- [ ] 操作成功后：
  - [ ] Toast 提示
  - [ ] 如果是 Dismiss/Resolve → 返回 Today 页面
  - [ ] 如果是 Pin/Snooze → 停留在详情页，UI 更新

**测试要求：**
- [ ] Component tests 复用 US-006 测试
- [ ] E2E tests 覆盖详情页操作流程
- [ ] Verify in browser

---

### Epic 4: Daily Brief 生成与归档（P0）

#### US-013a: FactTable 聚合与结构化数据准备

**Description:** As a 简报生成器, I need 从当日所有 Active Events 聚合 FactTable 数据 so that LLM 能基于真实事实生成叙事。

**Acceptance Criteria:**

**功能验证：**
- [ ] 数据聚合范围：当日所有 `status = new/ongoing` 且未 snoozed 的 Events
- [ ] FactTable 结构：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `date` | date | 简报日期 |
  | `summary_stats` | object | 总体统计 |
  | `top_events` | array | Top 5 events（按 attention_score） |
  | `trade_ideas` | array | 门控通过的 Trade Ideas |
  | `research_ideas` | array | 门控未通过但值得追踪的 Research Ideas |
  | `open_loops` | array | 前日未解决的 Open Loops（P1功能，当前可为空） |
  | `data_quality` | object | 数据源健康状态 |

- [ ] `summary_stats` 内容：
  ```typescript
  interface SummaryStats {
    total_events_active: number;
    total_events_new_today: number;  // 今天新增的
    total_observations_today: number;
    sources_healthy: number;
    sources_total: number;
    top_asset_classes: {  // 按事件数量排序
      ticker: number;
      crypto: number;
      polymarket: number;
    };
  }
  ```

- [ ] `top_events` 每项包含：
  ```typescript
  interface TopEventFact {
    event_id: string;
    entity_symbol: string;
    entity_name: string;
    event_type: EventType;
    title: string;
    attention_score: number;
    scores: {
      anomaly: number;
      catalyst: number;
      flow: number;
      confidence: number;
    };
    observation_summary: {
      congress: number;
      "13f": number;
      news: number;
      sec: number;
      polymarket: number;
      market: number;
    };
    latest_observation: {
      source_type: string;
      title: string;
      observed_at: string;
    };
    evidence_count: number;
  }
  ```

- [ ] `trade_ideas` 每项包含（从 Event Detail 的 Action Panel 提取）：
  ```typescript
  interface TradeIdeaFact {
    event_id: string;
    entity_symbol: string;
    recommendation: string;  // "做多" | "做空" | "观望"
    entry_range: string | null;
    invalidation: string;  // 必填，失效条件
    rationale_points: string[];  // 关键理由（3-5条）
    confidence: number;
    supporting_evidence: {
      source_type: string;
      summary: string;
    }[];
  }
  ```

- [ ] `research_ideas` 每项包含：
  ```typescript
  interface ResearchIdeaFact {
    event_id: string;
    entity_symbol: string;
    research_questions: string[];  // 要验证的问题
    watch_points: string[];  // 明天要关注的证据点
    confidence: number;
    why_not_trade_yet: string;  // 为什么还不能交易
  }
  ```

- [ ] `data_quality` 内容：
  ```typescript
  interface DataQualityFact {
    overall_status: 'healthy' | 'degraded' | 'unhealthy';
    last_run_at: string;
    sources: {
      [key: string]: {
        status: 'healthy' | 'degraded' | 'unhealthy' | 'disabled';
        observations_today: number;
        last_error: string | null;
      };
    };
  }
  ```

**聚合逻辑：**
```python
def aggregate_daily_facttable(date: datetime.date) -> FactTable:
    """
    1. 查询当日所有 Active Events（status=new/ongoing, not snoozed）
    2. 按 attention_score 排序，取 Top 5
    3. 对每个 Event，查询其 Action Panel 输出（来自 US-010 的门控逻辑）
    4. 区分 Trade Ideas（门控通过）和 Research Ideas（未通过）
    5. 汇总数据源健康状态（来自 US-007a）
    6. 返回结构化 FactTable
    """
```

**边界条件：**
- [ ] 当日无 Active Events → `top_events = []`, `trade_ideas = []`, `research_ideas = []`
- [ ] 所有 Events 都未通过门控 → `trade_ideas = []`, 但 `research_ideas` 非空
- [ ] 某个 Event 的 Action Panel 未生成 → 跳过该 Event，记录 warning
- [ ] 数据源全挂 → `data_quality.overall_status = 'unhealthy'`，简报仍生成但标注警告

**错误处理：**
- [ ] 数据库查询失败 → 抛出异常，简报生成失败（不降级）
- [ ] 单个 Event 数据损坏 → 跳过该 Event，记录 error，继续聚合其他
- [ ] Action Panel API 超时 → 使用默认 Research Idea 模板

**示例（输入/输出）：**

```python
# 输出：FactTable
fact_table = {
    "date": "2026-01-21",
    "summary_stats": {
        "total_events_active": 8,
        "total_events_new_today": 3,
        "total_observations_today": 45,
        "sources_healthy": 5,
        "sources_total": 7,
        "top_asset_classes": {"ticker": 6, "crypto": 2, "polymarket": 0}
    },
    "top_events": [
        {
            "event_id": "evt-001",
            "entity_symbol": "NVDA",
            "entity_name": "NVIDIA Corp",
            "event_type": "mixed",
            "title": "佩洛西买入 NVDA + 新品发布 + 价格异动",
            "attention_score": 85,
            "scores": {"anomaly": 78, "catalyst": 82, "flow": 90, "confidence": 88},
            "observation_summary": {"congress": 1, "news": 2, "market": 1, "total": 4},
            "latest_observation": {
                "source_type": "market",
                "title": "NVDA +8% on volume spike",
                "observed_at": "2026-01-21T16:00:00Z"
            },
            "evidence_count": 4
        },
        # ... Top 4 more
    ],
    "trade_ideas": [
        {
            "event_id": "evt-001",
            "entity_symbol": "NVDA",
            "recommendation": "做多",
            "entry_range": "$850-$870",
            "invalidation": "跌破$820或Pelosi披露卖出",
            "rationale_points": [
                "国会议员买入信号（Pelosi，1-5M区间）",
                "新品发布催化，预期营收增长",
                "价格+8%突破阻力位，成交量确认"
            ],
            "confidence": 88,
            "supporting_evidence": [
                {"source_type": "congress", "summary": "Pelosi purchased $1M-$5M"},
                {"source_type": "news", "summary": "NVDA announces new GPU architecture"},
                {"source_type": "market", "summary": "Price +8%, volume 3.2x average"}
            ]
        }
    ],
    "research_ideas": [
        {
            "event_id": "evt-005",
            "entity_symbol": "TSLA",
            "research_questions": [
                "Musk 的新工厂计划资金来源是什么？",
                "该工厂产能对Q2财报影响几何？"
            ],
            "watch_points": [
                "明天关注 SEC 8-K 文件",
                "等待分析师会议纪要"
            ],
            "confidence": 65,
            "why_not_trade_yet": "缺失关键财务细节，仅有新闻报道"
        }
    ],
    "data_quality": {
        "overall_status": "degraded",
        "last_run_at": "2026-01-21T06:00:00Z",
        "sources": {
            "equities": {"status": "healthy", "observations_today": 14, "last_error": None},
            "congress": {"status": "degraded", "observations_today": 3, "last_error": "Rate limited"},
            "news": {"status": "unhealthy", "observations_today": 0, "last_error": "Quota exceeded"}
        }
    }
}
```

**测试要求:**

| 测试类型 | 覆盖场景 | 文件位置 |
|----------|----------|----------|
| Unit | 聚合逻辑：Active Events 筛选 | `tests/unit/test_facttable_aggregator.py` |
| Unit | Top 5 排序逻辑 | 同上 |
| Unit | Trade/Research 分类逻辑 | 同上 |
| Unit | 边界：无事件、全部未通过门控 | 同上 |
| Unit | 错误处理：单个 Event 损坏 | 同上 |
| Integration | 完整聚合流程 | `tests/integration/test_daily_facttable.py` |

- [ ] Unit tests 覆盖聚合算法所有分支
- [ ] Unit tests 覆盖所有边界条件
- [ ] Unit tests 覆盖错误处理
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes

---

#### US-013b: LLM 叙事生成（带 Template Fallback）

**Description:** As a 简报生成器, I need 基于 FactTable 调用 LLM 生成可读叙事 so that 用户得到易读的简报，LLM 失败时必须有模板兜底。

**Acceptance Criteria:**

**功能验证：**
- [ ] 双通道策略：
  1. **Primary**: LLM 叙事生成（使用 US-001d 的 LLM 抽象层）
  2. **Fallback**: Template 引擎生成（LLM 失败/超时时）

- [ ] LLM Prompt 结构：
  ```
  你是一位专业的交易研究分析师。基于以下事实数据，生成一份结构化的每日简报。

  **重要约束**：
  1. 只使用提供的 FactTable 数据，严禁自造信息
  2. 所有数字、日期、名称必须与 FactTable 一致
  3. 如果 FactTable 某字段为空，不要编造内容
  4. 输出格式必须为 Markdown

  # FactTable 数据
  {json_dump(fact_table)}

  # 要求的输出结构
  ## Executive Summary
  - 用 2-3 句话概括今日市场重点

  ## Top Events（按重要性排序）
  - 每个事件 1 段，包含：资产、事件类型、关键证据、分数

  ## Trade Ideas
  - 每个 idea 包含：标的、建议、理由、失效条件

  ## Research Ideas
  - 每个 idea 包含：标的、待解答问题、明天关注点

  ## Data Quality
  - 数据源健康状况简述
  ```

- [ ] LLM 参数配置：
  | 参数 | 值 | 说明 |
  |------|---|------|
  | `model` | `anthropic/claude-3-haiku` | 成本优化 |
  | `max_tokens` | 2000 | 足够生成完整简报 |
  | `temperature` | 0.3 | 降低随机性，保持事实准确 |
  | `timeout` | 30s | 超时后降级到模板 |

- [ ] Template 引擎结构（Jinja2）：
  ```markdown
  # Daily Trading Brief - {{date}}

  ## Executive Summary
  今日共有 {{summary_stats.total_events_active}} 个活跃事件，
  新增 {{summary_stats.total_events_new_today}} 个。
  数据源状态：{{data_quality.overall_status}}。

  ## Top Events
  {% for event in top_events[:5] %}
  ### {{loop.index}}. {{event.entity_symbol}} - {{event.title}}
  - **类型**: {{event.event_type}}
  - **综合分数**: {{event.attention_score}}/100
  - **证据来源**: {{event.observation_summary | format_sources}}
  - **最新动态**: {{event.latest_observation.title}}
  {% endfor %}

  ## Trade Ideas
  {% for idea in trade_ideas %}
  ### {{idea.entity_symbol}} - {{idea.recommendation}}
  **理由**:
  {% for point in idea.rationale_points %}
  - {{point}}
  {% endfor %}
  **失效条件**: {{idea.invalidation}}
  **入场区间**: {{idea.entry_range or "待确定"}}
  {% endfor %}

  ## Research Ideas
  {% for idea in research_ideas %}
  ### {{idea.entity_symbol}}
  **待解答**:
  {% for q in idea.research_questions %}
  - {{q}}
  {% endfor %}
  **明天关注**: {{idea.watch_points | join(", ")}}
  {% endfor %}

  ## Data Quality
  总体状态: {{data_quality.overall_status}}
  {% if data_quality.overall_status != 'healthy' %}
  ⚠️ 以下数据源异常:
  {% for source, status in data_quality.sources.items() %}
  {% if status.status != 'healthy' %}
  - {{source}}: {{status.last_error}}
  {% endif %}
  {% endfor %}
  {% endif %}

  ---
  *Generated at {{generated_at}}*
  *Method: {{generation_method}}*
  ```

**LLM 幻觉检测：**
- [ ] 生成后验证规则：
  1. 提取 LLM 输出中所有 entity symbols → 必须全部在 FactTable 中
  2. 提取所有数字（分数、日期、金额）→ 必须与 FactTable 一致
  3. 检查是否出现 FactTable 中不存在的数据源名称
- [ ] 如果检测到幻觉 → 降级到 Template，记录 warning `"LLM hallucination detected"`

**边界条件：**
- [ ] FactTable 为空（无事件）→ Template 生成 "今日无活跃事件" 简报
- [ ] LLM 返回格式错误（非 Markdown）→ 降级到 Template
- [ ] LLM 返回超长（>5000 tokens）→ 截断并标注

**错误处理：**
- [ ] LLM API 超时（>30s）→ 降级到 Template，记录 `generation_method = 'template_timeout'`
- [ ] LLM API 返回 429（Rate limit）→ 降级到 Template，记录 `generation_method = 'template_ratelimit'`
- [ ] LLM API 返回 500 → 降级到 Template，记录 `generation_method = 'template_api_error'`
- [ ] OpenRouter 额度不足 → 降级到 Template，发送告警邮件给管理员
- [ ] Template 引擎失败 → 抛出异常，简报生成失败（这是最后防线）

**成本控制（使用 OpenRouter + Haiku）：**
- [ ] 预估每次调用成本：
  - Input: ~1500 tokens（FactTable JSON）× $0.00025/1K ≈ $0.0004
  - Output: ~1000 tokens × $0.00125/1K ≈ $0.0013
  - 总计 ≈ $0.0017/次
- [ ] 每日 1 次 ≈ $0.05/月
- [ ] 设置 OpenRouter 月度预算上限：$5

**示例（输入/输出）：**

```python
# 输入：FactTable（见 US-013a）
fact_table = {...}

# LLM 成功输出
llm_output = """
# Daily Trading Brief - 2026-01-21

## Executive Summary
今日市场呈现多点开花格局，共8个活跃事件值得关注。其中NVDA因国会买入+新品发布+价格异动形成三重共振，综合评分85分位居榜首。数据源整体健康度为降级状态，主要因NewsAPI配额耗尽。

## Top Events
### 1. NVDA - 佩洛西买入 NVDA + 新品发布 + 价格异动
- **类型**: 混合信号
- **综合分数**: 85/100（异常78, 催化82, 流90, 置信88）
- **证据来源**: 国会披露1条, 新闻2条, 市场数据1条
- **最新动态**: 股价+8%伴随3.2倍成交量放大

...（其他 Top Events）

## Trade Ideas
### NVDA - 做多
**理由**:
- 国会议员Pelosi买入信号（1-5M区间），历史准确率较高
- 新GPU架构发布催化，预期驱动营收增长
- 技术面突破阻力位$850，成交量确认有效

**失效条件**: 跌破$820或Pelosi披露卖出
**入场区间**: $850-$870

...（其他 Trade Ideas）

## Research Ideas
### TSLA
**待解答**:
- Musk新工厂计划的资金来源是什么？
- 该工厂产能对Q2财报影响几何？

**明天关注**: SEC 8-K文件, 分析师会议纪要

## Data Quality
总体状态: degraded
⚠️ 以下数据源异常:
- Congress Trading: Rate limited (使用缓存数据)
- News (NewsAPI): Quota exceeded (0条观察)

---
*Generated at 2026-01-21 06:30:00*
*Method: llm*
"""

# Template Fallback 输出（LLM 失败时）
template_output = """
# Daily Trading Brief - 2026-01-21

## Executive Summary
今日共有 8 个活跃事件，新增 3 个。数据源状态：degraded。

## Top Events
### 1. NVDA - 佩洛西买入 NVDA + 新品发布 + 价格异动
- **类型**: mixed
- **综合分数**: 85/100
- **证据来源**: congress(1), news(2), market(1)
- **最新动态**: NVDA +8% on volume spike

...

*Generated at 2026-01-21 06:30:00*
*Method: template_timeout*
"""
```

**测试要求：**

| 测试类型 | Provider | 覆盖场景 |
|----------|----------|----------|
| Unit | MockProvider | LLM 成功生成 |
| Unit | MockProvider | LLM 超时降级 |
| Unit | MockProvider | 幻觉检测与拒绝 |
| Unit | MockProvider | Template 引擎生成 |
| Unit | - | Template Jinja2 渲染正确性 |
| Integration | MockProvider | 完整双通道流程 |
| E2E (可选) | OpenRouterProvider | 真实 LLM 调用 |

- [ ] Unit tests 100% 使用 MockProvider，无需 API key
- [ ] Unit tests 覆盖幻觉检测所有规则
- [ ] Unit tests 覆盖所有降级场景
- [ ] Unit tests 覆盖 Template 引擎所有分支
- [ ] Integration test 验证双通道切换逻辑
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes

---

#### US-013c: Markdown + JSON 报告文件生成与落盘

**Description:** As a 简报生成器, I need 将生成的简报保存为 Markdown 和 JSON 文件 so that 用户可以通过邮件和 UI 两种方式访问。

**Acceptance Criteria:**

**功能验证：**
- [ ] 文件生成双格式：
  1. **Markdown 文件**：`reports/{YYYY-MM-DD}.md` - 用于邮件正文和 UI 渲染
  2. **JSON 文件**：`reports/{YYYY-MM-DD}.json` - 用于 API 和数据分析

- [ ] Markdown 文件结构：
  ```markdown
  # Daily Trading Brief - 2026-01-21

  *Generated at 2026-01-21 06:30:00 UTC*
  *Method: llm | Tradz v1.0*

  ---

  ## Executive Summary
  [LLM 或 Template 生成的内容]

  ## Top Events
  [事件列表]

  ## Trade Ideas 💡
  [可执行交易建议]

  ## Research Ideas 🔍
  [需要进一步研究的想法]

  ## Open Loops 🔄
  [前日未完成的追踪项]（P1功能，当前可为空）

  ## Data Quality 📊
  [数据源健康状态]

  ---

  *This report was generated automatically. All data is for informational purposes only.*
  ```

- [ ] JSON 文件结构：
  ```typescript
  interface DailyBriefJSON {
    metadata: {
      date: string;              // "2026-01-21"
      generated_at: string;      // ISO timestamp
      generation_method: string; // "llm" | "template_timeout" | "template_ratelimit" | ...
      tradz_version: string;     // "v1.0"
      llm_model: string | null;  // "anthropic/claude-3-haiku" or null if template
    };

    content: {
      markdown: string;          // 完整 Markdown 文本
      fact_table: FactTable;     // 原始 FactTable（来自 US-013a）
    };

    summary: {
      total_events: number;
      new_events_today: number;
      trade_ideas_count: number;
      research_ideas_count: number;
      data_quality_status: string;
    };

    performance: {
      generation_time_ms: number;
      llm_call_time_ms: number | null;
      template_fallback: boolean;
    };
  }
  ```

- [ ] 文件路径规范：
  | 类型 | 路径模式 | 示例 |
  |------|----------|------|
  | Markdown | `reports/{YYYY-MM-DD}.md` | `reports/2026-01-21.md` |
  | JSON | `reports/{YYYY-MM-DD}.json` | `reports/2026-01-21.json` |
  | 备份 | `reports/archive/{YYYY}/{MM}/{YYYY-MM-DD}.md` | `reports/archive/2026/01/2026-01-21.md` |

- [ ] 文件写入流程：
  ```python
  def save_daily_brief(brief_markdown: str, fact_table: FactTable, metadata: dict):
      """
      1. 生成文件名：{date}.md / {date}.json
      2. 检查 reports/ 目录是否存在，不存在则创建
      3. 写入 Markdown 文件
      4. 构造 JSON 结构并写入 JSON 文件
      5. （可选）创建归档副本到 reports/archive/{year}/{month}/
      6. 返回文件路径
      """
  ```

- [ ] 文件完整性校验：
  - [ ] Markdown 文件必须包含所有必需 section（Executive Summary, Top Events, etc.）
  - [ ] JSON 文件必须通过 schema 验证（使用 Pydantic）
  - [ ] 文件大小限制：Markdown < 500KB, JSON < 1MB
  - [ ] 文件编码：UTF-8

**边界条件：**
- [ ] 文件已存在 → 覆盖（保留原文件为 `.bak` 备份）
- [ ] Markdown 内容过长（> 500KB）→ 截断 + 警告标记
- [ ] reports/ 目录不存在 → 自动创建
- [ ] 磁盘空间不足 → 抛出异常，不生成文件
- [ ] 文件名包含非法字符 → 不应发生（日期格式固定），但仍需验证

**错误处理：**
- [ ] 写入权限不足 → 抛出 `PermissionError`，记录详细错误信息
- [ ] 磁盘满 → 抛出 `IOError`，发送告警
- [ ] JSON 序列化失败（如 FactTable 包含不可序列化对象）→ 使用自定义 encoder，记录 warning
- [ ] Markdown 渲染失败 → 保存原始文本 + 错误标记

**示例（输入/输出）：**

```python
# 输入
brief_markdown = """
# Daily Trading Brief - 2026-01-21
...（完整 Markdown）
"""

fact_table = {...}  # 来自 US-013a

metadata = {
    "date": "2026-01-21",
    "generated_at": "2026-01-21T06:30:00Z",
    "generation_method": "llm",
    "llm_model": "anthropic/claude-3-haiku",
    "generation_time_ms": 5234,
    "llm_call_time_ms": 4800
}

# 调用
save_daily_brief(brief_markdown, fact_table, metadata)

# 输出文件 1: reports/2026-01-21.md
"""
# Daily Trading Brief - 2026-01-21
...（完整 Markdown）
"""

# 输出文件 2: reports/2026-01-21.json
{
  "metadata": {
    "date": "2026-01-21",
    "generated_at": "2026-01-21T06:30:00Z",
    "generation_method": "llm",
    "tradz_version": "v1.0",
    "llm_model": "anthropic/claude-3-haiku"
  },
  "content": {
    "markdown": "# Daily Trading Brief...",
    "fact_table": {...}
  },
  "summary": {
    "total_events": 8,
    "new_events_today": 3,
    "trade_ideas_count": 2,
    "research_ideas_count": 3,
    "data_quality_status": "degraded"
  },
  "performance": {
    "generation_time_ms": 5234,
    "llm_call_time_ms": 4800,
    "template_fallback": false
  }
}
```

**测试要求：**

| 测试类型 | 覆盖场景 | 文件位置 |
|----------|----------|----------|
| Unit | Markdown 文件写入 | `tests/unit/test_brief_file_writer.py` |
| Unit | JSON 文件写入 + schema 验证 | 同上 |
| Unit | 文件覆盖 + 备份逻辑 | 同上 |
| Unit | 边界：大文件截断、磁盘满 | 同上 |
| Unit | 错误处理：权限、序列化失败 | 同上 |
| Integration | 完整文件生成流程 | `tests/integration/test_daily_brief_generation.py` |

- [ ] Unit tests 覆盖所有文件操作
- [ ] Unit tests 覆盖边界条件（大文件、已存在等）
- [ ] Unit tests 覆盖错误处理（使用 mock 模拟 IOError）
- [ ] JSON schema 验证测试（使用 Pydantic）
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes

---

#### US-014: 简报归档与 DuckDB 持久化

**Description:** As a 系统管理员, I need 将每日简报元数据持久化到 DuckDB so that 可以查询历史简报和生成统计报告。

**Acceptance Criteria:**

**功能验证：**
- [ ] 数据库表：`daily_briefs`（见 Technical Considerations 中的 schema）
- [ ] 每次简报生成后必须插入 1 条记录：
  ```sql
  INSERT INTO daily_briefs (
    id, date, summary_json, report_path_md, report_path_json,
    generation_method, created_at, run_id
  ) VALUES (...);
  ```

- [ ] 字段填充规则：
  | 字段 | 类型 | 填充规则 |
  |------|------|----------|
  | `id` | UUID | 自动生成 |
  | `date` | DATE | 简报日期（非生成时间） |
  | `summary_json` | JSON | 包含 `summary` 和 `performance` 字段（来自 US-013c 的 JSON） |
  | `report_path_md` | TEXT | 相对路径 `reports/2026-01-21.md` |
  | `report_path_json` | TEXT | 相对路径 `reports/2026-01-21.json` |
  | `generation_method` | VARCHAR | `llm` / `template_*` |
  | `created_at` | TIMESTAMP | 简报生成完成时间（UTC） |
  | `run_id` | UUID | FK 到 `run_history` 表，关联本次 pipeline 运行 |

- [ ] 唯一性约束：`date` 字段必须唯一（每天只能有 1 份简报）
- [ ] 如果同一天重复生成 → 更新现有记录（UPSERT），保留旧记录到 `daily_briefs_history` 表（可选）

- [ ] 查询接口：
  ```python
  def get_daily_brief(date: datetime.date) -> DailyBrief | None:
      """根据日期查询简报记录"""

  def list_daily_briefs(
      start_date: datetime.date,
      end_date: datetime.date,
      limit: int = 30
  ) -> List[DailyBrief]:
      """查询日期范围内的简报列表"""

  def get_generation_stats(days: int = 30) -> dict:
      """
      统计最近 N 天的简报生成情况
      返回：{
        "total": 30,
        "llm_success": 28,
        "template_fallback": 2,
        "avg_generation_time_ms": 5200
      }
      """
  ```

**边界条件：**
- [ ] 首次生成（表不存在）→ 自动创建表
- [ ] 同一天重复生成 → UPSERT，覆盖原记录
- [ ] 文件路径超长（> 500 字符）→ 截断，记录 warning
- [ ] `run_id` 为 NULL（手动触发生成）→ 允许，但记录 warning

**错误处理：**
- [ ] 数据库连接失败 → 抛出异常，简报文件仍保存（文件优先）
- [ ] INSERT 失败 → 记录 error，但不影响文件生成
- [ ] UNIQUE 约束冲突（并发生成）→ 重试 UPSERT，记录 warning

**示例（输入/输出）：**

```python
# 输入：简报元数据
brief_metadata = {
    "date": datetime.date(2026, 1, 21),
    "summary_json": {
        "total_events": 8,
        "new_events_today": 3,
        "trade_ideas_count": 2,
        "research_ideas_count": 3,
        "data_quality_status": "degraded"
    },
    "report_path_md": "reports/2026-01-21.md",
    "report_path_json": "reports/2026-01-21.json",
    "generation_method": "llm",
    "created_at": datetime.datetime(2026, 1, 21, 6, 30, 0, tzinfo=timezone.utc),
    "run_id": uuid.UUID("...")
}

# 插入数据库
db.insert_daily_brief(brief_metadata)

# 查询验证
brief = db.get_daily_brief(datetime.date(2026, 1, 21))
assert brief.generation_method == "llm"
assert brief.summary_json["total_events"] == 8

# 统计查询
stats = db.get_generation_stats(days=30)
# 输出示例
{
    "total": 30,
    "llm_success": 28,
    "template_fallback": 2,
    "avg_generation_time_ms": 5200,
    "success_rate": 0.933
}
```

**测试要求：**

| 测试类型 | 覆盖场景 | 文件位置 |
|----------|----------|----------|
| Unit | INSERT 逻辑 | `tests/unit/test_brief_database.py` |
| Unit | UPSERT 重复日期 | 同上 |
| Unit | 查询接口（单个/列表/统计） | 同上 |
| Unit | 边界：NULL run_id、超长路径 | 同上 |
| Integration | 完整持久化流程（mock DuckDB） | `tests/integration/test_brief_persistence.py` |
| Integration | 并发 UPSERT | 同上 |

- [ ] Unit tests 覆盖所有 CRUD 操作
- [ ] Unit tests 覆盖 UPSERT 逻辑
- [ ] Unit tests 覆盖统计查询
- [ ] Integration tests 使用临时 DuckDB 数据库
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes

---

#### US-015: 邮件发送（SMTP + HTML 渲染）

**Description:** As a 用户, I want 每天早上收到邮件简报 so that 我不需要主动打开系统就能获取信息。

**Acceptance Criteria:**

**功能验证：**
- [ ] 邮件发送触发：简报生成完成后自动发送（除非 `--skip-email` flag）
- [ ] 邮件配置（来自 `.env`）：
  | 配置项 | 环境变量 | 默认值 | 说明 |
  |--------|----------|--------|------|
  | SMTP 服务器 | `SMTP_HOST` | - | 必填 |
  | SMTP 端口 | `SMTP_PORT` | 587 | TLS 端口 |
  | 用户名 | `SMTP_USER` | - | 必填 |
  | 密码 | `SMTP_PASSWORD` | - | 必填 |
  | 发件人 | `SMTP_FROM` | `tradz@example.com` | |
  | 收件人 | `SMTP_TO` | - | 逗号分隔，必填 |
  | DRY_RUN | `DRY_RUN` | 0 | 1=不实际发送 |

- [ ] 邮件结构：
  ```python
  {
    "subject": "Daily Trading Brief - 2026-01-21",
    "from": "Tradz <tradz@example.com>",
    "to": ["user@example.com", "team@example.com"],
    "reply_to": "noreply@example.com",
    "content_type": "multipart/alternative",  # 同时支持 HTML 和纯文本
    "body_text": "[Markdown 转纯文本]",
    "body_html": "[Markdown 转 HTML + CSS 样式]",
    "attachments": []  # P2 可选：附加 JSON 文件
  }
  ```

- [ ] HTML 渲染：
  - [ ] 使用 `markdown` 库将 Markdown 转换为 HTML
  - [ ] 应用 CSS 样式（内联样式，兼容邮件客户端）：
    ```html
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
      h1 { color: #1a1a1a; border-bottom: 2px solid #3B82F6; }
      h2 { color: #3B82F6; margin-top: 24px; }
      .score-bar { background: #E5E7EB; height: 8px; border-radius: 4px; }
      .score-fill { background: #22C55E; height: 100%; }
      table { border-collapse: collapse; width: 100%; }
      td, th { padding: 8px; border: 1px solid #E5E7EB; }
    </style>
    ```
  - [ ] 确保链接可点击（如果包含事件详情链接）
  - [ ] 适配暗色模式（可选，P2）

- [ ] 纯文本 Fallback：
  - [ ] 直接使用 Markdown 文本（不转换），兼容不支持 HTML 的邮件客户端

**DRY_RUN 模式：**
- [ ] `DRY_RUN=1` 时：
  - 不实际发送邮件
  - 将邮件内容保存到 `reports/{date}_email.html`
  - 日志输出 "DRY_RUN: Email saved to ..."
  - 返回成功状态

**边界条件：**
- [ ] 收件人列表为空 → 跳过发送，记录 warning
- [ ] Markdown 转 HTML 失败 → 使用纯文本 Fallback，记录 error
- [ ] HTML 过大（> 2MB）→ 截断 + 添加 "查看完整报告" 链接
- [ ] SMTP 配置缺失 → 跳过发送，记录 error，不影响简报生成

**错误处理：**
- [ ] SMTP 连接失败 → 重试 3 次（间隔 5s/10s/20s），仍失败则记录 error，不抛异常
- [ ] 认证失败（401）→ 不重试，记录 error，发送告警
- [ ] 发送超时（>30s）→ 取消发送，记录 timeout error
- [ ] 邮件被拒绝（如收件人不存在）→ 记录 warning，继续尝试其他收件人

**示例（输入/输出）：**

```python
# 输入：简报 Markdown
markdown_content = """
# Daily Trading Brief - 2026-01-21
...
"""

# 发送邮件
send_daily_brief_email(
    markdown_content=markdown_content,
    date=datetime.date(2026, 1, 21),
    recipients=["user@example.com"]
)

# DRY_RUN=1 输出
"""
DRY_RUN: Email not sent, saved to reports/2026-01-21_email.html
Subject: Daily Trading Brief - 2026-01-21
To: user@example.com
"""

# 实际发送成功输出
"""
Email sent successfully to user@example.com
Message-ID: <abc123@smtp.gmail.com>
"""

# HTML 渲染示例
"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>...</style>
</head>
<body>
  <h1>Daily Trading Brief - 2026-01-21</h1>
  <p><em>Generated at 2026-01-21 06:30:00 UTC</em></p>
  <hr>
  <h2>Executive Summary</h2>
  <p>今日市场呈现多点开花格局...</p>
  ...
</body>
</html>
"""
```

**测试要求：**

| 测试类型 | 覆盖场景 | 文件位置 |
|----------|----------|----------|
| Unit | Markdown → HTML 转换 | `tests/unit/test_email_renderer.py` |
| Unit | Markdown → 纯文本 Fallback | 同上 |
| Unit | 邮件结构构造 | 同上 |
| Unit | DRY_RUN 模式 | 同上 |
| Unit | 错误处理：转换失败、配置缺失 | 同上 |
| Integration | 完整邮件发送流程（mock SMTP） | `tests/integration/test_email_sending.py` |
| Integration | SMTP 重试逻辑 | 同上 |

- [ ] Unit tests 覆盖 HTML 渲染所有分支
- [ ] Unit tests 覆盖 DRY_RUN 模式
- [ ] Integration tests 使用 `smtplib.SMTP` mock
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] 手动测试：发送真实邮件到测试账户，验证 HTML 显示

---

#### US-016: Reports API - 简报查询与差分接口

**Description:** As a 前端, I need 查询历史简报的 API so that Reports 页面能展示简报归档。

**Acceptance Criteria:**

**功能验证：**
- [ ] 端点 1：`GET /api/reports` - 简报列表
  - Query 参数：
    | 参数 | 类型 | 默认值 | 说明 |
    |------|------|--------|------|
    | `start_date` | string | 30天前 | ISO date `YYYY-MM-DD` |
    | `end_date` | string | 今天 | ISO date `YYYY-MM-DD` |
    | `limit` | int | 30 | 1-100 |

  - Response schema：
    ```typescript
    interface ReportsListResponse {
      reports: ReportSummary[];
      total: number;
      date_range: { start: string; end: string; };
    }

    interface ReportSummary {
      date: string;                      // "2026-01-21"
      generation_method: string;         // "llm" | "template_*"
      total_events: number;
      trade_ideas_count: number;
      research_ideas_count: number;
      data_quality_status: string;
      file_path_md: string;              // 相对路径
      file_path_json: string;
      created_at: string;                // ISO timestamp
    }
    ```

- [ ] 端点 2：`GET /api/reports/{date}` - 单个简报详情
  - Path 参数：`date` (YYYY-MM-DD)
  - Response schema：
    ```typescript
    interface ReportDetailResponse {
      metadata: {
        date: string;
        generated_at: string;
        generation_method: string;
        tradz_version: string;
        llm_model: string | null;
      };
      content: {
        markdown: string;       // 完整 Markdown 文本
        html: string;           // 服务端渲染的 HTML（可选）
      };
      fact_table: FactTable;    // 原始 FactTable
      summary: { ... };
      performance: { ... };
    }
    ```

- [ ] 端点 3（P1）：`GET /api/reports/diff` - 报告差分
  - Query 参数：
    | 参数 | 类型 | 说明 |
    |------|------|------|
    | `date` | string | 要对比的日期 |
    | `baseline` | string | 基准日期（默认前一天） |

  - Response schema：
    ```typescript
    interface ReportDiffResponse {
      date: string;
      baseline: string;
      changes: {
        new_events: EventDiff[];        // 新增事件
        upgraded_events: EventDiff[];   // 分数提升 > 10
        downgraded_events: EventDiff[]; // 分数下降 > 10
        resolved_events: EventDiff[];   // 已解决
        disappeared_events: EventDiff[]; // 消失（不再 Active）
      };
      summary: {
        total_changes: number;
        net_attention_change: number;   // 综合关注度变化
      };
    }

    interface EventDiff {
      event_id: string;
      entity_symbol: string;
      title: string;
      old_score: number | null;
      new_score: number | null;
      change_reason: string;  // "new_observation" | "score_change" | "status_change"
    }
    ```

**边界条件：**
- [ ] `date` 日期无简报 → 404 错误，`{ error: "Report not found for date 2026-01-21" }`
- [ ] `start_date > end_date` → 400 错误
- [ ] `limit > 100` → 强制设为 100
- [ ] Markdown 文件不存在但数据库有记录 → 500 错误，`{ error: "Report file missing" }`

**错误处理：**
- [ ] 数据库查询失败 → 500 错误
- [ ] 文件读取失败 → 500 错误，返回元数据但 `content.markdown = null`
- [ ] Markdown → HTML 转换失败 → 跳过 HTML 字段，只返回 Markdown

**示例：**

```bash
# 请求 1: 列表
GET /api/reports?start_date=2026-01-01&end_date=2026-01-31&limit=10

# 响应 200
{
  "reports": [
    {
      "date": "2026-01-21",
      "generation_method": "llm",
      "total_events": 8,
      "trade_ideas_count": 2,
      "research_ideas_count": 3,
      "data_quality_status": "degraded",
      "file_path_md": "reports/2026-01-21.md",
      "file_path_json": "reports/2026-01-21.json",
      "created_at": "2026-01-21T06:30:00Z"
    },
    ...
  ],
  "total": 21,
  "date_range": { "start": "2026-01-01", "end": "2026-01-31" }
}

# 请求 2: 单个简报
GET /api/reports/2026-01-21

# 响应 200
{
  "metadata": { ... },
  "content": {
    "markdown": "# Daily Trading Brief - 2026-01-21\n\n...",
    "html": "<h1>Daily Trading Brief...</h1>"
  },
  "fact_table": { ... },
  "summary": { ... },
  "performance": { ... }
}

# 请求 3 (P1): 差分
GET /api/reports/diff?date=2026-01-21&baseline=2026-01-20

# 响应 200
{
  "date": "2026-01-21",
  "baseline": "2026-01-20",
  "changes": {
    "new_events": [
      {
        "event_id": "evt-010",
        "entity_symbol": "META",
        "title": "Zuckerberg 国会听证",
        "old_score": null,
        "new_score": 75,
        "change_reason": "new_observation"
      }
    ],
    "upgraded_events": [
      {
        "event_id": "evt-001",
        "entity_symbol": "NVDA",
        "title": "佩洛西买入 NVDA...",
        "old_score": 70,
        "new_score": 85,
        "change_reason": "score_change"
      }
    ],
    ...
  },
  "summary": {
    "total_changes": 5,
    "net_attention_change": +15
  }
}
```

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | 查询参数解析和验证 |
| Unit | 文件读取逻辑 |
| Unit | Markdown → HTML 转换 |
| Unit | 边界：无简报、文件缺失 |
| Integration | 完整 API 调用（mock DB + 文件系统） |
| Integration | 差分算法（P1） |

- [ ] Unit tests 覆盖所有端点
- [ ] Integration tests 使用 mock 文件系统
- [ ] 本 story 新增代码测试覆盖率 >= 90%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] API 文档更新（OpenAPI/Swagger）

---

#### US-017: Reports UI - 简报归档浏览器

**Description:** As a 研究者, I want 在 Reports 页面浏览历史简报 so that 我能回顾过去的分析和建议。

**Acceptance Criteria:**

**功能验证：**
- [ ] 页面结构：
  ```
  ┌─────────────────────────────────────────────────────────────┐
  │ Reports                                          [刷新按钮]   │
  ├─────────────────────────────────────────────────────────────┤
  │ 日期范围: [2026-01-01 ▼] 至 [2026-01-31 ▼]    [搜索]       │
  ├─────────────────────────────────────────────────────────────┤
  │ ┌─────────────────────────────────────────────────────────┐ │
  │ │ 📄 2026-01-21  LLM  8 events  2 trades  3 research    │ │
  │ │    Generated at 06:30 UTC                              │ │
  │ │    Status: degraded                        [查看详情]   │ │
  │ └─────────────────────────────────────────────────────────┘ │
  │ ┌─────────────────────────────────────────────────────────┐ │
  │ │ 📄 2026-01-20  Template  5 events  1 trade  2 research│ │
  │ │    Generated at 06:30 UTC                              │ │
  │ │    Status: healthy                         [查看详情]   │ │
  │ └─────────────────────────────────────────────────────────┘ │
  │ ...                                                         │
  └─────────────────────────────────────────────────────────────┘
  ```

- [ ] 列表项显示内容：
  | 元素 | 说明 |
  |------|------|
  | 日期 | YYYY-MM-DD |
  | 生成方式 | LLM / Template（颜色区分：绿色/黄色） |
  | 统计 | X events, X trades, X research |
  | 生成时间 | HH:MM UTC |
  | 数据质量状态 | healthy / degraded / unhealthy（颜色标识） |
  | 查看详情按钮 | 点击展开详情 |

- [ ] 点击 "查看详情" → 展开 Markdown 渲染器：
  ```
  ┌──────────────────────────────────────────────────────────────┐
  │ Daily Trading Brief - 2026-01-21                    [关闭 ×] │
  ├──────────────────────────────────────────────────────────────┤
  │ [Markdown 渲染内容]                                          │
  │                                                              │
  │ # Executive Summary                                          │
  │ 今日市场呈现...                                              │
  │                                                              │
  │ ## Top Events                                                │
  │ ...                                                          │
  ├──────────────────────────────────────────────────────────────┤
  │ [下载 MD]  [下载 JSON]  [发送邮件]                          │
  └──────────────────────────────────────────────────────────────┘
  ```

- [ ] Markdown 渲染器要求：
  - [ ] 使用 `react-markdown` 或类似库
  - [ ] 支持表格、列表、代码块
  - [ ] 链接可点击（如事件详情链接）
  - [ ] 样式与邮件 HTML 一致
  - [ ] 响应式布局

- [ ] 日期范围筛选：
  - [ ] 默认显示最近 30 天
  - [ ] 日期选择器支持快捷选项：最近 7 天 / 30 天 / 90 天 / 自定义
  - [ ] URL 同步：`?start=2026-01-01&end=2026-01-31`

- [ ] 下载功能：
  - [ ] 下载 MD：直接下载 `{date}.md` 文件
  - [ ] 下载 JSON：下载 `{date}.json` 文件

- [ ] 发送邮件（P2）：
  - [ ] 点击 "发送邮件" → 弹出对话框
  - [ ] 输入收件人邮箱
  - [ ] 调用 API 发送该简报

**状态处理：**
- [ ] Loading：显示 Skeleton 占位符
- [ ] Error：显示错误提示 + 重试按钮
- [ ] Empty（无简报）：
  ```
  ┌─────────────────────────────────────────┐
  │  📭 暂无简报                             │
  │  所选日期范围内没有生成简报              │
  │  [调整日期范围]                         │
  └─────────────────────────────────────────┘
  ```

**边界条件：**
- [ ] 简报数量 = 0 → 显示 Empty 状态
- [ ] Markdown 渲染失败 → 显示原始文本 + 警告
- [ ] 文件下载失败 → toast 错误提示

**性能要求：**
- [ ] 初始加载 < 1s（30 条记录）
- [ ] Markdown 渲染 < 500ms
- [ ] 列表虚拟滚动（当简报 > 50 条时）

**React 组件结构：**
```typescript
// pages/Reports.tsx
interface ReportsProps {}

// 状态
// - dateRange: { start: Date; end: Date; }
// - reports: ReportSummary[]
// - selectedReport: ReportDetail | null

// 子组件
// - ReportListItem: 单条简报摘要
// - ReportDetailModal: Markdown 渲染器 + 操作按钮
// - DateRangePicker: 日期范围选择器

// 使用的 hooks
// - useReports(dateRange) - TanStack Query
// - useReportDetail(date) - TanStack Query
```

**测试要求：**

| 测试类型 | 覆盖场景 |
|----------|----------|
| Unit | 日期范围筛选逻辑 |
| Unit | URL 状态同步 |
| Component | 列表渲染（mock data） |
| Component | Markdown 渲染器 |
| Component | 下载功能 |
| Component | Loading/Error/Empty 状态 |
| E2E | 完整用户流程（Playwright） |

- [ ] Component tests 覆盖所有 UI 状态
- [ ] Component tests 使用 MSW mock API
- [ ] Snapshot tests 防止 Markdown 渲染变化
- [ ] 本 story 新增代码测试覆盖率 >= 85%
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] Verify in browser：列表浏览、详情展开、下载、Markdown 渲染
- [ ] 无障碍：键盘导航、屏幕阅读器支持

---

### Epic 5: 事件状态机与持久化（P0）

#### US-018: Event 状态转换逻辑

**Description**: 实现事件状态机，定义 5 种状态（new, ongoing, resolved, dismissed, stale）及转换规则，支持用户手动操作（resolve, dismiss, snooze）和系统自动转换（stale detection）。

**Acceptance Criteria**:

##### 功能验证
- [ ] 定义 `EventStatus` 枚举：`new`, `ongoing`, `resolved`, `dismissed`, `stale`
- [ ] 实现 `EventStateMachine` 类，封装所有转换逻辑
- [ ] 支持用户触发的状态转换：
  - `resolve(event_id: str, resolution_note: str)` - 标记为已解决
  - `dismiss(event_id: str, reason: str)` - 忽略此事件
  - `snooze(event_id: str, hours: int)` - 延迟显示（默认 24h）
- [ ] 支持系统自动转换：
  - `new` → `ongoing`：当有新 Observation 加入时自动触发
  - `ongoing` → `stale`：72 小时无新 Observation 且未手动标记
  - `stale` → `ongoing`：stale 事件收到新 Observation 时自动恢复
- [ ] 所有状态转换记录到 `event_state_history` 表（event_id, old_status, new_status, trigger, timestamp, user_action）
- [ ] 支持 `unsnoozed_at` 字段：snooze 期间不显示在 Signal Inbox，到期后自动重新显示

##### 边界条件
- [ ] 不允许的转换会抛出 `InvalidStateTransition` 异常（如：`resolved` → `new`）
- [ ] `dismissed` 和 `resolved` 为终态，除非显式 reopen（手动操作）
- [ ] snooze 期间，事件仍在数据库中，但 `is_snoozed()` 返回 True
- [ ] stale 检测：计算最新 Observation 的 `observed_at`，与当前时间对比
- [ ] 72 小时阈值可配置（`config.yaml: events.stale_threshold_hours`）

##### 错误处理
- [ ] 无效状态转换 → 返回 400 错误，消息：`"Cannot transition from {old} to {new}"`
- [ ] Event 不存在 → 返回 404 错误
- [ ] Snooze 小时数 <= 0 → 返回 400 错误，消息：`"Snooze hours must be positive"`
- [ ] 数据库写入失败 → 返回 500 错误，记录到日志
- [ ] 状态历史记录失败 → 不影响状态转换，仅记录 warning 日志

##### 示例

**输入**（API 调用）:
```json
POST /api/events/evt_123/resolve
{
  "resolution_note": "Confirmed false alarm - volume spike was earnings-related"
}
```

**内部处理**（EventStateMachine）:
```python
class EventStateMachine:
    ALLOWED_TRANSITIONS = {
        "new": ["ongoing", "dismissed"],
        "ongoing": ["resolved", "dismissed", "stale"],
        "stale": ["ongoing", "resolved", "dismissed"],
        "resolved": [],  # 终态
        "dismissed": []  # 终态
    }

    def resolve(self, event_id: str, resolution_note: str):
        event = db.get_event(event_id)
        if event.status not in ["ongoing", "stale"]:
            raise InvalidStateTransition(f"Cannot resolve event in status {event.status}")

        # 1. 更新状态
        old_status = event.status
        event.status = "resolved"
        event.resolved_at = datetime.now()
        event.resolution_note = resolution_note

        # 2. 记录状态历史
        db.insert_state_history({
            "event_id": event_id,
            "old_status": old_status,
            "new_status": "resolved",
            "trigger": "user_action",
            "timestamp": datetime.now(),
            "metadata": {"resolution_note": resolution_note}
        })

        # 3. 持久化
        db.update_event(event)
```

**输出**（数据库变化）:
```
events 表：
event_id | status   | resolved_at         | resolution_note
evt_123  | resolved | 2026-01-21 10:00:00 | Confirmed false alarm...

event_state_history 表：
event_id | old_status | new_status | trigger      | timestamp
evt_123  | ongoing    | resolved   | user_action  | 2026-01-21 10:00:00
```

##### 测试要求
- [ ] 单元测试：所有允许的状态转换路径（≥15 个 case）
- [ ] 单元测试：所有不允许的转换抛出异常（≥10 个 case）
- [ ] 单元测试：snooze 逻辑（is_snoozed() 在到期前/后的返回值）
- [ ] 单元测试：stale detection（时间边界：71h59m → False, 72h1m → True）
- [ ] 集成测试：状态历史记录完整性
- [ ] 集成测试：并发状态转换（两个请求同时 resolve 同一 Event）
- [ ] E2E 测试：用户从 UI 执行 resolve/dismiss/snooze → 验证 DB + UI 刷新

---

#### US-019: Event 生命周期持久化

**Description**: 在 DuckDB 中实现事件生命周期的完整持久化，包括事件基础信息、状态历史、Observation 关联关系、用户操作元数据。

**Acceptance Criteria**:

##### 功能验证
- [ ] 创建 `events` 表，包含字段：
  ```sql
  CREATE TABLE events (
    event_id VARCHAR PRIMARY KEY,
    entity_id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,  -- price_move, news_catalyst, flow_signal, filing_alert
    status VARCHAR NOT NULL,       -- new, ongoing, resolved, dismissed, stale
    attention_score DOUBLE,        -- 综合分数 0-100
    anomaly_score DOUBLE,
    catalyst_score DOUBLE,
    flow_score DOUBLE,
    confidence_score DOUBLE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    snoozed_until TIMESTAMP,
    resolution_note TEXT,
    metadata JSON,                 -- 自定义字段（如 pinned, tags, user_notes）
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
  );
  ```

- [ ] 创建 `event_state_history` 表：
  ```sql
  CREATE TABLE event_state_history (
    history_id VARCHAR PRIMARY KEY,
    event_id VARCHAR NOT NULL,
    old_status VARCHAR NOT NULL,
    new_status VARCHAR NOT NULL,
    trigger VARCHAR NOT NULL,      -- user_action, system_auto, observation_added
    timestamp TIMESTAMP NOT NULL,
    user_action VARCHAR,           -- resolve, dismiss, snooze, reopen, null
    metadata JSON,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
  );
  ```

- [ ] 创建 `event_observations` 表（多对多关系）：
  ```sql
  CREATE TABLE event_observations (
    event_id VARCHAR NOT NULL,
    observation_id VARCHAR NOT NULL,
    added_at TIMESTAMP NOT NULL,
    relevance_score DOUBLE,        -- 0.0-1.0，来自 US-009a 的相关性算法
    PRIMARY KEY (event_id, observation_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (observation_id) REFERENCES observations(observation_id)
  );
  ```

- [ ] 实现 CRUD 操作：
  - `create_event(event: Event) -> str` - 返回 event_id
  - `get_event(event_id: str) -> Event | None`
  - `update_event(event: Event) -> bool`
  - `delete_event(event_id: str) -> bool` - 级联删除关联记录
  - `add_observation_to_event(event_id: str, obs_id: str, relevance: float)`
  - `remove_observation_from_event(event_id: str, obs_id: str)`

- [ ] 实现查询接口：
  - `get_active_events() -> List[Event]` - status in (new, ongoing)
  - `get_events_by_status(status: str) -> List[Event]`
  - `get_events_by_entity(entity_id: str) -> List[Event]`
  - `get_event_history(event_id: str) -> List[StateTransition]`
  - `get_snoozed_events() -> List[Event]` - snoozed_until > now

##### 边界条件
- [ ] 删除 Event 时，级联删除 `event_state_history` 和 `event_observations` 中的关联记录
- [ ] `event_observations.relevance_score` 允许 NULL（对于手动关联的 Observation）
- [ ] `events.metadata` 支持任意 JSON（如：`{"pinned": true, "tags": ["earnings"], "user_notes": "..."}`）
- [ ] 同一 Observation 不能重复添加到同一 Event（PRIMARY KEY 约束）
- [ ] `snoozed_until` 为 NULL 时表示未 snooze

##### 错误处理
- [ ] 创建 Event 时 entity_id 不存在 → 返回 400 错误，消息：`"Entity {entity_id} not found"`
- [ ] 更新不存在的 Event → 返回 404 错误
- [ ] 删除不存在的 Event → 返回 404 错误
- [ ] 添加不存在的 Observation → 返回 400 错误，消息：`"Observation {obs_id} not found"`
- [ ] 数据库约束冲突（如重复 event_id）→ 返回 409 错误
- [ ] 数据库连接失败 → 返回 503 错误，记录到日志并重试（最多 3 次）

##### 示例

**输入**（创建新事件）:
```python
event = Event(
    event_id="evt_456",
    entity_id="ent_AAPL",
    title="Unusual volume spike + SEC filing",
    event_type="flow_signal",
    status="new",
    attention_score=87.5,
    anomaly_score=75,
    catalyst_score=95,
    flow_score=90,
    confidence_score=80,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    metadata={"pinned": False, "tags": ["volume", "sec"]}
)

db.create_event(event)
db.add_observation_to_event("evt_456", "obs_789", relevance=0.95)
db.add_observation_to_event("evt_456", "obs_790", relevance=0.88)
```

**输出**（数据库记录）:
```
events 表：
event_id | entity_id | title                             | event_type  | status | attention_score
evt_456  | ent_AAPL  | Unusual volume spike + SEC filing | flow_signal | new    | 87.5

event_observations 表：
event_id | observation_id | added_at            | relevance_score
evt_456  | obs_789        | 2026-01-21 10:00:00 | 0.95
evt_456  | obs_790        | 2026-01-21 10:00:01 | 0.88

event_state_history 表：
history_id | event_id | old_status | new_status | trigger      | timestamp
hist_001   | evt_456  | null       | new        | system_auto  | 2026-01-21 10:00:00
```

**查询示例**:
```python
# 获取所有活跃事件
active_events = db.get_active_events()
# 返回：[Event(evt_456, status=new), Event(evt_123, status=ongoing), ...]

# 获取事件的完整历史
history = db.get_event_history("evt_456")
# 返回：[StateTransition(old=null, new=new, trigger=system_auto, timestamp=...)]
```

##### 测试要求
- [ ] 单元测试：所有 CRUD 操作（create, get, update, delete）
- [ ] 单元测试：所有查询接口（get_active_events, get_events_by_status, etc.）
- [ ] 单元测试：级联删除逻辑（删除 Event → 验证关联记录也被删除）
- [ ] 单元测试：边界条件（重复添加 Observation, entity_id 不存在, etc.）
- [ ] 集成测试：完整事件生命周期（create → add observations → update status → resolve → query history）
- [ ] 集成测试：并发写入（两个线程同时创建 Event）
- [ ] 集成测试：数据完整性（外键约束验证）
- [ ] 性能测试：查询 1000+ 事件的响应时间 < 100ms
- [ ] E2E 测试：从 UI 创建事件 → 验证 DB 持久化 → 刷新页面后数据仍存在

---

### Epic 6: Compare Yesterday（P1）

#### US-020: Daily Brief Diff 算法

**Description**: 实现 Daily Brief 内容对比算法，检测两个 Brief 之间的差异（新增事件、状态变化、建议更新），生成结构化的 diff 结果供 UI 展示。

**Acceptance Criteria**:

##### 功能验证
- [ ] 实现 `DailyBriefDiffer` 类，支持两个 `DailyBriefJSON` 对象的对比
- [ ] 检测 **事件层面的变化**：
  - `added_events`: 今日新增的事件（event_id 在今日存在，昨日不存在）
  - `removed_events`: 昨日消失的事件（event_id 在昨日存在，今日不存在 或 状态变为 resolved/dismissed）
  - `continuing_events`: 持续中的事件（event_id 在两日均存在且状态为 active）
  - `status_changed_events`: 状态发生变化的事件（如 new → ongoing, ongoing → stale）

- [ ] 检测 **事件内部的变化**（针对 continuing_events）：
  - `score_changes`: attention_score 变化幅度（记录昨日分数、今日分数、变化百分比）
  - `new_observations`: 新增的 Observation（对比 observation_ids）
  - `evidence_strength_change`: 证据强度变化（Observation 数量变化、最高相关性变化）

- [ ] 检测 **Trade Ideas 的变化**：
  - `new_trade_ideas`: 今日新增的 Trade Idea（entity_symbol + recommendation）
  - `updated_trade_ideas`: 已有 Trade Idea 的更新（如入场区间变化、失效条件更新）
  - `closed_trade_ideas`: 昨日有、今日无（可能已执行或失效）

- [ ] 检测 **Research Ideas 的变化**：
  - `new_research_ideas`: 今日新增的 Research Plan
  - `resolved_research_ideas`: 昨日的 Research Plan 今日转为 Trade Idea（说明研究完成）

- [ ] 生成 **Diff Summary**：
  ```python
  {
    "comparison_date_range": {"from": "2026-01-20", "to": "2026-01-21"},
    "overall_changes": {
      "total_events_yesterday": 12,
      "total_events_today": 15,
      "net_change": +3,
      "new_events_count": 5,
      "resolved_count": 2,
      "continuing_count": 10
    },
    "events": {
      "added": [...],      # Event 对象列表
      "removed": [...],
      "continuing": [...],
      "status_changed": [...]
    },
    "trade_ideas": {
      "new": [...],
      "updated": [...],
      "closed": [...]
    },
    "research_ideas": {
      "new": [...],
      "resolved": [...]
    },
    "highlights": [
      "AAPL attention_score +15% (from 72 to 87)",
      "New high-confidence trade idea: TSLA Long",
      "NVDA research plan resolved → Trade Idea generated"
    ]
  }
  ```

##### 边界条件
- [ ] 如果昨日没有 Brief（首次运行）→ 返回所有事件为 `added_events`，highlights 为空
- [ ] 如果今日 Brief 为空（系统故障）→ 返回错误，不生成 diff
- [ ] Score 变化小于 5% → 不计入 highlights（避免噪音）
- [ ] Trade Idea 的 `updated` 判断：同一 entity_symbol + recommendation，但 entry_range/invalidation/rationale 有变化
- [ ] Research Idea 的 `resolved` 判断：昨日在 research_ideas，今日在 trade_ideas，且 entity_symbol 相同

##### 错误处理
- [ ] 昨日 Brief 文件不存在 → 返回 404 错误，消息：`"No brief available for {yesterday_date}"`
- [ ] JSON 解析失败 → 返回 500 错误，消息：`"Failed to parse brief JSON"`
- [ ] Event ID 在数据库中不存在（数据不一致）→ 记录 warning，跳过该事件
- [ ] 日期参数无效（如 from > to）→ 返回 400 错误，消息：`"Invalid date range"`

##### 示例

**输入**（两个 DailyBriefJSON）:
```python
# 昨日（2026-01-20）
yesterday_brief = {
  "summary": {"total_events": 12, "trade_ideas_count": 3, ...},
  "content": {
    "fact_table": {
      "top_events": [
        {"event_id": "evt_123", "entity_symbol": "AAPL", "attention_score": 72, ...},
        {"event_id": "evt_124", "entity_symbol": "TSLA", "attention_score": 65, ...}
      ],
      "trade_ideas": [
        {"entity_symbol": "NVDA", "recommendation": "Long", "entry_range": "800-820", ...}
      ],
      "research_ideas": [
        {"entity_symbol": "MSFT", "questions": ["Verify Azure revenue growth"], ...}
      ]
    }
  }
}

# 今日（2026-01-21）
today_brief = {
  "summary": {"total_events": 15, "trade_ideas_count": 4, ...},
  "content": {
    "fact_table": {
      "top_events": [
        {"event_id": "evt_123", "entity_symbol": "AAPL", "attention_score": 87, ...},  # 分数提升
        {"event_id": "evt_125", "entity_symbol": "AMZN", "attention_score": 78, ...},  # 新增
        {"event_id": "evt_124", "entity_symbol": "TSLA", "attention_score": 65, ...}   # 无变化
      ],
      "trade_ideas": [
        {"entity_symbol": "NVDA", "recommendation": "Long", "entry_range": "780-800", ...},  # 入场区间更新
        {"entity_symbol": "MSFT", "recommendation": "Long", "entry_range": "400-410", ...}   # 从 Research 转为 Trade
      ],
      "research_ideas": []
    }
  }
}
```

**输出**（DiffResult）:
```python
{
  "comparison_date_range": {"from": "2026-01-20", "to": "2026-01-21"},
  "overall_changes": {
    "total_events_yesterday": 12,
    "total_events_today": 15,
    "net_change": +3,
    "new_events_count": 3,
    "resolved_count": 0,
    "continuing_count": 12
  },
  "events": {
    "added": [
      {"event_id": "evt_125", "entity_symbol": "AMZN", "attention_score": 78, ...}
    ],
    "removed": [],
    "continuing": [
      {"event_id": "evt_123", "entity_symbol": "AAPL", "score_change": +15, "yesterday": 72, "today": 87},
      {"event_id": "evt_124", "entity_symbol": "TSLA", "score_change": 0, "yesterday": 65, "today": 65}
    ],
    "status_changed": []
  },
  "trade_ideas": {
    "new": [],
    "updated": [
      {
        "entity_symbol": "NVDA",
        "recommendation": "Long",
        "changes": {"entry_range": {"from": "800-820", "to": "780-800"}}
      }
    ],
    "closed": []
  },
  "research_ideas": {
    "new": [],
    "resolved": [
      {
        "entity_symbol": "MSFT",
        "yesterday_status": "research",
        "today_status": "trade_idea",
        "note": "Research completed → Trade Idea generated"
      }
    ]
  },
  "highlights": [
    "AAPL attention_score +20.8% (from 72 to 87)",
    "NVDA trade idea updated: entry_range 800-820 → 780-800",
    "MSFT research plan resolved → Trade Idea generated"
  ]
}
```

##### 测试要求
- [ ] 单元测试：新增事件检测（≥5 个 case）
- [ ] 单元测试：删除/解决事件检测（≥5 个 case）
- [ ] 单元测试：分数变化检测（边界：±4.9%, ±5.0%, ±10%）
- [ ] 单元测试：Trade Idea 更新检测（entry_range, invalidation, rationale 变化）
- [ ] 单元测试：Research Idea → Trade Idea 转换检测
- [ ] 单元测试：首次运行（昨日无 Brief）
- [ ] 集成测试：完整 diff 流程（读取两个 JSON → 生成 diff → 验证所有字段）
- [ ] 性能测试：对比两个 100+ 事件的 Brief，耗时 < 200ms

---

#### US-021: Compare Yesterday UI 组件

**Description**: 在 Reports 页面实现 "Compare Yesterday" 视图，可视化展示 Daily Brief 的逐日变化，包括事件变化、分数趋势、建议更新。

**Acceptance Criteria**:

##### 功能验证
- [ ] 在 Reports 页面添加 **"Compare" 标签页**（与 "Archive" 并列）
- [ ] 默认展示 **今日 vs. 昨日** 的对比（自动选择最近两个 Brief）
- [ ] 支持 **自定义日期选择**：
  - 两个日期选择器（From Date, To Date）
  - 验证：To Date 必须晚于 From Date
  - 最大跨度：7 天（防止性能问题）
  - 点击 "Compare" 按钮触发 diff 计算

- [ ] **总览卡片**（Overview Cards）：
  ```tsx
  <div className="grid grid-cols-4 gap-4">
    <StatCard label="Total Events" yesterday={12} today={15} change={+3} />
    <StatCard label="Trade Ideas" yesterday={3} today={4} change={+1} />
    <StatCard label="New Events" value={5} highlight />
    <StatCard label="Resolved" value={2} />
  </div>
  ```

- [ ] **Highlights 面板**（自动生成的关键变化）：
  - 显示 diff.highlights 数组（最多 10 条）
  - 高亮显示分数变化 >10% 的事件
  - 高亮显示新增的 Trade Idea
  - 排序：按重要性（Trade Idea > 大幅分数变化 > 新增事件）

- [ ] **事件变化列表**（Event Changes）：
  - **三个分组 Tab**：New Events / Continuing Events / Resolved Events
  - **New Events Tab**：
    - 展示 diff.events.added 列表
    - 每个事件显示：entity_symbol, title, attention_score, event_type, 首次出现时间
    - 点击跳转到 Event Detail 页面
  - **Continuing Events Tab**：
    - 展示 diff.events.continuing 列表
    - 每个事件显示：
      - entity_symbol, title
      - 分数变化：`72 → 87 (+20.8%)` 带颜色（绿色=上升，红色=下降）
      - 新增证据数量：`+3 new observations`
      - 状态变化（如有）：`new → ongoing`
    - 支持按分数变化幅度排序（默认降序）
  - **Resolved Events Tab**：
    - 展示 diff.events.removed 列表
    - 显示解决原因（resolution_note）或 dismiss 原因

- [ ] **Trade Ideas 变化面板**：
  - **三列布局**：New | Updated | Closed
  - **New 列**：展示新增 Trade Idea，高亮显示
  - **Updated 列**：
    - 显示 entity_symbol + recommendation
    - 展示变化内容（如：`Entry Range: 800-820 → 780-800`）
    - 使用 diff 样式（删除线 + 高亮）
  - **Closed 列**：展示昨日有、今日无的 Trade Idea

- [ ] **Research Ideas 变化面板**：
  - 展示 Research Plan 的状态变化
  - 高亮显示 resolved（研究完成并转为 Trade Idea）
  - 显示新增的 Research Plan

##### 边界条件
- [ ] 如果选择的日期没有 Brief → 显示空状态：`"No brief available for {date}"`
- [ ] 如果两个 Brief 相同（用户选择同一天）→ 显示警告：`"Please select different dates"`
- [ ] 如果是首次运行（昨日无 Brief）→ 显示提示：`"This is the first brief. No comparison available."`
- [ ] 分数变化 < 1% → 显示为 "No significant change"
- [ ] 超过 50 个事件变化 → 分页显示（每页 20 个）

##### 错误处理
- [ ] API 返回 404（Brief 不存在）→ 显示友好错误：`"Brief not found for {date}. Please select another date."`
- [ ] API 返回 500（diff 计算失败）→ 显示错误：`"Failed to compare briefs. Please try again."`
- [ ] 日期选择器输入无效 → 客户端验证，禁用 "Compare" 按钮
- [ ] 网络超时 → 显示加载指示器，超过 10 秒后显示重试按钮

##### 示例

**UI 布局**：
```tsx
<div className="compare-page">
  {/* 日期选择器 */}
  <div className="date-selector flex gap-4 mb-6">
    <DatePicker label="From Date" value={yesterday} onChange={setFrom} />
    <DatePicker label="To Date" value={today} onChange={setTo} />
    <Button onClick={handleCompare}>Compare</Button>
  </div>

  {/* 总览卡片 */}
  <div className="overview-cards grid grid-cols-4 gap-4 mb-6">
    <StatCard
      label="Total Events"
      yesterday={12}
      today={15}
      change={+3}
      changePercent={25}
    />
    {/* ... 其他卡片 */}
  </div>

  {/* Highlights */}
  <div className="highlights bg-yellow-50 p-4 rounded mb-6">
    <h3 className="font-bold mb-2">Key Changes</h3>
    <ul className="space-y-1">
      <li>AAPL attention_score +20.8% (from 72 to 87)</li>
      <li>New trade idea: MSFT Long (400-410)</li>
      <li>NVDA research plan resolved</li>
    </ul>
  </div>

  {/* 事件变化 */}
  <Tabs defaultValue="continuing">
    <TabsList>
      <TabsTrigger value="new">New Events (5)</TabsTrigger>
      <TabsTrigger value="continuing">Continuing (10)</TabsTrigger>
      <TabsTrigger value="resolved">Resolved (2)</TabsTrigger>
    </TabsList>

    <TabsContent value="continuing">
      <Table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Title</th>
            <th>Score Change</th>
            <th>New Evidence</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>AAPL</td>
            <td>Unusual volume spike</td>
            <td className="text-green-600">72 → 87 (+20.8%)</td>
            <td>+2 observations</td>
          </tr>
          {/* ... */}
        </tbody>
      </Table>
    </TabsContent>
  </Tabs>

  {/* Trade Ideas 变化 */}
  <div className="trade-ideas-changes grid grid-cols-3 gap-4 mt-6">
    <div className="new">
      <h4 className="font-bold mb-2">New Trade Ideas</h4>
      {/* ... */}
    </div>
    <div className="updated">
      <h4 className="font-bold mb-2">Updated</h4>
      <div className="idea-card">
        <div className="symbol">NVDA Long</div>
        <div className="change">
          Entry Range:
          <span className="line-through text-gray-400">800-820</span>
          <span className="text-green-600 font-bold">780-800</span>
        </div>
      </div>
    </div>
    <div className="closed">
      <h4 className="font-bold mb-2">Closed</h4>
      {/* ... */}
    </div>
  </div>
</div>
```

**API 调用**：
```typescript
// GET /api/reports/compare?from=2026-01-20&to=2026-01-21
const { data: diffResult } = useQuery({
  queryKey: ['reports', 'compare', fromDate, toDate],
  queryFn: () => api.get('/api/reports/compare', {
    params: { from: fromDate, to: toDate }
  }),
  enabled: fromDate && toDate && fromDate < toDate
});
```

##### 测试要求
- [ ] 单元测试：StatCard 组件（正负变化、百分比计算）
- [ ] 单元测试：事件列表渲染（新增、持续、已解决）
- [ ] 单元测试：Trade Idea diff 样式（删除线 + 高亮）
- [ ] 单元测试：日期选择器验证逻辑
- [ ] 集成测试：完整 Compare 流程（选择日期 → API 调用 → UI 渲染）
- [ ] 集成测试：边界条件（首次运行、同一天、Brief 不存在）
- [ ] E2E 测试：用户从 Reports 页面打开 Compare → 选择日期 → 查看结果 → 点击事件跳转
- [ ] 视觉回归测试：Compare 页面截图对比（使用 Playwright）

---

### Epic 7: Open Loops（P1）

#### US-022: Open Loop 定义与生成逻辑

**Description**: 定义 Open Loop 的数据模型和生成规则，自动从 Research Ideas 和未验证的 Trade Ideas 中提取"待办事项"，帮助用户追踪需要后续验证的信息。

**Acceptance Criteria**:

##### 功能验证
- [ ] 定义 `OpenLoop` 数据模型：
  ```python
  @dataclass
  class OpenLoop:
      loop_id: str                    # 唯一标识
      entity_id: str                  # 关联实体
      entity_symbol: str              # 显示用 ticker
      source_type: str                # research_idea | trade_idea | event_observation
      source_id: str                  # 来源 ID（research_id, trade_id, observation_id）
      question: str                   # 待验证的问题
      context: str                    # 背景信息
      priority: str                   # high | medium | low
      status: str                     # open | in_progress | resolved | dismissed
      created_at: datetime
      due_date: Optional[datetime]    # 可选截止日期
      resolution: Optional[str]       # 解决说明
      resolved_at: Optional[datetime]
  ```

- [ ] 实现 **Research Idea → Open Loop 转换**：
  - 每个 Research Idea 的 `questions` 字段中的每个问题 → 生成一个 Open Loop
  - `source_type = "research_idea"`
  - `priority` 基于 Research Idea 的 confidence_gap（gap 越大，priority 越高）
  - `context` 来自 Research Idea 的 `summary`

- [ ] 实现 **Trade Idea → Open Loop 转换**：
  - 从 Trade Idea 的 `invalidation` 条件生成 Open Loop（验证失效条件是否触发）
  - `source_type = "trade_idea"`
  - `question` 格式：`"Monitor: {invalidation_condition}"`
  - `priority = "high"`（Trade Idea 的失效条件需要密切关注）

- [ ] 实现 **Event Observation → Open Loop 转换**（可选）：
  - 某些 Observation 带有 `requires_followup` 标记 → 生成 Open Loop
  - `source_type = "event_observation"`
  - `priority` 基于 Observation 的 relevance_score

- [ ] 实现 `OpenLoopGenerator` 类：
  ```python
  class OpenLoopGenerator:
      def generate_from_daily_brief(self, brief: DailyBriefJSON) -> List[OpenLoop]:
          """从 Daily Brief 的 FactTable 生成 Open Loops"""
          loops = []

          # 1. 从 Research Ideas 生成
          for research in brief.fact_table.research_ideas:
              for question in research.questions:
                  loops.append(self._create_research_loop(research, question))

          # 2. 从 Trade Ideas 的失效条件生成
          for trade in brief.fact_table.trade_ideas:
              if trade.invalidation:
                  loops.append(self._create_invalidation_loop(trade))

          return loops

      def merge_with_existing(self, new_loops: List[OpenLoop], existing: List[OpenLoop]) -> List[OpenLoop]:
          """智能合并：避免重复，更新状态"""
          # 基于 entity_id + question 的模糊匹配判断重复
          pass
  ```

- [ ] 实现 **去重和合并逻辑**：
  - 相同 entity_id + 相似 question（余弦相似度 > 0.85）→ 视为重复
  - 已存在的 Open Loop 不重复生成
  - 如果 Research Plan 转为 Trade Idea → 自动 resolve 相关 Open Loops

##### 边界条件
- [ ] Research Idea 没有 questions 字段 → 跳过，不生成 Open Loop
- [ ] Trade Idea 没有 invalidation 字段 → 跳过，不生成 Open Loop
- [ ] Question 长度 > 500 字符 → 截断并添加 "..."
- [ ] 单个 Daily Brief 最多生成 50 个新 Open Loops（防止爆炸）
- [ ] 相似度计算失败 → 降级为精确匹配

##### 错误处理
- [ ] FactTable 解析失败 → 返回空列表，记录 error 日志
- [ ] 数据库写入失败 → 返回 500 错误，记录日志，不影响 Daily Brief 生成
- [ ] 相似度计算超时（> 1s）→ 使用精确匹配降级
- [ ] entity_id 不存在 → 跳过该 Open Loop，记录 warning

##### 示例

**输入**（DailyBriefJSON 片段）:
```python
fact_table = {
  "research_ideas": [
    {
      "entity_symbol": "MSFT",
      "summary": "Azure revenue growth needs verification",
      "questions": [
        "What was Azure's Q4 revenue growth rate?",
        "How does this compare to AWS and GCP?"
      ],
      "confidence_gap": 0.35  # 较大，priority = high
    }
  ],
  "trade_ideas": [
    {
      "entity_symbol": "NVDA",
      "recommendation": "Long",
      "entry_range": "780-800",
      "invalidation": "Price closes below $750 for 2 consecutive days"
    }
  ]
}
```

**输出**（生成的 Open Loops）:
```python
[
  OpenLoop(
    loop_id="loop_001",
    entity_id="ent_MSFT",
    entity_symbol="MSFT",
    source_type="research_idea",
    source_id="research_msft_001",
    question="What was Azure's Q4 revenue growth rate?",
    context="Azure revenue growth needs verification",
    priority="high",  # confidence_gap > 0.3
    status="open",
    created_at=datetime(2026, 1, 21, 8, 0, 0),
    due_date=None,
    resolution=None,
    resolved_at=None
  ),
  OpenLoop(
    loop_id="loop_002",
    entity_id="ent_MSFT",
    entity_symbol="MSFT",
    source_type="research_idea",
    source_id="research_msft_001",
    question="How does this compare to AWS and GCP?",
    context="Azure revenue growth needs verification",
    priority="high",
    status="open",
    ...
  ),
  OpenLoop(
    loop_id="loop_003",
    entity_id="ent_NVDA",
    entity_symbol="NVDA",
    source_type="trade_idea",
    source_id="trade_nvda_001",
    question="Monitor: Price closes below $750 for 2 consecutive days",
    context="Trade Idea invalidation condition for NVDA Long",
    priority="high",  # Trade Idea 失效条件始终是 high
    status="open",
    ...
  )
]
```

##### 测试要求
- [ ] 单元测试：Research Idea → Open Loop 转换（单问题、多问题、无问题）
- [ ] 单元测试：Trade Idea → Open Loop 转换（有 invalidation、无 invalidation）
- [ ] 单元测试：priority 计算逻辑（confidence_gap 阈值：0.2, 0.3, 0.5）
- [ ] 单元测试：去重逻辑（精确匹配、相似度匹配）
- [ ] 单元测试：最大数量限制（> 50 个时截断）
- [ ] 集成测试：完整流程（Daily Brief → 生成 Open Loops → 持久化）
- [ ] 集成测试：合并逻辑（新 Brief 不重复生成已有 Open Loops）

---

#### US-023: Open Loop 持久化与状态管理

**Description**: 在 DuckDB 中实现 Open Loop 的持久化，支持状态更新（open → in_progress → resolved）、查询过滤、与 Event/Entity 的关联。

**Acceptance Criteria**:

##### 功能验证
- [ ] 创建 `open_loops` 表：
  ```sql
  CREATE TABLE open_loops (
    loop_id VARCHAR PRIMARY KEY,
    entity_id VARCHAR NOT NULL,
    entity_symbol VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,    -- research_idea | trade_idea | event_observation
    source_id VARCHAR NOT NULL,
    question TEXT NOT NULL,
    context TEXT,
    priority VARCHAR NOT NULL,       -- high | medium | low
    status VARCHAR NOT NULL,         -- open | in_progress | resolved | dismissed
    created_at TIMESTAMP NOT NULL,
    due_date TIMESTAMP,
    resolution TEXT,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR,             -- system_auto | user_manual
    metadata JSON,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
  );

  CREATE INDEX idx_open_loops_status ON open_loops(status);
  CREATE INDEX idx_open_loops_entity ON open_loops(entity_id);
  CREATE INDEX idx_open_loops_priority ON open_loops(priority);
  ```

- [ ] 实现 CRUD 操作：
  - `create_open_loop(loop: OpenLoop) -> str` - 返回 loop_id
  - `get_open_loop(loop_id: str) -> OpenLoop | None`
  - `update_open_loop(loop: OpenLoop) -> bool`
  - `delete_open_loop(loop_id: str) -> bool`
  - `bulk_create_open_loops(loops: List[OpenLoop]) -> List[str]` - 批量创建

- [ ] 实现查询接口：
  - `get_open_loops(status: Optional[str] = None, entity_id: Optional[str] = None, priority: Optional[str] = None) -> List[OpenLoop]`
  - `get_open_loops_by_source(source_type: str, source_id: str) -> List[OpenLoop]`
  - `get_overdue_loops() -> List[OpenLoop]` - due_date < now AND status = open
  - `count_by_status() -> Dict[str, int]` - 各状态的数量统计

- [ ] 实现状态转换方法：
  - `start_loop(loop_id: str) -> bool` - open → in_progress
  - `resolve_loop(loop_id: str, resolution: str, resolved_by: str = "user_manual") -> bool`
  - `dismiss_loop(loop_id: str, reason: str) -> bool`
  - `reopen_loop(loop_id: str) -> bool` - resolved/dismissed → open

- [ ] 实现 **系统自动解决**：
  - 当 Research Plan 转为 Trade Idea 时，自动 resolve 相关 Open Loops
  - `resolved_by = "system_auto"`
  - `resolution = "Research completed - Trade Idea generated"`

##### 边界条件
- [ ] 删除 Entity 时，级联删除相关 Open Loops
- [ ] 重复创建（相同 entity_id + question）→ 返回已存在的 loop_id，不创建新记录
- [ ] resolved/dismissed 状态的 Loop 不能直接转为 in_progress（需要先 reopen）
- [ ] due_date 为 NULL 时表示无截止日期
- [ ] bulk_create 中部分失败 → 回滚全部，返回错误

##### 错误处理
- [ ] 无效状态转换 → 返回 400 错误，消息：`"Cannot transition from {old} to {new}"`
- [ ] Loop 不存在 → 返回 404 错误
- [ ] 数据库约束冲突 → 返回 409 错误
- [ ] 批量创建部分失败 → 返回 500 错误，记录失败的 loop_id

##### 示例

**输入**（状态更新）:
```python
# 用户开始处理某个 Open Loop
db.start_loop("loop_001")

# 用户解决了问题
db.resolve_loop(
    loop_id="loop_001",
    resolution="Verified: Azure Q4 revenue growth was 29%, above expectations",
    resolved_by="user_manual"
)
```

**输出**（数据库状态）:
```
open_loops 表：
loop_id  | status   | resolution                                           | resolved_at         | resolved_by
loop_001 | resolved | Verified: Azure Q4 revenue growth was 29%, above... | 2026-01-21 14:30:00 | user_manual
```

**查询示例**:
```python
# 获取所有 open 状态的高优先级 Loop
high_priority_open = db.get_open_loops(status="open", priority="high")

# 获取某个 Entity 的所有 Open Loops
msft_loops = db.get_open_loops(entity_id="ent_MSFT")

# 获取逾期的 Open Loops
overdue = db.get_overdue_loops()
```

##### 测试要求
- [ ] 单元测试：所有 CRUD 操作
- [ ] 单元测试：所有状态转换路径（open → in_progress → resolved）
- [ ] 单元测试：所有查询接口（按状态、实体、优先级过滤）
- [ ] 单元测试：overdue 检测逻辑（边界：due_date = now - 1s, now + 1s）
- [ ] 单元测试：批量创建（成功、部分失败、全部失败）
- [ ] 集成测试：完整生命周期（create → start → resolve → query history）
- [ ] 集成测试：系统自动解决（Research → Trade Idea 触发）
- [ ] 性能测试：查询 1000+ Open Loops，响应时间 < 100ms

---

#### US-024: Open Loop UI 组件

**Description**: 在 Dashboard 和 Event Detail 页面实现 Open Loop 的展示和管理界面，支持查看、过滤、状态更新、与事件关联。

**Acceptance Criteria**:

##### 功能验证
- [ ] **Dashboard 集成**（Signal Inbox 旁边）：
  - 添加 "Open Loops" 小组件，显示未解决的 Loop 数量
  - 按 priority 分组显示：High (红色徽章), Medium (黄色), Low (灰色)
  - 点击展开查看详细列表
  - 支持快速操作：Mark as In Progress, Resolve, Dismiss

- [ ] **Event Detail 集成**：
  - 在 Event Detail 页面添加 "Related Open Loops" 区块
  - 显示与当前 Event 关联的 Entity 的所有 Open Loops
  - 支持从 Event Detail 直接创建新的 Open Loop（手动添加）

- [ ] **Open Loops 独立页面**（可选，作为 Dashboard 子页面）：
  - 完整列表视图，支持分页（每页 20 条）
  - **过滤器**：
    - Status: All | Open | In Progress | Resolved | Dismissed
    - Priority: All | High | Medium | Low
    - Entity: 下拉选择或搜索
    - Source Type: All | Research Idea | Trade Idea | Observation
    - Date Range: 创建时间范围
  - **排序**：
    - 默认：Priority (High → Low), 然后 Created At (Newest First)
    - 可切换：Due Date (Soonest First), Entity (A-Z)

- [ ] **Open Loop 卡片组件**：
  ```tsx
  <OpenLoopCard
    loop={loop}
    onStart={() => handleStart(loop.loop_id)}
    onResolve={(resolution) => handleResolve(loop.loop_id, resolution)}
    onDismiss={(reason) => handleDismiss(loop.loop_id, reason)}
  >
    <div className="flex items-center gap-2">
      <PriorityBadge priority={loop.priority} />
      <span className="font-bold">{loop.entity_symbol}</span>
    </div>
    <p className="text-sm mt-1">{loop.question}</p>
    <p className="text-xs text-gray-500 mt-1">{loop.context}</p>
    <div className="flex gap-2 mt-2">
      <StatusBadge status={loop.status} />
      {loop.due_date && <DueDateBadge date={loop.due_date} />}
    </div>
  </OpenLoopCard>
  ```

- [ ] **解决对话框**：
  - 点击 "Resolve" 弹出对话框
  - 文本输入框：Resolution（必填，最少 10 字符）
  - 确认按钮：Resolve
  - 取消按钮：Cancel

- [ ] **Dismiss 对话框**：
  - 点击 "Dismiss" 弹出对话框
  - 文本输入框：Reason（可选）
  - 常用原因快捷按钮：No longer relevant, Duplicate, Low priority
  - 确认按钮：Dismiss

- [ ] **手动创建 Open Loop**：
  - 在 Event Detail 页面，点击 "Add Open Loop" 按钮
  - 表单字段：
    - Question（必填）
    - Context（可选）
    - Priority（下拉：High/Medium/Low，默认 Medium）
    - Due Date（可选日期选择器）
  - 自动关联当前 Event 的 Entity

##### 边界条件
- [ ] 没有 Open Loops → 显示空状态：`"No open loops. All caught up!"`
- [ ] 列表超过 100 条 → 强制分页，显示 "Load More" 按钮
- [ ] Resolution 输入少于 10 字符 → 禁用 Resolve 按钮，显示提示
- [ ] 已 resolved 的 Loop → 显示 resolution 和 resolved_at，隐藏操作按钮
- [ ] Overdue Loop → 高亮显示（红色边框），due_date 显示为红色

##### 错误处理
- [ ] API 返回 404 → 显示 "Loop not found"，刷新列表
- [ ] API 返回 400（无效状态转换）→ 显示错误消息，不更新 UI
- [ ] 网络错误 → 显示 "Failed to update. Please try again."，保留原状态
- [ ] 乐观更新失败 → 回滚 UI 状态，显示错误提示

##### 示例

**Dashboard Open Loops Widget**:
```tsx
<div className="open-loops-widget bg-white rounded-lg shadow p-4">
  <div className="flex justify-between items-center mb-4">
    <h3 className="font-bold">Open Loops</h3>
    <span className="text-2xl font-bold text-orange-500">12</span>
  </div>

  <div className="priority-breakdown flex gap-2 mb-4">
    <Badge variant="destructive">High: 3</Badge>
    <Badge variant="warning">Medium: 7</Badge>
    <Badge variant="secondary">Low: 2</Badge>
  </div>

  <div className="top-loops space-y-2">
    {topLoops.slice(0, 3).map(loop => (
      <OpenLoopCard key={loop.loop_id} loop={loop} compact />
    ))}
  </div>

  <Button variant="ghost" className="w-full mt-2">
    View All Open Loops →
  </Button>
</div>
```

**Event Detail - Related Open Loops**:
```tsx
<div className="related-loops mt-6">
  <div className="flex justify-between items-center mb-4">
    <h4 className="font-bold">Related Open Loops for {entity.symbol}</h4>
    <Button size="sm" onClick={openCreateDialog}>
      + Add Loop
    </Button>
  </div>

  {relatedLoops.length === 0 ? (
    <p className="text-gray-500">No open loops for this entity.</p>
  ) : (
    <div className="space-y-2">
      {relatedLoops.map(loop => (
        <OpenLoopCard key={loop.loop_id} loop={loop} />
      ))}
    </div>
  )}
</div>
```

##### 测试要求
- [ ] 单元测试：OpenLoopCard 组件（各状态、各优先级渲染）
- [ ] 单元测试：PriorityBadge、StatusBadge、DueDateBadge 组件
- [ ] 单元测试：过滤器逻辑（多条件组合）
- [ ] 单元测试：排序逻辑（Priority + Created At 复合排序）
- [ ] 单元测试：Resolve/Dismiss 对话框（验证逻辑、提交逻辑）
- [ ] 集成测试：完整流程（查看列表 → 过滤 → 操作 → 验证 API 调用）
- [ ] 集成测试：乐观更新和回滚
- [ ] E2E 测试：从 Dashboard 进入 Open Loops → 过滤 → Resolve → 验证状态更新
- [ ] E2E 测试：从 Event Detail 创建新 Open Loop → 验证显示在列表中
- [ ] 视觉回归测试：Open Loop 卡片各状态截图

---

### Epic 8: 建议质量门控（P1）

#### US-025: Trade Idea 质量门控引擎

**Description**: 实现可配置的质量门控系统，定义 Trade Idea 输出的前置条件（evidence threshold, confidence level, source diversity），确保只有高质量的建议才能成为可执行的 Trade Idea，否则降级为 Research Plan。

**Acceptance Criteria**:

##### 功能验证
- [ ] 定义 `GateConfig` 配置模型：
  ```python
  @dataclass
  class GateConfig:
      # 证据数量门控
      min_observations: int = 3              # 最少证据数量
      min_source_types: int = 2              # 最少来源类型数（如：news + congress）

      # 分数门控
      min_attention_score: float = 60.0      # 最低综合分数
      min_confidence_score: float = 50.0     # 最低置信度
      min_catalyst_or_flow: float = 40.0     # catalyst_score 或 flow_score 至少一个达标

      # 时效性门控
      max_observation_age_hours: int = 72    # 最新证据不超过 N 小时

      # 一致性门控
      require_consistent_direction: bool = True  # 多源证据方向需一致

      # 特殊门控
      congress_trade_boost: bool = True      # 有国会交易时降低其他门槛
      filing_required_for_large_cap: bool = True  # 大盘股需要 SEC filing 支持
  ```

- [ ] 实现 `GateEngine` 类：
  ```python
  class GateEngine:
      def __init__(self, config: GateConfig):
          self.config = config

      def evaluate(self, event: Event, observations: List[Observation]) -> GateResult:
          """
          评估事件是否通过门控
          返回 GateResult，包含是否通过、失败原因、改进建议
          """
          checks = []

          # 1. 证据数量检查
          checks.append(self._check_observation_count(observations))

          # 2. 来源多样性检查
          checks.append(self._check_source_diversity(observations))

          # 3. 分数检查
          checks.append(self._check_scores(event))

          # 4. 时效性检查
          checks.append(self._check_freshness(observations))

          # 5. 一致性检查
          checks.append(self._check_consistency(observations))

          # 6. 特殊条件检查
          checks.append(self._check_special_conditions(event, observations))

          return self._aggregate_results(checks)

      def _aggregate_results(self, checks: List[GateCheck]) -> GateResult:
          """聚合所有检查结果"""
          passed = all(c.passed for c in checks)
          failed_gates = [c for c in checks if not c.passed]

          return GateResult(
              passed=passed,
              output_type="trade_idea" if passed else "research_plan",
              checks=checks,
              failed_gates=failed_gates,
              improvement_suggestions=self._generate_suggestions(failed_gates)
          )
  ```

- [ ] 定义 `GateResult` 返回结构：
  ```python
  @dataclass
  class GateCheck:
      gate_name: str              # e.g., "observation_count", "source_diversity"
      passed: bool
      actual_value: Any           # 实际值
      required_value: Any         # 门槛值
      message: str                # 人类可读消息
      weight: float = 1.0         # 权重（用于计算整体置信度）

  @dataclass
  class GateResult:
      passed: bool                           # 是否通过所有必要门控
      output_type: str                       # "trade_idea" | "research_plan"
      checks: List[GateCheck]                # 所有检查详情
      failed_gates: List[GateCheck]          # 失败的门控
      improvement_suggestions: List[str]     # 改进建议
      gate_score: float                      # 综合门控得分（0-100）
      near_pass_gates: List[GateCheck]       # 接近通过的门控（用于提示）
  ```

- [ ] 实现 **软门控 vs 硬门控**：
  - **硬门控**（必须通过）：
    - `min_observations >= 1`（至少有 1 条证据）
    - `min_attention_score >= 30`（最低分数门槛）
    - `max_observation_age_hours <= 168`（证据不超过 7 天）
  - **软门控**（可配置严格程度）：
    - `min_observations`（默认 3，可调整）
    - `min_source_types`（默认 2，可调整）
    - `min_confidence_score`（默认 50，可调整）

- [ ] 实现 **门控豁免规则**：
  - 国会交易（Congress Trade）存在时：
    - `min_source_types` 降为 1
    - `min_attention_score` 降低 10 分
  - SEC 重大 Filing（8-K, insider transaction）存在时：
    - `min_observations` 降为 2
  - 高置信度异常（anomaly_score > 90）：
    - 可绕过 `min_source_types` 检查

- [ ] 实现 **Research Plan 自动生成**：
  - 当门控未通过时，自动生成 Research Plan
  - Research Plan 包含：
    - `questions`: 基于 failed_gates 生成具体问题
    - `suggested_sources`: 建议查看的数据源
    - `confidence_gap`: 当前置信度与门槛的差距
  ```python
  def generate_research_plan(self, event: Event, gate_result: GateResult) -> ResearchPlan:
      questions = []
      suggested_sources = []

      for gate in gate_result.failed_gates:
          if gate.gate_name == "source_diversity":
              questions.append(f"Find additional sources to confirm {event.title}")
              suggested_sources.extend(["news", "sec_filings", "social_sentiment"])
          elif gate.gate_name == "confidence_score":
              questions.append(f"Verify the reliability of existing evidence for {event.entity_symbol}")
          # ... 其他门控

      return ResearchPlan(
          entity_symbol=event.entity_symbol,
          summary=f"Need more evidence before recommending action on {event.entity_symbol}",
          questions=questions,
          suggested_sources=suggested_sources,
          confidence_gap=gate_result.gate_score / 100 - 1.0
      )
  ```

##### 边界条件
- [ ] Event 没有关联 Observation → 硬门控失败，直接返回 Research Plan
- [ ] 所有 Observation 都超过 7 天 → 硬门控失败，output_type = "stale_event"
- [ ] GateConfig 中的阈值为 0 → 视为禁用该门控
- [ ] 多个软门控失败但接近通过（差距 < 10%）→ 标记为 `near_pass`，提示用户
- [ ] Congress Trade 存在但金额 < $15,000 → 不触发豁免规则

##### 错误处理
- [ ] GateConfig 无效（如负数阈值）→ 返回 400 错误，消息：`"Invalid gate config: {field} must be positive"`
- [ ] Event 不存在 → 返回 404 错误
- [ ] Observation 数据损坏 → 跳过该 Observation，记录 warning，继续评估
- [ ] 门控计算超时（> 500ms）→ 返回部分结果，标记 `incomplete = true`

##### 示例

**输入**（Event + Observations）:
```python
event = Event(
    event_id="evt_123",
    entity_symbol="AAPL",
    attention_score=72,
    anomaly_score=65,
    catalyst_score=80,
    flow_score=75,
    confidence_score=55
)

observations = [
    Observation(source="news", observed_at=now - hours(2), ...),
    Observation(source="congress", observed_at=now - hours(24), ...),
    Observation(source="sec_filing", observed_at=now - hours(48), ...)
]

config = GateConfig(
    min_observations=3,
    min_source_types=2,
    min_attention_score=60,
    min_confidence_score=50,
    congress_trade_boost=True
)
```

**输出**（GateResult - 通过）:
```python
GateResult(
    passed=True,
    output_type="trade_idea",
    checks=[
        GateCheck(
            gate_name="observation_count",
            passed=True,
            actual_value=3,
            required_value=3,
            message="Observation count meets requirement (3 >= 3)"
        ),
        GateCheck(
            gate_name="source_diversity",
            passed=True,
            actual_value=3,  # news, congress, sec_filing
            required_value=2,
            message="Source diversity meets requirement (3 >= 2)"
        ),
        GateCheck(
            gate_name="attention_score",
            passed=True,
            actual_value=72,
            required_value=60,
            message="Attention score meets requirement (72 >= 60)"
        ),
        GateCheck(
            gate_name="confidence_score",
            passed=True,
            actual_value=55,
            required_value=50,
            message="Confidence score meets requirement (55 >= 50)"
        ),
        GateCheck(
            gate_name="freshness",
            passed=True,
            actual_value=2,  # 最新证据 2 小时前
            required_value=72,
            message="Latest observation is fresh (2h < 72h)"
        )
    ],
    failed_gates=[],
    improvement_suggestions=[],
    gate_score=92.5,
    near_pass_gates=[]
)
```

**输出**（GateResult - 失败）:
```python
# 假设 confidence_score = 45（低于门槛 50）
GateResult(
    passed=False,
    output_type="research_plan",
    checks=[...],
    failed_gates=[
        GateCheck(
            gate_name="confidence_score",
            passed=False,
            actual_value=45,
            required_value=50,
            message="Confidence score below requirement (45 < 50)"
        )
    ],
    improvement_suggestions=[
        "Verify the reliability of existing evidence",
        "Look for additional high-quality sources",
        "Check for conflicting information that may be reducing confidence"
    ],
    gate_score=78.0,
    near_pass_gates=[
        GateCheck(gate_name="confidence_score", ...)  # 差距 5 分，接近通过
    ]
)
```

##### 测试要求
- [ ] 单元测试：每个门控检查逻辑（observation_count, source_diversity, scores, freshness, consistency）
- [ ] 单元测试：硬门控 vs 软门控行为差异
- [ ] 单元测试：豁免规则（Congress Trade, SEC Filing, High Anomaly）
- [ ] 单元测试：Research Plan 自动生成（基于不同 failed_gates 组合）
- [ ] 单元测试：near_pass 检测（边界值：差距 9%, 10%, 11%）
- [ ] 单元测试：GateConfig 验证（无效配置抛出异常）
- [ ] 集成测试：完整门控流程（Event + Observations → GateResult → Trade Idea / Research Plan）
- [ ] 集成测试：门控结果影响 Daily Brief 输出
- [ ] 性能测试：单次门控评估 < 50ms

---

#### US-025b: 门控配置 UI 与可视化

**Description**: 在设置页面提供门控配置的可视化界面，允许用户调整门槛值；在 Event Detail 页面展示门控评估结果，帮助用户理解为什么某个事件是 Trade Idea 或 Research Plan。

**Acceptance Criteria**:

##### 功能验证
- [ ] **Settings 页面 - Gate Configuration**：
  - 分组展示门控配置：
    - **Evidence Gates**：min_observations, min_source_types
    - **Score Gates**：min_attention_score, min_confidence_score, min_catalyst_or_flow
    - **Freshness Gates**：max_observation_age_hours
    - **Special Rules**：congress_trade_boost, filing_required_for_large_cap
  - 每个配置项显示：
    - 当前值（可编辑的数字输入框或滑块）
    - 默认值（hover 显示）
    - 简短说明（tooltip）
  - "Reset to Defaults" 按钮
  - "Save" 按钮（保存到 config.yaml 或用户配置）

- [ ] **Event Detail - Gate Evaluation Panel**：
  - 在 Action Panel 区域显示门控评估结果
  - 可视化展示：
    - **通过的门控**：绿色勾选，显示实际值 vs 门槛值
    - **失败的门控**：红色叉号，显示差距
    - **接近通过的门控**：黄色警告，显示还差多少
  - 整体门控得分：圆形进度条（0-100）
  - 输出类型标签：`Trade Idea` (绿色) 或 `Research Plan` (橙色)

- [ ] **门控进度条组件**：
  ```tsx
  <GateProgressBar
    gateName="Confidence Score"
    actualValue={55}
    requiredValue={50}
    passed={true}
    format={(v) => `${v}/100`}
  />
  // 渲染为：[========|--] 55/100 ✓ (超过门槛 10%)

  <GateProgressBar
    gateName="Source Diversity"
    actualValue={1}
    requiredValue={2}
    passed={false}
    format={(v) => `${v} types`}
  />
  // 渲染为：[====|------] 1/2 types ✗ (需要再 1 个来源)
  ```

- [ ] **改进建议展示**：
  - 当门控失败时，显示 `improvement_suggestions` 列表
  - 每条建议可点击，跳转到相关数据源（如 "Add news source" → 跳转到 News Panel）

- [ ] **门控历史**（可选）：
  - 显示该事件的门控评估历史
  - 追踪门控得分随时间的变化趋势

##### 边界条件
- [ ] 配置值超出合理范围（如 min_observations > 100）→ 显示警告，阻止保存
- [ ] 配置值为 0 → 显示提示：`"Setting to 0 disables this gate"`
- [ ] 没有 GateResult（旧事件）→ 显示 "Gate evaluation not available"
- [ ] 用户没有修改权限 → 配置项显示为只读

##### 错误处理
- [ ] 保存配置失败 → 显示错误消息，保留表单状态
- [ ] 加载配置失败 → 显示默认值，提示 "Using default configuration"
- [ ] GateResult 数据格式错误 → 显示 "Unable to parse gate result"

##### 示例

**Settings - Gate Configuration UI**:
```tsx
<div className="gate-settings">
  <h2>Trade Idea Quality Gates</h2>

  <Section title="Evidence Requirements">
    <SliderInput
      label="Minimum Observations"
      value={config.min_observations}
      min={1}
      max={10}
      default={3}
      onChange={(v) => setConfig({...config, min_observations: v})}
      tooltip="Minimum number of supporting observations required"
    />
    <SliderInput
      label="Minimum Source Types"
      value={config.min_source_types}
      min={1}
      max={5}
      default={2}
      onChange={(v) => setConfig({...config, min_source_types: v})}
      tooltip="Minimum number of different data sources (news, congress, etc.)"
    />
  </Section>

  <Section title="Score Thresholds">
    <SliderInput
      label="Minimum Attention Score"
      value={config.min_attention_score}
      min={0}
      max={100}
      default={60}
      onChange={(v) => setConfig({...config, min_attention_score: v})}
    />
    {/* ... 其他分数配置 */}
  </Section>

  <Section title="Special Rules">
    <Toggle
      label="Congress Trade Boost"
      checked={config.congress_trade_boost}
      onChange={(v) => setConfig({...config, congress_trade_boost: v})}
      description="Lower thresholds when Congress trade is present"
    />
  </Section>

  <div className="actions flex gap-2 mt-4">
    <Button variant="outline" onClick={resetToDefaults}>Reset to Defaults</Button>
    <Button onClick={saveConfig}>Save Configuration</Button>
  </div>
</div>
```

**Event Detail - Gate Evaluation Panel**:
```tsx
<div className="gate-evaluation bg-gray-50 rounded-lg p-4">
  <div className="flex justify-between items-center mb-4">
    <h4 className="font-bold">Quality Gate Evaluation</h4>
    <div className="flex items-center gap-2">
      <CircularProgress value={gateResult.gate_score} size={40} />
      <Badge variant={gateResult.passed ? "success" : "warning"}>
        {gateResult.output_type === "trade_idea" ? "Trade Idea" : "Research Plan"}
      </Badge>
    </div>
  </div>

  <div className="gate-checks space-y-2">
    {gateResult.checks.map(check => (
      <GateProgressBar
        key={check.gate_name}
        gateName={formatGateName(check.gate_name)}
        actualValue={check.actual_value}
        requiredValue={check.required_value}
        passed={check.passed}
      />
    ))}
  </div>

  {gateResult.failed_gates.length > 0 && (
    <div className="improvement-suggestions mt-4 p-3 bg-orange-50 rounded">
      <h5 className="font-semibold text-orange-800 mb-2">How to improve:</h5>
      <ul className="text-sm text-orange-700 space-y-1">
        {gateResult.improvement_suggestions.map((suggestion, i) => (
          <li key={i}>• {suggestion}</li>
        ))}
      </ul>
    </div>
  )}
</div>
```

##### 测试要求
- [ ] 单元测试：SliderInput 组件（值范围、默认值、onChange）
- [ ] 单元测试：GateProgressBar 组件（passed/failed/near-pass 状态）
- [ ] 单元测试：CircularProgress 组件（0-100 范围）
- [ ] 单元测试：配置验证逻辑（超出范围、为 0、负数）
- [ ] 集成测试：Settings 页面加载 → 修改配置 → 保存 → 刷新验证
- [ ] 集成测试：Event Detail 页面显示 GateResult
- [ ] E2E 测试：修改门控配置 → 查看 Event Detail → 验证门控评估结果变化
- [ ] 视觉回归测试：Gate Evaluation Panel 各状态截图

---

### Epic 9: 多资产统一（P1）

#### US-026: 多资产 Entity 模型统一

**Description**: 扩展 Entity 模型以支持多资产类型（Equity, Crypto, Polymarket），统一不同资产的标识符解析、元数据存储、跨资产关联。

**Acceptance Criteria**:

##### 功能验证
- [ ] 扩展 `Entity` 数据模型，支持多资产类型：
  ```python
  @dataclass
  class Entity:
      entity_id: str                    # 唯一标识（如：ent_AAPL, ent_BTC, ent_poly_123）
      entity_type: str                  # equity | crypto | polymarket | index | commodity

      # 通用标识符
      symbol: str                       # 显示用符号（AAPL, BTC, "Will Trump win?"）
      name: str                         # 全名

      # 资产特定标识符
      identifiers: Dict[str, str]       # 多标识符映射
      # Equity: {"ticker": "AAPL", "cik": "0000320193", "cusip": "037833100"}
      # Crypto: {"symbol": "BTC", "coingecko_id": "bitcoin", "binance_pair": "BTCUSDT"}
      # Polymarket: {"market_id": "0x123...", "slug": "trump-2024-election"}

      # 元数据
      metadata: Dict[str, Any]          # 资产特定元数据
      # Equity: {"sector": "Technology", "market_cap": 3000000000000, "exchange": "NASDAQ"}
      # Crypto: {"category": "Layer 1", "market_cap": 800000000000, "chains": ["Bitcoin"]}
      # Polymarket: {"category": "Politics", "end_date": "2024-11-05", "volume": 50000000}

      # 关联
      related_entities: List[str]       # 相关实体 ID 列表
      # AAPL -> [ent_MSFT, ent_GOOGL]（同板块）
      # BTC -> [ent_ETH, ent_COIN]（加密生态）

      # 状态
      is_active: bool = True
      created_at: datetime
      updated_at: datetime
  ```

- [ ] 实现 **资产类型特定的解析器**：
  ```python
  class EntityResolver:
      def resolve(self, identifier: str, asset_type: str = None) -> Entity:
          """
          智能解析标识符到 Entity
          - "AAPL" -> Equity Entity
          - "BTC" / "bitcoin" / "BTCUSDT" -> Crypto Entity
          - "0x123..." (Polymarket market ID) -> Polymarket Entity
          """
          if asset_type:
              return self._resolve_by_type(identifier, asset_type)

          # 自动检测资产类型
          if self._looks_like_crypto(identifier):
              return self._resolve_crypto(identifier)
          elif self._looks_like_polymarket(identifier):
              return self._resolve_polymarket(identifier)
          else:
              return self._resolve_equity(identifier)

      def _looks_like_crypto(self, identifier: str) -> bool:
          """检测是否为加密货币标识符"""
          crypto_patterns = ["BTC", "ETH", "USDT", "/USDT", "/USD"]
          return any(p in identifier.upper() for p in crypto_patterns)

      def _looks_like_polymarket(self, identifier: str) -> bool:
          """检测是否为 Polymarket 标识符"""
          return identifier.startswith("0x") or "polymarket" in identifier.lower()
  ```

- [ ] 实现 **跨资产关联**：
  - 自动检测相关实体：
    - Equity ↔ Equity：同行业、同指数成分
    - Crypto ↔ Crypto：同生态系统、相关协议
    - Equity ↔ Crypto：COIN ↔ BTC, MSTR ↔ BTC
    - Polymarket ↔ Equity/Crypto：市场标的关联
  - 手动关联支持：用户可添加/删除关联

- [ ] 实现 **Entity 合并与去重**：
  - 检测重复实体（如：BTC 和 BTCUSDT 指向同一资产）
  - 合并逻辑：保留主实体，创建别名映射
  - 别名解析：`resolve("BTCUSDT")` 返回 BTC 主实体

##### 边界条件
- [ ] 未知标识符 → 创建新 Entity，`entity_type = "unknown"`，标记需人工确认
- [ ] 同一标识符跨资产类型冲突（如 "LINK" 可能是 Chainlink 或某股票）→ 优先返回加密货币，记录冲突
- [ ] Polymarket 市场已结束 → `is_active = False`，仍可查询历史
- [ ] Entity 没有 identifiers → 使用 symbol 作为唯一标识
- [ ] related_entities 包含不存在的 entity_id → 过滤掉，记录 warning

##### 错误处理
- [ ] 标识符解析失败 → 返回 404 错误，消息：`"Unable to resolve identifier: {identifier}"`
- [ ] 资产类型不支持 → 返回 400 错误，消息：`"Unsupported asset type: {type}"`
- [ ] 外部 API 调用失败（如 CoinGecko）→ 使用缓存数据，标记 `stale = true`
- [ ] 合并冲突（两个 Entity 都有关联数据）→ 返回 409 错误，需要人工决策

##### 示例

**Equity Entity**:
```python
Entity(
    entity_id="ent_AAPL",
    entity_type="equity",
    symbol="AAPL",
    name="Apple Inc.",
    identifiers={
        "ticker": "AAPL",
        "cik": "0000320193",
        "cusip": "037833100",
        "isin": "US0378331005"
    },
    metadata={
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 3000000000000,
        "exchange": "NASDAQ",
        "country": "US"
    },
    related_entities=["ent_MSFT", "ent_GOOGL", "ent_META"],
    is_active=True
)
```

**Crypto Entity**:
```python
Entity(
    entity_id="ent_BTC",
    entity_type="crypto",
    symbol="BTC",
    name="Bitcoin",
    identifiers={
        "symbol": "BTC",
        "coingecko_id": "bitcoin",
        "binance_pair": "BTCUSDT",
        "coinbase_pair": "BTC-USD",
        "aliases": ["XBT", "bitcoin"]
    },
    metadata={
        "category": "Layer 1",
        "market_cap": 800000000000,
        "chains": ["Bitcoin"],
        "consensus": "Proof of Work",
        "max_supply": 21000000
    },
    related_entities=["ent_ETH", "ent_COIN", "ent_MSTR"],
    is_active=True
)
```

**Polymarket Entity**:
```python
Entity(
    entity_id="ent_poly_trump2024",
    entity_type="polymarket",
    symbol="Trump 2024 Election",
    name="Will Donald Trump win the 2024 US Presidential Election?",
    identifiers={
        "market_id": "0x123abc...",
        "slug": "will-trump-win-2024-election",
        "condition_id": "0x456def..."
    },
    metadata={
        "category": "Politics",
        "end_date": "2024-11-05",
        "volume_usd": 50000000,
        "liquidity_usd": 5000000,
        "outcomes": ["Yes", "No"],
        "current_prices": {"Yes": 0.52, "No": 0.48}
    },
    related_entities=["ent_poly_biden2024", "ent_SPY"],
    is_active=True
)
```

##### 测试要求
- [ ] 单元测试：各资产类型的 Entity 创建和验证
- [ ] 单元测试：标识符解析（Equity ticker, Crypto symbol, Polymarket ID）
- [ ] 单元测试：自动类型检测（_looks_like_crypto, _looks_like_polymarket）
- [ ] 单元测试：跨资产关联检测
- [ ] 单元测试：别名解析（BTCUSDT → BTC）
- [ ] 单元测试：边界条件（未知标识符、冲突标识符）
- [ ] 集成测试：完整解析流程（标识符 → Entity → 持久化）
- [ ] 集成测试：Entity 合并与去重

---

#### US-027: 多资产 Scoring 统一

**Description**: 统一不同资产类型的评分逻辑，确保 Equity、Crypto、Polymarket 的 4D 分数具有可比性，同时保留资产特定的评分因子。

**Acceptance Criteria**:

##### 功能验证
- [ ] 定义 **通用评分框架**：
  ```python
  class UnifiedScorer:
      def score(self, entity: Entity, observations: List[Observation]) -> Score4D:
          """
          统一评分入口，根据 entity_type 路由到特定评分器
          """
          scorer = self._get_scorer(entity.entity_type)
          raw_scores = scorer.calculate(entity, observations)

          # 标准化到 0-100
          normalized = self._normalize(raw_scores, entity.entity_type)

          return Score4D(
              anomaly_score=normalized.anomaly,
              catalyst_score=normalized.catalyst,
              flow_score=normalized.flow,
              confidence_score=normalized.confidence,
              attention_score=self._calculate_attention(normalized)
          )
  ```

- [ ] 实现 **Equity 评分器**（已有，确认兼容）：
  ```python
  class EquityScorer:
      def calculate(self, entity: Entity, observations: List[Observation]) -> RawScores:
          return RawScores(
              anomaly=self._calculate_anomaly(observations),    # 价格/成交量异常
              catalyst=self._calculate_catalyst(observations),  # 新闻/Filing/财报
              flow=self._calculate_flow(observations),          # Congress/13F
              confidence=self._calculate_confidence(observations)
          )

      def _calculate_anomaly(self, observations: List[Observation]) -> float:
          """
          Equity Anomaly: 价格变动 (40%) + 成交量 (30%) + 波动率 (20%) + 期权活动 (10%)
          """
          pass
  ```

- [ ] 实现 **Crypto 评分器**：
  ```python
  class CryptoScorer:
      def calculate(self, entity: Entity, observations: List[Observation]) -> RawScores:
          return RawScores(
              anomaly=self._calculate_anomaly(observations),
              catalyst=self._calculate_catalyst(observations),
              flow=self._calculate_flow(observations),
              confidence=self._calculate_confidence(observations)
          )

      def _calculate_anomaly(self, observations: List[Observation]) -> float:
          """
          Crypto Anomaly: 价格变动 (35%) + 成交量 (25%) + 链上活动 (25%) + 资金费率 (15%)
          """
          price_change = self._get_price_change(observations)
          volume_change = self._get_volume_change(observations)
          onchain_activity = self._get_onchain_metrics(observations)
          funding_rate = self._get_funding_rate(observations)

          return (
              price_change * 0.35 +
              volume_change * 0.25 +
              onchain_activity * 0.25 +
              funding_rate * 0.15
          )

      def _calculate_catalyst(self, observations: List[Observation]) -> float:
          """
          Crypto Catalyst: 项目公告 (30%) + 交易所上/下架 (25%) + 协议升级 (25%) + 监管新闻 (20%)
          """
          pass

      def _calculate_flow(self, observations: List[Observation]) -> float:
          """
          Crypto Flow: 交易所流入/流出 (40%) + 鲸鱼活动 (35%) + 机构持仓 (25%)
          """
          exchange_flow = self._get_exchange_flow(observations)
          whale_activity = self._get_whale_activity(observations)
          institutional = self._get_institutional_holdings(observations)

          return (
              exchange_flow * 0.40 +
              whale_activity * 0.35 +
              institutional * 0.25
          )
  ```

- [ ] 实现 **Polymarket 评分器**：
  ```python
  class PolymarketScorer:
      def calculate(self, entity: Entity, observations: List[Observation]) -> RawScores:
          return RawScores(
              anomaly=self._calculate_anomaly(observations),
              catalyst=self._calculate_catalyst(observations),
              flow=self._calculate_flow(observations),
              confidence=self._calculate_confidence(observations)
          )

      def _calculate_anomaly(self, observations: List[Observation]) -> float:
          """
          Polymarket Anomaly: 价格变动 (50%) + 成交量激增 (30%) + 价格与民调背离 (20%)
          """
          price_move = self._get_price_move(observations)
          volume_spike = self._get_volume_spike(observations)
          poll_divergence = self._get_poll_divergence(observations)

          return (
              price_move * 0.50 +
              volume_spike * 0.30 +
              poll_divergence * 0.20
          )

      def _calculate_catalyst(self, observations: List[Observation]) -> float:
          """
          Polymarket Catalyst: 相关新闻 (40%) + 官方声明 (30%) + 辩论/事件 (30%)
          """
          pass

      def _calculate_flow(self, observations: List[Observation]) -> float:
          """
          Polymarket Flow: 大额交易 (50%) + 流动性变化 (30%) + Smart Money 追踪 (20%)
          """
          large_trades = self._get_large_trades(observations)
          liquidity_change = self._get_liquidity_change(observations)
          smart_money = self._get_smart_money_activity(observations)

          return (
              large_trades * 0.50 +
              liquidity_change * 0.30 +
              smart_money * 0.20
          )
  ```

- [ ] 实现 **分数标准化**：
  ```python
  def _normalize(self, raw: RawScores, entity_type: str) -> NormalizedScores:
      """
      将原始分数标准化到 0-100，确保跨资产可比性
      使用历史分位数或 Z-score 标准化
      """
      distribution = self._get_distribution(entity_type)

      return NormalizedScores(
          anomaly=self._percentile_rank(raw.anomaly, distribution.anomaly),
          catalyst=self._percentile_rank(raw.catalyst, distribution.catalyst),
          flow=self._percentile_rank(raw.flow, distribution.flow),
          confidence=raw.confidence
      )
  ```

- [ ] 实现 **跨资产 attention_score 计算**：
  ```python
  def _calculate_attention(self, scores: NormalizedScores) -> float:
      """
      统一的 attention_score 计算，权重可按资产类型微调
      """
      weights = {
          "equity": {"anomaly": 0.30, "catalyst": 0.30, "flow": 0.25, "confidence": 0.15},
          "crypto": {"anomaly": 0.35, "catalyst": 0.25, "flow": 0.25, "confidence": 0.15},
          "polymarket": {"anomaly": 0.40, "catalyst": 0.30, "flow": 0.20, "confidence": 0.10}
      }
      w = weights.get(self.entity_type, weights["equity"])

      return (
          scores.anomaly * w["anomaly"] +
          scores.catalyst * w["catalyst"] +
          scores.flow * w["flow"] +
          scores.confidence * w["confidence"]
      )
  ```

##### 边界条件
- [ ] 某个维度没有数据（如 Polymarket 没有 Flow 数据）→ 使用默认值 50，降低 confidence
- [ ] 新资产类型没有历史分布 → 使用全局分布进行标准化
- [ ] 原始分数为负数（如价格下跌）→ 转换为异常程度（绝对值）
- [ ] 数据源不可用（如链上数据 API 挂了）→ 跳过该因子，重新计算权重

##### 错误处理
- [ ] 不支持的资产类型 → 返回 400 错误
- [ ] 评分计算失败 → 返回部分结果，标记 `incomplete = true`
- [ ] 标准化失败（历史数据不足）→ 使用原始分数，标记 `raw_score = true`

##### 示例

**Crypto 评分示例**:
```python
# 输入
entity = Entity(entity_id="ent_BTC", entity_type="crypto", symbol="BTC", ...)
observations = [
    Observation(source="price", data={"change_24h": 0.08, "volume_change": 2.5}),
    Observation(source="onchain", data={"active_addresses_change": 0.15}),
    Observation(source="exchange_flow", data={"net_flow": -50000})
]

# 输出
Score4D(
    anomaly_score=78,      # 价格 +8%，成交量 2.5x，链上活跃度上升
    catalyst_score=45,     # 无重大公告
    flow_score=85,         # 大量流出交易所（看涨信号）
    confidence_score=72,   # 多数据源确认
    attention_score=71.3   # 加权平均
)
```

**Polymarket 评分示例**:
```python
# 输入
entity = Entity(entity_id="ent_poly_trump2024", entity_type="polymarket", ...)
observations = [
    Observation(source="polymarket", data={"yes_price_change": 0.05, "volume_24h": 2000000}),
    Observation(source="news", data={"headline": "Trump leads in new poll", "sentiment": 0.7}),
    Observation(source="trades", data={"large_trades": [{"amount": 100000, "side": "yes"}]})
]

# 输出
Score4D(
    anomaly_score=82,      # Yes 价格 +5%，成交量激增
    catalyst_score=75,     # 新民调利好
    flow_score=70,         # 大额买入 Yes
    confidence_score=65,   # 单一来源（Polymarket）
    attention_score=75.5   # Polymarket 权重偏向 anomaly
)
```

##### 测试要求
- [ ] 单元测试：EquityScorer 各维度计算
- [ ] 单元测试：CryptoScorer 各维度计算（含链上数据）
- [ ] 单元测试：PolymarketScorer 各维度计算
- [ ] 单元测试：分数标准化（percentile rank）
- [ ] 单元测试：attention_score 权重计算
- [ ] 单元测试：边界条件（缺失数据、负数、API 失败）
- [ ] 集成测试：完整评分流程（Entity + Observations → Score4D）
- [ ] 集成测试：跨资产分数可比性验证（同等级事件分数应相近）

---

#### US-028: 多资产 UI 统一展示

**Description**: 在 Dashboard 和各页面统一展示多资产类型的事件和信号，支持资产类型过滤、混合排序、资产特定的可视化组件。

**Acceptance Criteria**:

##### 功能验证
- [ ] **Dashboard 多资产视图**：
  - Signal Inbox 混合展示所有资产类型的事件
  - 默认按 attention_score 排序（跨资产可比）
  - 每个事件卡片显示资产类型图标：
    - Equity: 股票图标
    - Crypto: 加密货币图标
    - Polymarket: 预测市场图标

- [ ] **资产类型过滤器**：
  ```tsx
  <AssetTypeFilter
    options={["All", "Equity", "Crypto", "Polymarket"]}
    selected={selectedTypes}
    onChange={setSelectedTypes}
    counts={{ equity: 12, crypto: 8, polymarket: 5 }}
  />
  ```
  - 支持多选（如同时查看 Equity + Crypto）
  - 显示各类型的事件数量
  - 记住用户偏好（localStorage）

- [ ] **资产特定的 EventCard 变体**：
  ```tsx
  <EventCard event={event}>
    {/* 通用部分 */}
    <EntityBadge entity={event.entity} />
    <ScoreDisplay scores={event.scores} />

    {/* 资产特定部分 */}
    {event.entity.entity_type === "equity" && (
      <EquityMetrics
        price={event.metadata.price}
        change={event.metadata.change_24h}
        volume={event.metadata.volume}
      />
    )}
    {event.entity.entity_type === "crypto" && (
      <CryptoMetrics
        price={event.metadata.price}
        change={event.metadata.change_24h}
        marketCap={event.metadata.market_cap}
        dominance={event.metadata.btc_dominance}
      />
    )}
    {event.entity.entity_type === "polymarket" && (
      <PolymarketMetrics
        yesPrice={event.metadata.yes_price}
        noPrice={event.metadata.no_price}
        volume={event.metadata.volume_24h}
        endDate={event.metadata.end_date}
      />
    )}
  </EventCard>
  ```

- [ ] **EntityBadge 组件**：
  ```tsx
  <EntityBadge entity={entity}>
    <AssetTypeIcon type={entity.entity_type} />
    <span className="symbol">{entity.symbol}</span>
    {entity.entity_type === "equity" && (
      <span className="exchange">{entity.metadata.exchange}</span>
    )}
    {entity.entity_type === "crypto" && (
      <span className="rank">#{entity.metadata.rank}</span>
    )}
  </EntityBadge>
  ```

- [ ] **Market Snapshot 多资产支持**：
  - 分区展示：Equities | Crypto | Polymarket
  - 每个区域显示 Top 5
  - 支持展开/折叠

- [ ] **Sources 页面多资产支持**：
  - 新增 Crypto Panel（交易所数据、链上数据）
  - 新增 Polymarket Panel（活跃市场、大额交易）
  - 现有面板保持不变（Congress, HedgeFunds, News, SEC）

- [ ] **跨资产关联展示**：
  - 在 Event Detail 页面显示 "Related Assets" 区块
  - 展示 entity.related_entities 中的资产
  - 点击跳转到相关资产的事件

##### 边界条件
- [ ] 没有某类资产的事件 → 过滤器中该选项显示为灰色，计数为 0
- [ ] 资产类型未知 → 使用默认图标和通用 metrics 展示
- [ ] Polymarket 市场已结束 → 显示 "Resolved" 标签和最终结果
- [ ] 跨资产关联为空 → 隐藏 "Related Assets" 区块

##### 错误处理
- [ ] 资产特定数据加载失败 → 显示通用视图，隐藏特定 metrics
- [ ] 过滤器状态异常 → 重置为 "All"
- [ ] 图标资源加载失败 → 使用文字标签代替

##### 示例

**混合资产 Signal Inbox**:
```tsx
<SignalInbox>
  {/* 过滤器 */}
  <div className="filters flex gap-2 mb-4">
    <AssetTypeFilter ... />
    <StatusFilter ... />
    <SortSelector ... />
  </div>

  {/* 混合列表 */}
  <div className="events space-y-3">
    {/* Equity Event */}
    <EventCard event={appleEvent}>
      <EntityBadge>
        <StockIcon /> AAPL <span className="text-gray-500">NASDAQ</span>
      </EntityBadge>
      <EquityMetrics price="$185.50" change="+3.2%" volume="85M" />
      <ScoreBar attention={87} />
    </EventCard>

    {/* Crypto Event */}
    <EventCard event={btcEvent}>
      <EntityBadge>
        <BitcoinIcon /> BTC <span className="text-gray-500">#1</span>
      </EntityBadge>
      <CryptoMetrics price="$52,300" change="+5.1%" mcap="$1.02T" />
      <ScoreBar attention={82} />
    </EventCard>

    {/* Polymarket Event */}
    <EventCard event={trumpEvent}>
      <EntityBadge>
        <PredictionIcon /> Trump 2024 <span className="text-gray-500">Politics</span>
      </EntityBadge>
      <PolymarketMetrics yes="52c" no="48c" volume="$2.1M" ends="Nov 5" />
      <ScoreBar attention={78} />
    </EventCard>
  </div>
</SignalInbox>
```

**Market Snapshot 多资产**:
```tsx
<MarketSnapshot>
  <Accordion>
    <AccordionItem title="Equities" count={5} defaultOpen>
      <MiniTable
        columns={["Symbol", "Price", "Change", "Score"]}
        data={topEquities}
      />
    </AccordionItem>

    <AccordionItem title="Crypto" count={5}>
      <MiniTable
        columns={["Symbol", "Price", "Change", "Score"]}
        data={topCrypto}
      />
    </AccordionItem>

    <AccordionItem title="Polymarket" count={5}>
      <MiniTable
        columns={["Market", "Yes", "Volume", "Score"]}
        data={topPolymarket}
      />
    </AccordionItem>
  </Accordion>
</MarketSnapshot>
```

##### 测试要求
- [ ] 单元测试：AssetTypeFilter 组件（单选、多选、计数）
- [ ] 单元测试：EntityBadge 组件（各资产类型）
- [ ] 单元测试：EquityMetrics、CryptoMetrics、PolymarketMetrics 组件
- [ ] 单元测试：AssetTypeIcon 组件（各类型 + 未知类型）
- [ ] 集成测试：混合资产列表渲染和过滤
- [ ] 集成测试：Market Snapshot 多资产展开/折叠
- [ ] E2E 测试：从 Dashboard 过滤资产类型 → 验证列表更新
- [ ] E2E 测试：点击跨资产关联 → 跳转到相关事件
- [ ] 视觉回归测试：各资产类型的 EventCard 截图

---

### Epic 10: 增强功能（P2）

| User Story | 标题 | 优先级 |
|------------|------|--------|
| US-029 | X 情绪异常触发 | P2 |
| US-030 | SEC 文本 Diff | P2 |
| US-031 | Portfolio Overlay | P2 |

---

#### US-029: X 情绪异常触发

**Description**: As a trader, I want the system to detect abnormal sentiment spikes on X (Twitter) for tracked entities, so that I can catch social-driven momentum early.

**P2 原因**: 需要额外 API 集成，核心系统可独立运行

**Acceptance Criteria**:

- [ ] 新增 `src/tradz/sources/x_sentiment.py` 数据源模块
- [ ] 支持至少一种 X 数据获取方式：
  - 方式 A: Apify X Scraper（推荐，无需官方 API）
  - 方式 B: X API v2（需付费 Basic tier）
  - 方式 C: 第三方情绪 API（SocialBlade, Brandwatch 等）
- [ ] 实现 `XSentimentSource` 类：
  ```python
  class XSentimentSource:
      async def fetch_sentiment(
          self,
          entity: Entity,
          lookback_hours: int = 24
      ) -> XSentimentResult:
          """
          返回:
          - mention_count: 提及次数
          - mention_velocity: 提及速度（mentions/hour）
          - sentiment_score: 情绪分数 (-1.0 ~ 1.0)
          - sentiment_std: 情绪标准差
          - top_tweets: 最具影响力的 tweets（按 engagement）
          - anomaly_detected: bool
          """
  ```
- [ ] 情绪异常检测算法：
  ```python
  def detect_anomaly(self, current: XSentimentResult, history: List[XSentimentResult]) -> bool:
      # 1. Volume spike: mention_velocity > 3x 7-day average
      volume_spike = current.mention_velocity > (avg_velocity * 3)

      # 2. Sentiment shift: |current - avg| > 2 * std
      sentiment_shift = abs(current.sentiment_score - avg_sentiment) > (2 * sentiment_std)

      # 3. Viral threshold: any tweet > 10K engagement
      viral_content = any(t.engagement > 10000 for t in current.top_tweets)

      return volume_spike or sentiment_shift or viral_content
  ```
- [ ] 生成 Observation 并关联 Event：
  ```python
  observation = Observation(
      source="x_sentiment",
      observation_type="social_anomaly",
      data={
          "mention_count": result.mention_count,
          "mention_velocity": result.mention_velocity,
          "sentiment_score": result.sentiment_score,
          "trigger_reason": "volume_spike | sentiment_shift | viral_content",
          "sample_tweets": [
              {"text": "...", "engagement": 12500, "author_followers": 50000}
          ]
      },
      quality_score=0.6,  # Social data 质量较低
      freshness=1.0
  )
  ```
- [ ] 配置项 in `config.yaml`：
  ```yaml
  x_sentiment:
      enabled: false  # P2 feature, 默认关闭
      provider: "apify"  # apify | x_api | mock
      lookback_hours: 24
      velocity_threshold: 3.0  # x倍于平均值
      sentiment_shift_sigma: 2.0
      viral_engagement_threshold: 10000
      rate_limit_per_hour: 100
  ```
- [ ] UI 展示（可选，取决于实现进度）：
  - Event Card 显示 X 情绪指标徽章
  - Evidence 部分展示 top tweets 摘要
- [ ] 速率限制和错误处理：
  - 尊重 API rate limits
  - 失败时不影响核心数据流
  - 记录失败到日志而非抛出异常
- [ ] Typecheck 通过
- [ ] 单元测试覆盖 mock 数据场景

---

#### US-030: SEC 文本 Diff

**Description**: As a researcher, I want to see what changed between consecutive SEC filings (10-K, 10-Q), so that I can quickly identify material changes without reading entire documents.

**P2 原因**: 计算密集型功能，需要 NLP 处理，核心系统可独立运行

**Acceptance Criteria**:

- [ ] 新增 `src/tradz/analysis/sec_diff.py` 模块
- [ ] 实现 `SECFilingDiffer` 类：
  ```python
  class SECFilingDiffer:
      def diff_filings(
          self,
          old_filing: SECFiling,
          new_filing: SECFiling
      ) -> FilingDiffResult:
          """
          对比两个 SEC 文件，返回差异分析

          返回:
          - summary: 变化摘要
          - sections_changed: 变更的章节列表
          - risk_factors_diff: Risk Factors 章节差异
          - md&a_diff: MD&A 章节差异
          - material_changes: 重大变更提取
          - sentiment_shift: 整体语气变化
          """
  ```
- [ ] 章节解析器：
  ```python
  class SECFilingParser:
      SECTION_PATTERNS = {
          "risk_factors": r"Item\s*1A[\.\s]*Risk\s*Factors",
          "md_and_a": r"Item\s*7[\.\s]*Management.s Discussion",
          "legal_proceedings": r"Item\s*3[\.\s]*Legal\s*Proceedings",
          "financial_statements": r"Item\s*8[\.\s]*Financial\s*Statements",
      }

      def extract_sections(self, filing_text: str) -> Dict[str, str]:
          """提取各章节文本"""
  ```
- [ ] 文本差异算法：
  ```python
  def compute_diff(self, old_text: str, new_text: str) -> SectionDiff:
      # 1. Sentence-level diff（比 word-level 更有意义）
      old_sentences = self._split_sentences(old_text)
      new_sentences = self._split_sentences(new_text)

      # 2. 使用 difflib 或更高级的语义相似度
      diff = difflib.unified_diff(old_sentences, new_sentences)

      # 3. 分类变更
      return SectionDiff(
          added_sentences=[...],
          removed_sentences=[...],
          modified_sentences=[...],  # 相似度 > 0.7 但 < 0.95
          change_magnitude=self._calculate_magnitude(diff)
      )
  ```
- [ ] 重大变更检测：
  ```python
  MATERIAL_KEYWORDS = [
      "material adverse", "significant risk", "litigation",
      "going concern", "restatement", "impairment",
      "regulatory action", "cybersecurity incident",
      "executive departure", "acquisition", "divestiture"
  ]

  def detect_material_changes(self, diff: SectionDiff) -> List[MaterialChange]:
      """识别包含重大关键词的新增/修改内容"""
  ```
- [ ] 生成 Observation：
  ```python
  observation = Observation(
      source="sec_diff",
      observation_type="filing_change",
      data={
          "filing_type": "10-K",
          "comparison": {"old": "2024-12-31", "new": "2025-12-31"},
          "change_magnitude": "high",  # low | medium | high
          "sections_changed": ["risk_factors", "md_and_a"],
          "material_changes": [
              {
                  "section": "risk_factors",
                  "keyword": "cybersecurity incident",
                  "context": "新增关于2024年12月数据泄露事件的披露..."
              }
          ],
          "summary": "新增3项风险因素，MD&A语气趋于谨慎"
      },
      quality_score=0.9,  # SEC 数据质量高
      freshness=1.0
  )
  ```
- [ ] API 端点（可选）：
  ```
  GET /api/sec/diff/{ticker}?old_date=2024-12-31&new_date=2025-12-31

  Response:
  {
    "ticker": "AAPL",
    "filing_type": "10-K",
    "diff_result": {...},
    "processing_time_ms": 2500
  }
  ```
- [ ] 配置项：
  ```yaml
  sec_diff:
      enabled: false  # P2 feature
      auto_diff_on_new_filing: true
      sections_to_compare: ["risk_factors", "md_and_a", "legal_proceedings"]
      similarity_threshold: 0.95  # Below this = modified
      cache_parsed_filings: true
  ```
- [ ] 性能考虑：
  - 解析后的 filing 结构缓存到 DuckDB
  - 长文档分块处理，避免内存问题
  - 后台异步处理，不阻塞核心流程
- [ ] Typecheck 通过
- [ ] 测试用例覆盖已知格式的 10-K/10-Q 文件

---

#### US-031: Portfolio Overlay

**Description**: As an investor, I want to overlay my personal portfolio positions on the event system, so that I can see which events affect my holdings and prioritize accordingly.

**P2 原因**: 涉及个人敏感数据，需要额外安全考虑，核心系统可独立运行

**Acceptance Criteria**:

- [ ] 新增 `src/tradz/portfolio/` 模块目录
- [ ] Portfolio 数据模型：
  ```python
  @dataclass
  class PortfolioPosition:
      symbol: str
      quantity: float
      avg_cost: float
      current_price: float  # 从 market data 获取
      market_value: float
      unrealized_pnl: float
      unrealized_pnl_pct: float
      weight_pct: float  # 占组合比重

  @dataclass
  class Portfolio:
      portfolio_id: str
      name: str
      positions: List[PortfolioPosition]
      total_value: float
      cash: float
      last_updated: datetime
  ```
- [ ] Portfolio 数据来源（支持多种）：
  ```python
  class PortfolioSource(Protocol):
      def fetch_positions(self) -> Portfolio: ...

  class ManualPortfolioSource:
      """从 JSON 文件读取手动输入的持仓"""

  class IBKRPortfolioSource:
      """从 Interactive Brokers 同步（复用 brokers/ibkr.py）"""

  class CSVPortfolioSource:
      """从 CSV 导入（支持常见券商导出格式）"""
  ```
- [ ] Portfolio 配置文件 `data/portfolio.json`：
  ```json
  {
    "portfolio_id": "my_portfolio",
    "name": "My Trading Account",
    "source": "manual",
    "positions": [
      {"symbol": "AAPL", "quantity": 100, "avg_cost": 175.50},
      {"symbol": "NVDA", "quantity": 50, "avg_cost": 450.00},
      {"symbol": "BTC/USDT", "quantity": 0.5, "avg_cost": 42000}
    ],
    "cash": 10000
  }
  ```
- [ ] Event 关联逻辑：
  ```python
  class PortfolioOverlay:
      def annotate_events(
          self,
          events: List[Event],
          portfolio: Portfolio
      ) -> List[AnnotatedEvent]:
          """
          为每个 Event 添加 portfolio context
          """
          for event in events:
              position = self._find_position(event.entity_id, portfolio)
              if position:
                  event.portfolio_context = PortfolioContext(
                      is_held=True,
                      position_size=position.quantity,
                      position_value=position.market_value,
                      portfolio_weight=position.weight_pct,
                      unrealized_pnl=position.unrealized_pnl,
                      impact_estimate=self._estimate_impact(event, position)
                  )
              else:
                  event.portfolio_context = PortfolioContext(is_held=False)
  ```
- [ ] Impact 估算：
  ```python
  def _estimate_impact(self, event: Event, position: PortfolioPosition) -> ImpactEstimate:
      """
      基于事件类型和历史数据估算潜在影响
      """
      # 使用 attention_score 作为影响强度参考
      impact_magnitude = event.attention_score / 100  # 0-1

      # 估算价格变动范围（基于历史类似事件）
      price_change_range = self._lookup_historical_impact(event.event_type)

      return ImpactEstimate(
          potential_pnl_low=position.market_value * price_change_range.low,
          potential_pnl_high=position.market_value * price_change_range.high,
          portfolio_impact_pct=position.weight_pct * impact_magnitude
      )
  ```
- [ ] UI 展示：
  - Signal Inbox 新增 "My Holdings" 筛选标签
  - Event Card 显示持仓信息：
    ```
    📊 You hold: 100 shares ($17,550, 8.5% of portfolio)
    💰 Unrealized: +$1,200 (+6.8%)
    ⚡ Potential impact: -$500 to +$800
    ```
  - Dashboard 新增 "Portfolio Impact" 卡片（可折叠）
- [ ] 隐私保护：
  - Portfolio 数据仅存储在本地 `data/` 目录
  - 不上传到任何远程服务
  - API 端点默认不暴露组合数据
  - 配置项控制是否启用：
    ```yaml
    portfolio:
        enabled: false  # 需要用户显式开启
        source: "manual"  # manual | ibkr | csv
        file_path: "data/portfolio.json"
        refresh_interval_minutes: 60
        show_values_in_ui: true  # false 则只显示是否持仓
    ```
- [ ] API 端点（本地访问）：
  ```
  GET /api/portfolio  # 获取组合概览
  GET /api/portfolio/positions  # 获取持仓列表
  GET /api/portfolio/events  # 获取影响持仓的事件
  POST /api/portfolio/sync  # 手动触发同步
  ```
- [ ] Typecheck 通过
- [ ] 单元测试覆盖 portfolio overlay 逻辑
- [ ] 验证敏感数据不会泄露到日志

---

#### Epic 10 技术实现摘要

```
src/tradz/
├── sources/
│   └── x_sentiment.py      # US-029: X 情绪源
├── analysis/
│   └── sec_diff.py         # US-030: SEC Diff 分析
├── portfolio/
│   ├── __init__.py
│   ├── models.py           # Portfolio 数据模型
│   ├── sources/
│   │   ├── base.py         # PortfolioSource 协议
│   │   ├── manual.py       # JSON 手动输入
│   │   ├── csv_import.py   # CSV 导入
│   │   └── ibkr.py         # IBKR 同步
│   └── overlay.py          # Event 关联逻辑

api/routers/
├── portfolio.py            # US-031: Portfolio API
└── sec.py                  # US-030: SEC Diff API

frontend/src/
├── components/
│   ├── portfolio/          # Portfolio 相关组件
│   │   ├── PortfolioCard.tsx
│   │   └── HoldingsBadge.tsx
│   └── events/
│       └── EventCard.tsx   # 添加 portfolio context 显示
```

#### P2 功能共同特征

| 特性 | US-029 | US-030 | US-031 |
|------|--------|--------|--------|
| 默认状态 | disabled | disabled | disabled |
| 外部依赖 | X API/Apify | 无（计算密集） | 无/可选 IBKR |
| 数据敏感度 | 低 | 低 | 高 |
| 影响核心流程 | 否 | 否 | 否 |
| 单独测试 | 是 | 是 | 是 |

**所有 P2 功能设计原则**:
1. **默认关闭** - 需要用户显式启用
2. **优雅降级** - 失败不影响核心系统
3. **独立模块** - 可单独开发、测试、部署
4. **配置驱动** - 通过 `config.yaml` 控制行为

---

## Functional Requirements / 功能需求

### 事件引擎

| ID | 需求 |
|----|------|
| FR-001 | 系统必须以 entity_id 为主键，按可配置时间窗口（默认 72h）聚合 observations 生成 events |
| FR-002 | 事件类型必须分类为：market_anomaly / catalyst_news / catalyst_filing / flow_congress / flow_13f / prediction_shift / mixed / uncertain |
| FR-003 | 事件 attention_score 必须来自关联 signals 的四维分数聚合 + coverage_bonus |
| FR-004 | 事件状态必须支持：new / ongoing / stale / resolved / dismissed |
| FR-005 | 72h 无新 observation 的事件必须自动进入 stale 状态 |
| FR-006 | 支持 Primary/Secondary 事件层级结构 |

### Today 页面

| ID | 需求 |
|----|------|
| FR-007 | Signal Inbox 必须从 events 表读取数据，支持 Active/Resolved/All 切换 |
| FR-008 | Event Card 必须显示：标题、资产 chips、四维分数、证据计数、最新更新、行动标签 |
| FR-009 | System Status 必须显示各数据源健康状态和最后更新时间 |
| FR-010 | Daily Brief 区域必须显示 Executive Summary 和 Trade/Research Ideas |

### 事件详情

| ID | 需求 |
|----|------|
| FR-011 | 事件详情页必须包含：Evidence Timeline、FactTable Spotlight、Action Panel |
| FR-012 | Evidence Timeline 必须按时间排序展示 observations，支持来源过滤 |
| FR-013 | FactTable Spotlight 必须只显示来自 FactTableEntry 的数据，禁止 LLM 自造 |
| FR-014 | Trade Idea 必须包含 Invalidation（失效条件），缺失则降级为 Research Plan |
| FR-015 | Research Plan 必须包含要验证的问题和明天要看的证据点 |

### Daily Brief

| ID | 需求 |
|----|------|
| FR-016 | Daily Brief 必须包含：Executive Summary / Top Events / Trade Ideas / Research Ideas / Open Loops / Data Quality |
| FR-017 | 生成采用双通道：FactTable 确定性 + LLM 叙事，LLM 失败必须 fallback 到模板 |
| FR-018 | 每日简报必须落盘：reports/{date}.md + reports/{date}.json + DuckDB daily_briefs 表 |
| FR-019 | SEND 邮件内容必须与 Reports 页面显示一致 |

### 用户操作

| ID | 需求 |
|----|------|
| FR-020 | 用户操作（pin/snooze/dismiss/resolve）必须持久化到 DuckDB |
| FR-021 | Snooze 的事件在到期前不得出现在 Active 列表 |
| FR-022 | Dismissed/Resolved 事件不得被自动重新激活（除非出现重大新证据，需定义规则） |

### API

| ID | 需求 |
|----|------|
| FR-023 | GET /api/events 必须返回事件列表，支持 status/sort/pagination |
| FR-024 | GET /api/events/{event_id} 必须返回事件详情（含 timeline + facts + recommendation） |
| FR-025 | POST /api/events/{event_id}/actions 必须支持 pin/snooze/dismiss/resolve |
| FR-026 | GET /api/system/status 必须返回数据源健康状态 |
| FR-027 | GET /api/briefs/{date} 必须返回结构化简报 |
| FR-028 | GET /api/reports/diff?date=...&baseline=... 必须返回对比结果（P1） |

---

## Non-Goals / 不在范围内

本 PRD 明确 **不包含** 以下功能：

1. **自动下单/券商交易执行** — 保留 IBKR read-only，不做自动交易
2. **全量 X 情绪实时流** — P2 只做异常触发检测
3. **复杂回测与收益归因** — P2 或后续版本
4. **多用户权限系统** — 当前为小团队内部工具
5. **移动端 App** — 仅 Web 界面
6. **实时推送通知** — 当前为轮询模式

---

## Design Considerations / 设计考虑

### UI/UX 原则

1. **信息架构保持不变**：Today / Signals / Sources / Reports 四个主 tab
2. **补齐而非推倒重来**：在现有页面上增强内容和交互
3. **一屏完成判断**：Event Detail 页面用户能在一页内完成"理解 → 判断 → 决定"
4. **点击数最小化**：获取今日重点 <= 3 次点击

### 页面改造重点

| 页面 | 现状 | 改造 |
|------|------|------|
| Today | Signal Inbox 为空 | 用真实 events 驱动，展示 Event Cards |
| Today | System Status 显示 0/0 | 接入真实数据源状态 |
| Today | Daily Brief 空/泛化 | 结构化简报 + CTA 按钮 |
| Signals | 纯诊断表 | 增加四维分数列，支持跳转到事件 |
| Sources | 独立面板 | 增加 "View in Event" 跳转 |
| Reports | "No reports found" | 可浏览归档列表 + Markdown viewer |
| 新增 | 无 | /events/:eventId 事件详情页 |

### 组件复用

- 现有 `EventCard` 组件需扩展字段
- 现有 TanStack Query hooks 需对接新 API
- Tailwind 样式保持一致

---

## Technical Considerations / 技术考虑

### DuckDB Schema 变更

**events 表扩展**

```sql
ALTER TABLE events ADD COLUMN event_type VARCHAR;
ALTER TABLE events ADD COLUMN parent_event_id UUID;
ALTER TABLE events ADD COLUMN last_update_at TIMESTAMP;
ALTER TABLE events ADD COLUMN start_at TIMESTAMP;
ALTER TABLE events ADD COLUMN resolved_at TIMESTAMP;
ALTER TABLE events ADD COLUMN pinned BOOLEAN DEFAULT FALSE;
ALTER TABLE events ADD COLUMN snoozed_until TIMESTAMP;
ALTER TABLE events ADD COLUMN dismissed_reason TEXT;
ALTER TABLE events ADD COLUMN title_template TEXT;
ALTER TABLE events ADD COLUMN title_source VARCHAR;  -- 'template' | 'llm'
```

**signals 表扩展**

```sql
ALTER TABLE signals ADD COLUMN event_id UUID;
```

**observations 表扩展**

```sql
ALTER TABLE observations ADD COLUMN source_url TEXT;
ALTER TABLE observations ADD COLUMN title VARCHAR(200);
ALTER TABLE observations ADD COLUMN summary VARCHAR(2000);
ALTER TABLE observations ADD COLUMN raw_payload JSON;
ALTER TABLE observations ADD COLUMN fact_entries JSON;
ALTER TABLE observations ADD COLUMN entity_mapping_confidence FLOAT;
ALTER TABLE observations ADD COLUMN payload_truncated BOOLEAN DEFAULT FALSE;
```

**新增 daily_briefs 表**

```sql
CREATE TABLE daily_briefs (
  id UUID PRIMARY KEY,
  date DATE NOT NULL,
  summary_json JSON,
  report_path_md TEXT,
  report_path_json TEXT,
  generation_method VARCHAR, -- 'claude' | 'template'
  created_at TIMESTAMP,
  run_id UUID
);
```

**新增 event_type_history 表**

```sql
CREATE TABLE event_type_history (
  id UUID PRIMARY KEY,
  event_id UUID NOT NULL,
  old_type VARCHAR,
  new_type VARCHAR NOT NULL,
  changed_at TIMESTAMP NOT NULL,
  trigger_observation_id UUID
);
```

### API 新增端点

| 端点 | 方法 | 描述 |
|------|------|------|
| /api/events | GET | 事件列表（支持 status/sort/pagination） |
| /api/events/{event_id} | GET | 事件详情 |
| /api/events/{event_id}/actions | POST | 用户操作 |
| /api/system/status | GET | 数据源健康状态 |
| /api/briefs/{date} | GET | 指定日期简报 |
| /api/reports/diff | GET | 报告差分（P1） |

### LLM 抽象层

支持三种 Provider：
- `ClaudeCLIProvider`：通过 Claude CLI 调用
- `OpenRouterProvider`：通过 OpenRouter API 调用（推荐用于降低成本）
- `MockProvider`：用于测试

### 降级策略

| 场景 | 降级方案 |
|------|----------|
| LLM 失败 | Fallback 到模板引擎生成 |
| 单个数据源失败 | 继续处理其他源，在 System Status 标记 |
| DuckDB 查询超时 | 返回缓存数据 + 警告 |

### 性能要求

| 指标 | 目标 |
|------|------|
| Today 页面加载 | < 2s（本地） |
| Event Timeline | 分页加载，每页 20 条 |
| Daily Brief 生成 | < 60s（含 LLM 调用） |

---

## Success Metrics / 成功指标

### 定量指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 每日 Active Events | >= 3 | 自动化测试 |
| Daily Brief 成功率 | >= 95% | 日志统计 |
| 证据一致性 | 100% | E2E 测试 |
| 页面加载时间 | < 2s | Performance 监控 |
| 代码测试覆盖率 | >= 85% (UI) / >= 90% (Backend) | CI 报告 |

### 定性指标

| 指标 | 目标 |
|------|------|
| 用户满意度 | 早晨 10 分钟内完成 review |
| 信息优势感 | "Borderline unfair" 体验 |
| 减少手工操作 | 不再需要盯 15 个标签页 |

---

## Open Questions / 待定问题

1. **重大新证据的定义** — Dismissed 事件在什么条件下应该重新激活？建议：attention_score 增加 > 20 或出现新的强催化剂
2. **Coverage Bonus 权重** — 多源覆盖的加分幅度？建议：每增加一个独立来源 +5 分，上限 +20
3. **Trade Idea 门控阈值** — confidence >= 70 是否合适？需要根据实际数据调整
4. **Polymarket 市场筛选** — 哪些类别的预测市场应该纳入？当前配置：Economy, Crypto, Business, Politics, Finance, Stocks, Tech
5. **X 情绪异常检测算法** — P2 阶段需要定义具体的异常检测逻辑

---

## Milestones / 里程碑

### Milestone A: 事件能生成 + Inbox 不为空

**交付物**
- US-001a/b/c/d: Event Builder 完整实现
- US-004a/b: Events API + Signal Inbox UI
- US-005: Event Card
- US-007a/b: System Status

**验收标准**
- Today 至少 3 个事件卡片可打开详情页
- 所有 Unit tests 通过，覆盖率 >= 90%

---

### Milestone B: 事件详情页 + 证据链 + 建议门控

**交付物**
- Event Detail 页面上线
- FactSpotlight 引用 fact_id
- ActionPanel 输出 Trade/Research（带失效条件）
- US-006: Event Card 用户操作

**验收标准**
- 每个事件可审计
- Trade Idea 门控生效

---

### Milestone C: Daily Brief 结构化生成 + Reports 归档

**交付物**
- daily_briefs 表/文件落盘
- Reports 页面可回看
- Send 邮件与 UI 一致

**验收标准**
- 95% 生成成功率

---

### Milestone D: Compare Yesterday + Open Loops

**交付物**
- diff API + UI
- open loops checklist + 进展更新

**验收标准**
- 每天只看变化即可

---

### Milestone E: 多资产统一 + 质量门控

**交付物**
- Entity 类型扩展
- 跨资产 Event Card
- Trade Idea 门控规则配置化

**验收标准**
- Crypto/Polymarket 在 Inbox 中显示

---

### Milestone F: P2 增强功能

**交付物**
- X 情绪异常触发
- SEC 文本 Diff
- Portfolio Overlay

**验收标准**
- 功能可用，不影响核心流程

---

## Appendix / 附录

### 事件类型定义

| 类型 | 描述 | 触发条件 |
|------|------|----------|
| market_anomaly | 纯市场异常 | 仅有 market 源，且 anomaly_score >= 70 |
| catalyst_news | 新闻驱动 | 有 news 源，catalyst_score >= 60 |
| catalyst_filing | SEC 文件驱动 | 有 sec 源（8-K/10-K/10-Q） |
| flow_congress | 国会披露驱动 | 有 congress 源 |
| flow_13f | 机构持仓驱动 | 有 13f 源 |
| prediction_shift | Polymarket 概率变动 | 有 polymarket 源，概率变化 >= 10% |
| mixed | 多源混合 | 涉及 >= 2 种不同类型的源 |
| uncertain | 低置信度 | 所有 observation 的 confidence < 0.5 |

### 行动标签规则

| 标签 | 条件 |
|------|------|
| Act | confidence >= 70 且门控通过 |
| Investigate | confidence 50-70 或门控部分通过 |
| Monitor | confidence < 50 或仅市场异常 |

### 四维分数说明

| 维度 | 权重 | 来源 |
|------|------|------|
| Anomaly | 30% | 价格(40%) + 成交量(30%) + 波动率(20%) |
| Catalyst | 30% | SEC filings + News + Polymarket |
| Flow | 25% | Congress trades + 13F filings |
| Confidence | 15% | 数据质量 + 来源验证 |

### LLM Provider 配置

```yaml
llm:
  provider: "openrouter"  # claude_cli | openrouter | mock
  openrouter:
    api_key: "${OPENROUTER_API_KEY}"
    model: "anthropic/claude-3-haiku"
    timeout: 10
    max_retries: 2
  claude_cli:
    timeout: 30
  mock:
    enabled_in_test: true
```

---

*Document version: v1.8*
*Last updated: 2026-01-21*
