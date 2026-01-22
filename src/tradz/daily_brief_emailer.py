"""
Daily Brief Email Report Generator.

Generates email reports from DailyBriefContent structure to match UI brief format.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Template

logger = logging.getLogger(__name__)


class DailyBriefEmailGenerator:
    """Generates email reports from DailyBriefContent structure."""

    def __init__(self):
        self.template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tradz Daily Brief - {{ date }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            color: #7f8c8d;
            margin-bottom: 5px;
        }
        .executive-summary {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            font-size: 16px;
            line-height: 1.7;
        }
        .trade-idea {
            background: #e8f5e8;
            border: 2px solid #27ae60;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        .research-idea {
            background: #fff3cd;
            border: 2px solid #f39c12;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        .open-loop {
            background: #f8f9fa;
            border-left: 4px solid #6c757d;
            padding: 15px;
            margin: 10px 0;
        }
        .data-quality {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .source-status {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .status-ok { background: #d4edda; color: #155724; }
        .status-degraded { background: #fff3cd; color: #856404; }
        .status-error { background: #f8d7da; color: #721c24; }
        .score-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .score-anomaly { background: #e74c3c; color: white; }
        .score-catalyst { background: #3498db; color: white; }
        .score-flow { background: #27ae60; color: white; }
        .score-confidence { background: #95a5a6; color: white; }
        .event-card {
            background: #f9f9f9;
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .metadata {
            color: #7f8c8d;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f8f9fa;
            font-weight: bold;
        }
        ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .generation-method {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 10px;
        }
        .method-llm { background: #9b59b6; color: white; }
        .method-template { background: #95a5a6; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            Tradz Daily Brief - {{ date }}
            <span class="generation-method method-{{ generation_method }}">
                {{ generation_method.upper() }}
            </span>
        </h1>

        <div class="metadata">
            Generated at {{ generated_at }} UTC
        </div>

        {% if executive_summary %}
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            {{ executive_summary|safe }}
        </div>
        {% endif %}

        {% if top_events %}
        <h2>Top Events</h2>
        {% for event in top_events %}
        <div class="event-card">
            <h3>
                {{ event.title }}
                <span class="score-badge score-anomaly">A: {{ "%d"|format(event.anomaly_score) }}</span>
                <span class="score-badge score-catalyst">C: {{ "%d"|format(event.catalyst_score) }}</span>
                <span class="score-badge score-flow">F: {{ "%d"|format(event.flow_score) }}</span>
                <span class="score-badge score-confidence">CF: {{ "%d"|format(event.confidence_score) }}</span>
                <span class="score-badge" style="background: #34495e; color: white;">
                    Total: {{ "%d"|format(event.attention_score) }}
                </span>
            </h3>
            <p><strong>Type:</strong> {{ event.event_type.replace("_", " ").title() }}</p>
            <p><strong>Observations:</strong> {{ event.observation_count }} data points</p>
            {% if event.last_update_at %}
            <p><strong>Last Updated:</strong> {{ event.last_update_at.strftime('%Y-%m-%d %H:%M UTC') }}</p>
            {% endif %}
        </div>
        {% endfor %}
        {% endif %}

        {% if trade_ideas %}
        <h2>Trade Ideas</h2>
        {% for idea in trade_ideas %}
        <div class="trade-idea">
            <h3>
                {{ idea.ticker or "N/A" }} - {{ idea.direction.upper() }}
                <span class="score-badge" style="background: #27ae60; color: white;">
                    Confidence: {{ "%d"|format(idea.confidence_level) }}%
                </span>
            </h3>
            <p><strong>Rationale:</strong> {{ idea.rationale }}</p>
            <table>
                <tr>
                    <th>Entry Zone</th>
                    <th>Target</th>
                    <th>Stop Loss</th>
                </tr>
                <tr>
                    <td>{{ idea.entry_zone }}</td>
                    <td>{{ idea.target }}</td>
                    <td>{{ idea.stop_loss }}</td>
                </tr>
            </table>
        </div>
        {% endfor %}
        {% endif %}

        {% if research_ideas %}
        <h2>Research Ideas</h2>
        <p><em>These events show potential but need more evidence before trading:</em></p>
        {% for research in research_ideas %}
        <div class="research-idea">
            <h3>{{ research.ticker or "N/A" }} - Score: {{ "%d"|format(research.current_score) }}</h3>
            {% if research.questions %}
            <p><strong>Questions to Verify:</strong></p>
            <ul>
                {% for question in research.questions %}
                <li>{{ question }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            {% if research.evidence_to_watch %}
            <p><strong>Evidence to Watch:</strong></p>
            <ul>
                {% for evidence in research.evidence_to_watch %}
                <li>{{ evidence }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
        {% endif %}

        {% if open_loops %}
        <h2>Open Loops</h2>
        <p><em>Unresolved questions from previous research plans:</em></p>
        {% for item in open_loops %}
        <div class="open-loop">
            <strong>{{ item.question if item.question else item[0] }}</strong>
            <p>Status: {{ (item.status if item.status else item[1]).replace("_", " ").title() }}</p>
        </div>
        {% endfor %}
        {% endif %}

        {% if data_quality %}
        <h2>Data Quality</h2>
        <div class="data-quality">
            {% for source in data_quality %}
            <div class="source-status status-{{ source.status }}">
                <strong>{{ source.name }}</strong><br>
                Status: {{ source.status.upper() }}<br>
                Records (24h): {{ source.record_count_24h }}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="metadata">
            <p><strong>Report Generated:</strong> {{ generated_at }} UTC</p>
            <p><strong>Method:</strong> {{ generation_method.upper() }}</p>
            {% if run_id %}
            <p><strong>Run ID:</strong> {{ run_id }}</p>
            {% endif %}
        </div>

        <p style="margin-top: 30px; font-style: italic; color: #7f8c8d;">
            <strong>Disclaimer:</strong> This report is generated by an automated system for informational purposes only.
            It should not be considered as financial advice. Always conduct your own research and consult with a qualified
            financial advisor before making investment decisions. Trading involves substantial risk of loss.
        </p>
    </div>
</body>
</html>
""")

    def generate_html_report(self, brief_data: Dict, date: str) -> str:
        """
        Generate HTML report from DailyBriefContent.

        Args:
            brief_data: DailyBriefContent data dictionary
            date: Report date (YYYY-MM-DD)

        Returns:
            HTML string
        """
        # Prepare template data
        template_data = {
            'date': date,
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'generation_method': brief_data.get('generation_method', 'template'),
            'executive_summary': brief_data.get('executive_summary', ''),
            'top_events': brief_data.get('top_events', []),
            'trade_ideas': brief_data.get('trade_ideas', []),
            'research_ideas': brief_data.get('research_ideas', []),
            'open_loops': brief_data.get('open_loops', []),
            'data_quality': brief_data.get('data_quality', []),
            'run_id': brief_data.get('run_id')
        }

        return self.template.render(**template_data)

    def generate_plain_text_report(self, brief_data: Dict, date: str) -> str:
        """
        Generate plain text report from DailyBriefContent.

        Args:
            brief_data: DailyBriefContent data dictionary
            date: Report date (YYYY-MM-DD)

        Returns:
            Plain text string
        """
        lines = []
        lines.append(f"=" * 80)
        lines.append(f"TRADZ DAILY BRIEF - {date}")
        lines.append(f"=" * 80)
        lines.append(f"")
        lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append(f"Method: {brief_data.get('generation_method', 'template').upper()}")
        lines.append(f"=" * 80)
        lines.append(f"")

        if brief_data.get('executive_summary'):
            lines.append("EXECUTIVE SUMMARY")
            lines.append("-" * 80)
            lines.append(brief_data['executive_summary'])
            lines.append("")
            lines.append("=" * 80)
            lines.append("")

        # Top Events
        if brief_data.get('top_events'):
            lines.append("TOP EVENTS")
            lines.append("-" * 80)
            for i, event in enumerate(brief_data['top_events'], 1):
                lines.append(f"{i}. {event['title']}")
                lines.append(f"   Type: {event['event_type']}")
                lines.append(f"   Attention Score: {event['attention_score']:.0f}")
                lines.append(f"   Scores - A:{event['anomaly_score']:.0f} C:{event['catalyst_score']:.0f} "
                           f"F:{event['flow_score']:.0f} CF:{event['confidence_score']:.0f}")
                if event.get('last_update_at'):
                    lines.append(f"   Last Update: {event['last_update_at']}")
                lines.append("")
            lines.append("=" * 80)
            lines.append("")

        # Trade Ideas
        if brief_data.get('trade_ideas'):
            lines.append("TRADE IDEAS")
            lines.append("-" * 80)
            for i, idea in enumerate(brief_data['trade_ideas'], 1):
                lines.append(f"{i}. {idea['ticker'] or 'N/A'} - {idea['direction'].upper()}")
                lines.append(f"   Confidence: {idea['confidence_level']:.0f}%")
                lines.append(f"   Rationale: {idea['rationale']}")
                lines.append(f"   Entry: {idea['entry_zone']} | Target: {idea['target']} | Stop: {idea['stop_loss']}")
                lines.append("")
            lines.append("=" * 80)
            lines.append("")

        # Research Ideas
        if brief_data.get('research_ideas'):
            lines.append("RESEARCH IDEAS (Need More Evidence)")
            lines.append("-" * 80)
            for research in brief_data['research_ideas']:
                lines.append(f"• {research['ticker'] or 'N/A'} (Score: {research['current_score']:.0f})")
                if research.get('questions'):
                    lines.append("  Questions:")
                    for q in research['questions']:
                        lines.append(f"    - {q}")
                lines.append("")
            lines.append("=" * 80)
            lines.append("")

        # Data Quality
        if brief_data.get('data_quality'):
            lines.append("DATA QUALITY")
            lines.append("-" * 80)
            for source in brief_data['data_quality']:
                lines.append(f"• {source['name']}: {source['status'].upper()} "
                           f"({source['record_count_24h']} records)")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")

        lines.append("DISCLAIMER")
        lines.append("-" * 80)
        lines.append("This report is for informational purposes only and should not be considered")
        lines.append("financial advice. Always conduct your own research before making investment")
        lines.append("decisions. Trading involves substantial risk of loss.")
        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_email_content(self, brief_data: Dict, date: str) -> tuple[str, Optional[str]]:
        """
        Generate both plain text and HTML email content from DailyBriefContent.

        Args:
            brief_data: DailyBriefContent data dictionary
            date: Report date (YYYY-MM-DD)

        Returns:
            Tuple of (plain_text, html_content)
        """
        plain_text = self.generate_plain_text_report(brief_data, date)
        html_content = self.generate_html_report(brief_data, date)

        return plain_text, html_content
