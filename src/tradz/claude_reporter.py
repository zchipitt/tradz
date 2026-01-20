"""
Claude Code CLI integration for report generation.
Uses Claude with MCP Skills to generate high-quality trading reports.
"""
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ClaudeReporter:
    """Generates trading reports using Claude Code CLI."""

    def __init__(self, config: Dict):
        """
        Initialize Claude reporter.

        Args:
            config: Configuration dict
        """
        self.config = config
        self.claude_config = config.get('claude', {})

        # Directories
        self.prompts_dir = Path(config.get('prompts_dir', 'prompts'))
        self.reports_dir = Path(config.get('reports_dir', 'reports'))
        self.data_dir = Path(config.get('data_dir', 'data'))

        # Ensure directories exist
        self.reports_dir.mkdir(exist_ok=True)

        # Settings
        self.timeout = self.claude_config.get('timeout', 300)
        self.skip_permissions = self.claude_config.get('skip_permissions', True)
        self.fallback_to_template = self.claude_config.get('fallback_to_template', True)

    def generate_report(self, data: Dict, date: Optional[str] = None, fact_table: Optional[Dict] = None) -> str:
        """
        Generate a trading report using Claude.

        Args:
            data: Aggregated data from DataAggregator
            date: Report date (defaults to today)
            fact_table: Optional verified fact table for dual-channel reporting

        Returns:
            Generated report as Markdown string
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Generating report for {date} using Claude")

        # Check if Claude is enabled
        if not self.claude_config.get('enabled', True):
            logger.info("Claude disabled, using template fallback")
            return self._generate_with_template(data, date)

        try:
            # Build the prompt
            prompt = self._build_prompt(data, date, fact_table)

            # Invoke Claude CLI
            report = self._invoke_claude(prompt)

            if not report or len(report.strip()) < 100:
                raise ValueError("Claude returned empty or too short response")

            # Save report
            self._save_report(report, date)

            logger.info(f"Report generated successfully ({len(report)} chars)")
            return report

        except Exception as e:
            logger.error(f"Claude report generation failed: {e}")

            if self.fallback_to_template:
                logger.info("Falling back to template generation")
                return self._generate_with_template(data, date)
            else:
                raise

    def _build_prompt(self, data: Dict, date: str, fact_table: Optional[Dict] = None) -> str:
        """
        Build the prompt for Claude.

        Args:
            data: Aggregated data
            date: Report date
            fact_table: Optional verified fact table

        Returns:
            Complete prompt string
        """
        # Load system prompt
        system_prompt = self._load_prompt('report_system.md')

        # Load user prompt template
        user_template = self._load_prompt('report_user.md')

        # Generate data summary
        data_summary = self._generate_data_summary(data)

        # Data file path
        data_path = self.data_dir / f"{date}.json"
        
        # Format Fact Table if present
        fact_section = ""
        if fact_table:
            fact_json = json.dumps(fact_table, indent=2, default=str)
            fact_section = f"""
## Verified Fact Table
CRITICAL: The following JSON contains the DETERMINISTIC FACTS for this report. 
You MUST use these numbers and values. Do not calculate metrics yourself if they are present here.
Use this table to audit your narrative.

```json
{fact_json}
```
"""

        # Fill in the template
        # We append fact_section to data_summary or handle it as a new variable if template supports it.
        # But assuming template just takes {data_summary}, we can append it there or inject it.
        
        # Let's verify template content first? 
        # Assuming template has {data_summary}, we can just append to it for now.
        
        full_user_content = user_template.format(
            date=date,
            data_summary=data_summary + "\n" + fact_section,
            data_path=str(data_path),
        )

        # Combine prompts
        full_prompt = f"""
{system_prompt}

---

