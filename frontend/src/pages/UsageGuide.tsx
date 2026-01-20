/**
 * Usage Guide page component.
 * Renders the usage guide content in a styled format.
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight, BookOpen, Settings, Play, BarChart3, Clock, AlertTriangle, Zap, Bot, Monitor, Database } from 'lucide-react';

interface SectionProps {
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
    defaultOpen?: boolean;
}

function Section({ title, icon, children, defaultOpen = false }: SectionProps) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="border border-gray-200 rounded-lg overflow-hidden mb-4">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-3 px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
            >
                {isOpen ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                <span className="text-blue-600">{icon}</span>
                <span className="font-semibold text-gray-800">{title}</span>
            </button>
            {isOpen && (
                <div className="p-4 prose prose-sm max-w-none">
                    {children}
                </div>
            )}
        </div>
    );
}

function CodeBlock({ children }: { children: string }) {
    return (
        <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm">
            <code>{children}</code>
        </pre>
    );
}

function Table({ headers, rows }: { headers: string[]; rows: string[][] }) {
    return (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                    <tr>
                        {headers.map((h, i) => (
                            <th key={i} className="px-4 py-2 text-left font-medium text-gray-700">{h}</th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {rows.map((row, i) => (
                        <tr key={i}>
                            {row.map((cell, j) => (
                                <td key={j} className="px-4 py-2 text-gray-600">{cell}</td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export function UsageGuide() {
    return (
        <div className="max-w-4xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">📘 使用指南</h1>
                <p className="text-gray-600">Tradz 多源交易信号系统详细使用文档</p>
            </div>

            <Section title="1. 系统概述" icon={<BookOpen size={20} />} defaultOpen={true}>
                <p className="mb-4">
                    Tradz 是一个多源数据聚合的自动化交易信号系统，使用 4 维评分体系和 Claude AI 生成专业级分析报告。
                </p>

                <h4 className="font-semibold mt-4 mb-2">核心数据源</h4>
                <Table
                    headers={['功能模块', '说明', '数据延迟']}
                    rows={[
                        ['📈 美股监控', '通过 yfinance 获取美国股票数据', '15-20分钟'],
                        ['💰 加密货币监控', '通过 ccxt 获取主流加密货币数据', '实时'],
                        ['🏛️ 国会议员交易', 'House/Senate 交易披露', '~45天'],
                        ['🏦 对冲基金 13F', 'SEC EDGAR 机构持仓', '季度，~45天'],
                        ['🎰 Polymarket', '预测市场赔率', '实时'],
                        ['📰 新闻聚合', 'Yahoo Finance + NewsAPI', '实时'],
                        ['📋 SEC 年报', '10-K, 10-Q, 8-K 文件', '实时'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">4 维信号评分</h4>
                <Table
                    headers={['维度', '说明', '数据来源']}
                    rows={[
                        ['📊 异常评分', '价格/成交量/波动率的 Z-score 偏离', '市场数据'],
                        ['🎯 催化剂评分', '新闻、SEC 文件、预测市场事件', '多源信息'],
                        ['💸 资金流评分', '国会交易、13F 机构资金流', '披露数据'],
                        ['✅ 置信度评分', '数据质量和跨源验证', '质量指标'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">智能报告</h4>
                <Table
                    headers={['功能模块', '说明']}
                    rows={[
                        ['🤖 Claude AI 报告', '使用 Claude Code CLI + MCP Skills 生成高质量报告'],
                        ['🔍 实时搜索', 'Claude 使用 Tavily 搜索最新新闻'],
                        ['📊 跨源分析', '识别多数据源之间的关联模式'],
                        ['🎯 信号生成', '基于 4 维评分体系'],
                        ['📧 邮件报告', '通过 SMTP 发送每日报告'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">Web 仪表盘（事件中心化设计）</h4>
                <Table
                    headers={['功能模块', '说明']}
                    rows={[
                        ['🖥️ 事件中心化仪表盘', '从 Ticker 视图转为事件驱动设计'],
                        ['📋 信号收件箱', '事件卡片展示关注度评分、4D 评分、证据摘要'],
                        ['📊 事件状态机', 'New/Ongoing/Stale/Resolved/Dismissed'],
                        ['⚡ 事件操作', '置顶/推迟/标记已解决/驳回'],
                        ['🔌 FastAPI 后端', '信号、数据源和报告的 REST API'],
                        ['🔄 实时刷新', 'TanStack Query 实现 5 分钟自动刷新'],
                    ]}
                />
            </Section>

            <Section title="2. 安装配置" icon={<Settings size={20} />}>
                <h4 className="font-semibold mb-2">系统要求</h4>
                <ul className="list-disc list-inside mb-4 text-gray-600">
                    <li><strong>Python</strong>: 3.8+</li>
                    <li><strong>Node.js</strong>: 18+（用于前端和 Claude Code CLI）</li>
                    <li><strong>操作系统</strong>: macOS / Linux / Windows</li>
                </ul>

                <h4 className="font-semibold mb-2">安装步骤</h4>
                <CodeBlock>{`# 进入项目目录
cd /path/to/tradz

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填写 API 密钥
vim .env`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">验证安装</h4>
                <CodeBlock>{`source .venv/bin/activate
python3 -c "import yfinance; import ccxt; import duckdb; print('✅ 依赖安装成功')"

# 验证数据库
python3 scripts/verify_db.py`}</CodeBlock>
            </Section>

            <Section title="3. 配置详解" icon={<Settings size={20} />}>
                <h4 className="font-semibold mb-2">环境变量 (.env)</h4>
                <Table
                    headers={['变量名', '说明', '示例值']}
                    rows={[
                        ['DRY_RUN', '模拟模式（1=不发邮件）', '1'],
                        ['SMTP_HOST', '邮件服务器地址', 'smtp.gmail.com'],
                        ['SMTP_PORT', '邮件服务器端口', '587'],
                        ['SMTP_USER', '邮箱用户名', 'your@gmail.com'],
                        ['SMTP_PASS', '应用专用密码', 'xxxx-xxxx-xxxx'],
                        ['ANTHROPIC_API_KEY', 'Claude API 密钥', 'sk-ant-api03-...'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">监控列表 (config.yaml)</h4>
                <CodeBlock>{`equities:
  tickers:
    - AAPL    # 苹果
    - MSFT    # 微软
    - NVDA    # 英伟达

crypto:
  exchange: "binance"
  pairs:
    - BTC/USDT
    - ETH/USDT`}</CodeBlock>
            </Section>

            <Section title="4. 运行系统" icon={<Play size={20} />}>
                <h4 className="font-semibold mb-2">命令行参数</h4>
                <CodeBlock>{`python3 -m src.tradz.run_nightly [OPTIONS]

# 选项：
#   --use-claude      强制使用 Claude 生成报告
#   --template-only   强制使用模板生成
#   --skip-email      跳过邮件发送`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">一键启动/停止</h4>
                <CodeBlock>{`# 启动环境（后端 8002 + 前端 5173）
./scripts/local_up.sh

# 停止环境
./scripts/local_down.sh`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">查看报告</h4>
                <CodeBlock>{`# 查看今天的报告
cat reports/$(date +%Y-%m-%d).md

# 查看 JSON 数据
cat reports/$(date +%Y-%m-%d).json`}</CodeBlock>
            </Section>

            <Section title="5. 信号解读" icon={<BarChart3 size={20} />}>
                <h4 className="font-semibold mb-2">4 维信号评分</h4>
                <p className="mb-4 text-gray-600">每个信号在 4 个维度上评分（各 <strong>0-100</strong>）</p>
                
                <Table
                    headers={['维度', '说明', '权重']}
                    rows={[
                        ['异常评分 (Anomaly)', '价格/成交量/波动率的统计偏离', '30%'],
                        ['催化剂评分 (Catalyst)', '新闻、SEC 文件、预测市场事件', '30%'],
                        ['资金流评分 (Flow)', '国会交易、13F 机构资金流', '25%'],
                        ['置信度评分 (Confidence)', '数据质量和多源验证', '15%'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">综合关注度评分</h4>
                <CodeBlock>{`attention_score = anomaly × 0.30 + catalyst × 0.30 + flow × 0.25 + confidence × 0.15`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">信号强度</h4>
                <Table
                    headers={['分数区间', '信号强度', '建议操作']}
                    rows={[
                        ['80-100', '🔴 极强', '重点关注，可能有重大事件'],
                        ['65-79', '🟠 强', '值得关注'],
                        ['50-64', '🟡 中等', '保持观察'],
                        ['0-49', '🟢 弱', '正常波动，无需特别关注'],
                    ]}
                />
            </Section>

            <Section title="6. 定时任务" icon={<Clock size={20} />}>
                <h4 className="font-semibold mb-2">macOS (launchd)</h4>
                <CodeBlock>{`# 加载定时任务
launchctl load ~/Library/LaunchAgents/com.tradz.nightly.plist

# 验证是否加载成功
launchctl list | grep tradz

# 卸载定时任务
launchctl unload ~/Library/LaunchAgents/com.tradz.nightly.plist`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">Linux (cron)</h4>
                <CodeBlock>{`# 编辑 crontab
crontab -e

# 每天早上 6:30 运行
30 6 * * * /path/to/tradz/scripts/nightly.sh >> /path/to/tradz/logs/cron.log 2>&1`}</CodeBlock>
            </Section>

            <Section title="7. 故障排除" icon={<AlertTriangle size={20} />}>
                <h4 className="font-semibold mb-2">常见问题</h4>

                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                    <p className="font-medium text-yellow-800">ModuleNotFoundError: No module named 'yfinance'</p>
                    <p className="text-yellow-700 text-sm mt-1">解决方案：激活虚拟环境并安装依赖</p>
                    <CodeBlock>{`source .venv/bin/activate
pip install -r requirements.txt`}</CodeBlock>
                </div>

                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                    <p className="font-medium text-yellow-800">SMTP authentication failed</p>
                    <p className="text-yellow-700 text-sm mt-1">确认使用的是应用专用密码，而非账户密码</p>
                </div>

                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                    <p className="font-medium text-yellow-800">Claude CLI not found</p>
                    <CodeBlock>{`npm install -g @anthropic-ai/claude-code
claude --version`}</CodeBlock>
                </div>

                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                    <p className="font-medium text-yellow-800">DuckDB 数据库问题</p>
                    <CodeBlock>{`# 验证数据库
python3 scripts/verify_db.py

# 验证实体解析
python3 scripts/verify_entities.py

# 验证信号生成
python3 scripts/verify_signals.py`}</CodeBlock>
                </div>
            </Section>

            <Section title="8. 高级用法" icon={<Zap size={20} />}>
                <h4 className="font-semibold mb-2">添加更多股票代码</h4>
                <CodeBlock>{`# 编辑 config.yaml
equities:
  tickers:
    - AAPL
    - YOUR_NEW_TICKER`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">修改信号阈值</h4>
                <CodeBlock>{`thresholds:
  day_return_high: 7.0      # 增大以获得更少但更强的信号
  volume_high: 3.0          # 增大以获得更极端的成交量警报`}</CodeBlock>
            </Section>

            <Section title="9. Claude AI 报告生成" icon={<Bot size={20} />}>
                <p className="mb-4 text-gray-600">
                    Claude Code CLI 使用 MCP Skills 来增强报告质量：
                </p>
                <ul className="list-disc list-inside mb-4 text-gray-600">
                    <li><strong>tavily-search</strong>: 搜索每个信号的最新新闻</li>
                    <li><strong>filesystem</strong>: 读取历史报告进行对比</li>
                    <li><strong>sequential-thinking</strong>: 深度分析复杂信号</li>
                    <li><strong>fetch</strong>: 获取网页内容</li>
                </ul>

                <h4 className="font-semibold mb-2">安装 Claude CLI</h4>
                <CodeBlock>{`npm install -g @anthropic-ai/claude-code

# 在 .env 中设置 API 密钥
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# 验证安装
claude --version`}</CodeBlock>
            </Section>

            <Section title="10. Web 仪表盘" icon={<Monitor size={20} />}>
                <p className="mb-4 text-gray-600">
                    Tradz 提供 Robinhood 风格的事件中心化 Web 仪表盘，从传统的 Ticker 视图转为事件驱动设计。
                </p>

                <h4 className="font-semibold mb-2">一键启动</h4>
                <CodeBlock>{`# 启动后端 (8002) + 前端 (5173)
./scripts/local_up.sh

# 停止所有服务
./scripts/local_down.sh`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">手动启动</h4>
                <CodeBlock>{`# 终端 1：启动后端
uvicorn api.main:app --reload --port 8002

# 终端 2：启动前端
cd frontend && npm run dev`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">访问地址</h4>
                <ul className="list-disc list-inside text-gray-600">
                    <li><strong>前端</strong>: http://localhost:5173</li>
                    <li><strong>API 文档</strong>: http://localhost:8002/api/docs</li>
                </ul>

                <h4 className="font-semibold mt-4 mb-2">仪表盘页面</h4>
                <Table
                    headers={['页面', '功能']}
                    rows={[
                        ['Today', '事件中心化主页：系统状态、信号收件箱、每日简报、市场快照'],
                        ['Signals', '原始信号诊断表格，可排序导出'],
                        ['Sources', '国会交易、对冲基金、新闻、Polymarket 面板'],
                        ['Reports', '历史报告归档，可下载 MD/JSON'],
                        ['使用指南', '本页面 - 交互式可折叠文档'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">事件状态机</h4>
                <Table
                    headers={['状态', '说明', '颜色']}
                    rows={[
                        ['new', '新事件，首次出现', '蓝色'],
                        ['ongoing', '进行中，持续跟踪', '黄色'],
                        ['stale', '过期，超过 72h 未更新', '灰色'],
                        ['resolved', '已解决，用户标记完成', '绿色'],
                        ['dismissed', '已驳回，用户选择忽略', '红色'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">事件操作</h4>
                <ul className="list-disc list-inside text-gray-600">
                    <li><strong>置顶/取消置顶</strong>: 保持事件在收件箱顶部</li>
                    <li><strong>推迟 24h</strong>: 暂时隐藏事件</li>
                    <li><strong>标记已解决</strong>: 事件已处理完毕</li>
                    <li><strong>驳回</strong>: 从活跃视图移除</li>
                </ul>
            </Section>

            <Section title="11. 数据库与实体解析" icon={<Database size={20} />}>
                <p className="mb-4 text-gray-600">
                    Tradz 使用 DuckDB 作为本地分析数据库，存储在 <code className="bg-gray-100 px-1 rounded">data/tradz.duckdb</code>。
                </p>

                <h4 className="font-semibold mb-2">数据库表</h4>
                <Table
                    headers={['表名', '说明']}
                    rows={[
                        ['entities', '实体表（Ticker/CIK/公司名称映射）'],
                        ['observations', '观察表（各数据源的原始数据点）'],
                        ['events', '事件表（聚合相关观察的故事）'],
                        ['signals', '信号表（每日 4 维评分输出）'],
                        ['run_history', '运行历史（用于可观测性）'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">验证脚本</h4>
                <CodeBlock>{`# 验证数据库架构
python3 scripts/verify_db.py

# 验证实体解析
python3 scripts/verify_entities.py

# 验证信号生成
python3 scripts/verify_signals.py

# 验证事实生成
python3 scripts/verify_facts.py`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">实体解析</h4>
                <p className="text-gray-600 mb-2">
                    EntityResolver 负责将不同数据源的数据对齐到统一的实体 ID：
                </p>
                <ul className="list-disc list-inside text-gray-600">
                    <li>从 SEC 同步 Ticker/CIK/公司名称</li>
                    <li>解析文本中的实体（如 $AAPL）</li>
                    <li>为每个实体分配唯一 UUID</li>
                </ul>
            </Section>

            <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-blue-800 text-sm">
                    💡 <strong>提示</strong>: 完整版使用指南请查看 <code className="bg-blue-100 px-1 rounded">docs/USAGE_GUIDE_CN.md</code>
                </p>
            </div>

            <div className="mt-4 text-center text-sm text-gray-400">
                最后更新：2026-01-19
            </div>
        </div>
    );
}
