/**
 * Usage Guide page component.
 * Renders the usage guide content in a styled format.
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight, BookOpen, Settings, Play, BarChart3, Clock, AlertTriangle, Zap, Bot, Monitor } from 'lucide-react';

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
                    Tradz 是一个多源数据聚合的自动化交易信号系统，使用 Claude AI 生成专业级分析报告。
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

                <h4 className="font-semibold mt-4 mb-2">智能报告</h4>
                <Table
                    headers={['功能模块', '说明']}
                    rows={[
                        ['🤖 Claude AI 报告', '使用 Claude Code CLI + MCP Skills 生成高质量报告'],
                        ['🔍 实时搜索', 'Claude 使用 Tavily 搜索最新新闻'],
                        ['📊 跨源分析', '识别多数据源之间的关联模式'],
                        ['🎯 信号生成', '基于价格变动、波动率、成交量分析'],
                        ['📧 邮件报告', '通过 SMTP 发送每日报告'],
                    ]}
                />
            </Section>

            <Section title="2. 安装配置" icon={<Settings size={20} />}>
                <h4 className="font-semibold mb-2">系统要求</h4>
                <ul className="list-disc list-inside mb-4 text-gray-600">
                    <li><strong>Python</strong>: 3.8+</li>
                    <li><strong>Node.js</strong>: 16+（用于 Claude Code CLI）</li>
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
python3 -c "import yfinance; import ccxt; print('✅ 依赖安装成功')"`}</CodeBlock>
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
                <CodeBlock>{`# 启动环境
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
                <h4 className="font-semibold mb-2">信号评分机制</h4>
                <p className="mb-4 text-gray-600">信号分数范围：<strong>0-100 分</strong></p>
                <Table
                    headers={['分数区间', '信号强度', '建议操作']}
                    rows={[
                        ['80-100', '🔴 极强', '重点关注，可能有重大事件'],
                        ['65-79', '🟠 强', '值得关注'],
                        ['50-64', '🟡 中等', '保持观察'],
                        ['0-49', '🟢 弱', '正常波动，无需特别关注'],
                    ]}
                />

                <h4 className="font-semibold mt-4 mb-2">评分因素</h4>
                <Table
                    headers={['因素', '条件', '加分']}
                    rows={[
                        ['日涨跌幅', '>5%', '+15'],
                        ['日涨跌幅', '>3%', '+10'],
                        ['周涨跌幅', '>10%', '+10'],
                        ['波动率变化', '>50%', '+15'],
                        ['成交量比率', '>2.0x', '+10'],
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

                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                    <p className="font-medium text-yellow-800">Claude CLI not found</p>
                    <CodeBlock>{`npm install -g @anthropic-ai/claude-code
claude --version`}</CodeBlock>
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
                    Tradz 提供交互式 Web 仪表盘，可视化展示信号数据。
                </p>

                <h4 className="font-semibold mb-2">启动方式</h4>
                <CodeBlock>{`# 一键启动
./scripts/local_up.sh

# 或手动启动
# 终端 1：启动后端
uvicorn api.main:app --reload --port 8002

# 终端 2：启动前端
cd frontend && npm run dev`}</CodeBlock>

                <h4 className="font-semibold mt-4 mb-2">访问地址</h4>
                <ul className="list-disc list-inside text-gray-600">
                    <li><strong>前端</strong>: http://localhost:5173</li>
                    <li><strong>API 文档</strong>: http://localhost:8002/api/docs</li>
                </ul>
            </Section>

            <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-blue-800 text-sm">
                    💡 <strong>提示</strong>: 完整版使用指南请查看 <code className="bg-blue-100 px-1 rounded">docs/USAGE_GUIDE_CN.md</code>
                </p>
            </div>
        </div>
    );
}