{full_user_content}
"""
        return full_prompt

    def _load_prompt(self, filename: str) -> str:
        """Load a prompt file."""
        filepath = self.prompts_dir / filename
        if filepath.exists():
            return filepath.read_text(encoding='utf-8')
        else:
            logger.warning(f"Prompt file not found: {filepath}")
            return ""

    def _generate_data_summary(self, data: Dict) -> str:
        """Generate a text summary of the data."""
        summary_parts = []
        sources = data.get('sources', {})
        summary = data.get('summary', {})

        # Overall summary
        summary_parts.append(f"Date: {data.get('date', 'Unknown')}")
        summary_parts.append(f"Sources fetched: {summary.get('sources_fetched', 0)}")

        # Equities
        if 'equities' in sources and 'count' in sources['equities']:
            eq_count = sources['equities']['count']
            summary_parts.append(f"Equities: {eq_count} tickers")
            if 'top_equity_gainer' in summary:
                g = summary['top_equity_gainer']
                summary_parts.append(f"  Top gainer: {g['ticker']} ({g['return']:+.1f}%)")
            if 'top_equity_loser' in summary:
                l = summary['top_equity_loser']
                summary_parts.append(f"  Top loser: {l['ticker']} ({l['return']:+.1f}%)")

        # Crypto
        if 'crypto' in sources and 'count' in sources['crypto']:
            summary_parts.append(f"Crypto: {sources['crypto']['count']} pairs")

        # Congress
        if 'congress' in sources and 'count' in sources['congress']:
            c = sources['congress']
            summary_parts.append(f"Congress trades: {c['count']} total")
            if 'watchlist_overlap' in c:
                overlap = c['watchlist_overlap']
                summary_parts.append(f"  Watchlist matches: {len(overlap)}")
                for t in overlap[:3]:
                    summary_parts.append(f"    - {t['member']} {t['type']} {t['ticker']}")

        # Hedge funds
        if 'hedgefunds' in sources and 'filings_found' in sources['hedgefunds']:
            hf = sources['hedgefunds']
            summary_parts.append(f"Hedge fund 13F filings: {hf['filings_found']}")

        # Polymarket
        if 'polymarket' in sources and 'total_markets' in sources['polymarket']:
            pm = sources['polymarket']
            summary_parts.append(f"Polymarket markets: {pm['total_markets']}")
            if 'high_probability_events' in pm:
                summary_parts.append(f"  High probability events: {len(pm['high_probability_events'])}")

        # News
        if 'news' in sources and 'summary' in sources['news']:
            n = sources['news']['summary']
            summary_parts.append(f"News articles: {n.get('total_articles', 0)}")

        # SEC filings
        if 'sec_filings' in sources and 'summary' in sources['sec_filings']:
            sec = sources['sec_filings']['summary']
            summary_parts.append(f"SEC filings: {sec.get('total_filings', 0)}")

        return "\n".join(summary_parts)

    def _invoke_claude(self, prompt: str) -> str:
        """
        Invoke Claude CLI with the given prompt.

        Args:
            prompt: The prompt to send

        Returns:
            Claude's response
        """
        # Build command
        cmd = [
            "claude",
            "-p", prompt,
            "--output-format", "text",
        ]

        # Add permission skip flag for automation
        if self.skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        logger.info("Invoking Claude CLI...")
        logger.debug(f"Command: {' '.join(cmd[:3])}...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ},
                cwd=str(Path.cwd()),  # Run from project root
            )

            if result.returncode != 0:
                logger.error(f"Claude CLI error: {result.stderr}")
                raise RuntimeError(f"Claude CLI failed with code {result.returncode}: {result.stderr}")

            return result.stdout

        except subprocess.TimeoutExpired:
            logger.error(f"Claude CLI timed out after {self.timeout}s")
            raise
        except FileNotFoundError:
            logger.error("Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
            raise

    def _save_report(self, report: str, date: str):
        """Save report to file."""
        filepath = self.reports_dir / f"{date}.md"
        filepath.write_text(report, encoding='utf-8')
        logger.info(f"Report saved to {filepath}")

    def _generate_with_template(self, data: Dict, date: str) -> str:
        """
        Generate report using template (fallback).

        Args:
            data: Aggregated data
            date: Report date

        Returns:
            Report string
        """
        from .report import ReportGenerator

        # Convert aggregated data to signal format
        signals = self._convert_to_signals(data)

        generator = ReportGenerator(self.config)
        report = generator.generate_markdown(signals, date)

        # Save report
        self._save_report(report, date)

        return report

    def _convert_to_signals(self, data: Dict) -> Dict:
        """
        Convert aggregated data to signals format for template generator.

        Args:
            data: Aggregated data

        Returns:
            Signals dict compatible with ReportGenerator
        """
        from .signals import SignalGenerator

        sources = data.get('sources', {})

        # Get raw data
        equity_data = {}
        crypto_data = {}

        # For the template fallback, we just return minimal data
        # The template generator will work with what it has

        return {
            'top_equities': [],
            'top_crypto': [],
            'all_signals': [],
            'congress': sources.get('congress', {}),
            'hedgefunds': sources.get('hedgefunds', {}),
            'polymarket': sources.get('polymarket', {}),
            'news': sources.get('news', {}),
            'sec_filings': sources.get('sec_filings', {}),
        }


def check_claude_available() -> bool:
    """
    Check if Claude CLI is available.

    Returns:
        True if claude command exists
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
