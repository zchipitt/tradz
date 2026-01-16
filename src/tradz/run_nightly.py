#!/usr/bin/env python3
"""
Main entry point for nightly trading signal generation.

Workflow:
1. Load configuration
2. Aggregate data from all sources (equities, crypto, congress, etc.)
3. Generate report using Claude Code CLI (with fallback to template)
4. Send email (or dry-run)

Usage:
    python -m src.tradz.run_nightly [--use-claude] [--template-only]

Flags:
    --use-claude    Force use Claude for report generation
    --template-only Force use template (skip Claude)
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tradz.aggregator import DataAggregator
from src.tradz.claude_reporter import ClaudeReporter, check_claude_available
from src.tradz.signals import SignalGenerator
from src.tradz.report import ReportGenerator
from src.tradz.emailer import EmailSender


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Nightly trading signal generation'
    )
    parser.add_argument(
        '--use-claude',
        action='store_true',
        help='Force use Claude for report generation'
    )
    parser.add_argument(
        '--template-only',
        action='store_true',
        help='Force use template (skip Claude)'
    )
    parser.add_argument(
        '--skip-email',
        action='store_true',
        help='Skip email sending'
    )
    return parser.parse_args()


def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent.parent / 'config.yaml'

    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Add directory paths to config
    base_dir = Path(__file__).parent.parent.parent
    config['data_dir'] = str(base_dir / 'data')
    config['reports_dir'] = str(base_dir / 'reports')
    config['prompts_dir'] = str(base_dir / 'prompts')

    logger.info(f"✅ Configuration loaded from {config_path}")
    return config


def load_env_vars() -> dict:
    """Load environment variables from .env."""
    env_path = Path(__file__).parent.parent.parent / '.env'

    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"✅ Environment variables loaded from {env_path}")
    else:
        logger.warning(f"⚠️  No .env file found at {env_path}")
        logger.warning("Using system environment variables only")

    # Collect email config
    email_config = {
        'smtp_host': os.getenv('SMTP_HOST', ''),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'smtp_user': os.getenv('SMTP_USER', ''),
        'smtp_pass': os.getenv('SMTP_PASS', ''),
        'from_addr': os.getenv('SMTP_FROM', os.getenv('SMTP_USER', '')),
        'to_addr': os.getenv('SMTP_TO', os.getenv('SMTP_USER', '')),
        'dry_run': os.getenv('DRY_RUN', '1') != '0',
    }

    return email_config


def ensure_directories(config: dict):
    """Ensure required directories exist."""
    for dir_key in ['data_dir', 'reports_dir']:
        dir_path = Path(config.get(dir_key, dir_key))
        dir_path.mkdir(exist_ok=True)


def main():
    """Main execution flow."""
    args = parse_args()

    logger.info("=" * 80)
    logger.info("🚀 Starting nightly trading signal generation (Multi-Source)")
    logger.info("=" * 80)

    # Load configuration
    config = load_config()
    email_config = load_env_vars()
    ensure_directories(config)

    # Get report date
    report_date = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"📅 Report date: {report_date}")

    # Check Claude availability
    claude_available = check_claude_available()
    if claude_available:
        logger.info("✅ Claude Code CLI available")
    else:
        logger.warning("⚠️  Claude Code CLI not available")

    # Determine report generation mode
    use_claude = (
        claude_available and
        config.get('claude', {}).get('enabled', True) and
        not args.template_only
    )
    if args.use_claude and not claude_available:
        logger.error("❌ --use-claude specified but Claude CLI not available")
        sys.exit(1)

    # =========================================================================
    # Step 1: Aggregate data from all sources
    # =========================================================================
    logger.info("=" * 80)
    logger.info("📊 Step 1: Aggregating data from all sources...")
    logger.info("=" * 80)

    aggregator = DataAggregator(config)
    data = aggregator.fetch_all(date=report_date)

    # Save aggregated data
    data_path = aggregator.save_data(data, report_date)
    logger.info(f"✅ Data aggregated and saved to {data_path}")

    # Log summary
    summary = data.get('summary', {})
    logger.info(f"   Sources fetched: {summary.get('sources_fetched', 0)}")
    logger.info(f"   Equities: {summary.get('equities_count', 0)}")
    if 'congress_watchlist_matches' in summary:
        logger.info(f"   Congress watchlist matches: {summary['congress_watchlist_matches']}")

    # =========================================================================
    # Step 2: Generate signals (for scoring)
    # =========================================================================
    logger.info("=" * 80)
    logger.info("🎯 Step 2: Generating trading signals...")
    logger.info("=" * 80)

    # Get raw equity/crypto data for signal generation
    from src.tradz.sources.equities import EquitiesDataSource
    from src.tradz.sources.crypto import CryptoDataSource

    equities_source = EquitiesDataSource(
        max_retries=config.get('max_retries', 3),
        retry_delay=config.get('retry_delay', 2)
    )
    tickers = config.get('equities', {}).get('tickers', [])
    equity_data = equities_source.get_latest_data(tickers, days=60)

    crypto_source = CryptoDataSource(
        exchange_id=config.get('crypto', {}).get('exchange', 'binance'),
        max_retries=config.get('max_retries', 3),
        retry_delay=config.get('retry_delay', 2)
    )
    pairs = config.get('crypto', {}).get('pairs', [])
    crypto_data = crypto_source.get_latest_data(pairs, days=60)

    signal_gen = SignalGenerator(config)
    signals = signal_gen.generate_signals(equity_data, crypto_data)

    logger.info(f"✅ Generated {len(signals['all_signals'])} signals")
    logger.info(f"   Top equities: {len(signals['top_equities'])}")
    logger.info(f"   Top crypto: {len(signals['top_crypto'])}")

    # Add signals to aggregated data
    data['signals'] = signals

    # Re-save with signals
    aggregator.save_data(data, report_date)

    # =========================================================================
    # Step 3: Generate report
    # =========================================================================
    logger.info("=" * 80)
    if use_claude:
        logger.info("📝 Step 3: Generating report with Claude Code CLI...")
    else:
        logger.info("📝 Step 3: Generating report with template...")
    logger.info("=" * 80)

    reports_dir = Path(config['reports_dir'])

    if use_claude:
        # Use Claude for report generation
        reporter = ClaudeReporter(config)
        markdown_report = reporter.generate_report(data, report_date)
    else:
        # Use template fallback
        report_gen = ReportGenerator(config)
        markdown_report = report_gen.generate_markdown(signals, report_date)

        # Save report
        md_path = reports_dir / f"{report_date}.md"
        md_path.write_text(markdown_report, encoding='utf-8')

    # Generate plain text for email
    report_gen = ReportGenerator(config)
    text_report = report_gen.generate_plain_text(signals, report_date)

    logger.info(f"✅ Report generated ({len(markdown_report)} chars)")

    # Save signals JSON
    json_path = reports_dir / f"{report_date}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(signals, f, indent=2, default=str, ensure_ascii=False)
    logger.info(f"✅ Signals JSON saved to {json_path}")

    # =========================================================================
    # Step 4: Send email
    # =========================================================================
    if args.skip_email:
        logger.info("=" * 80)
        logger.info("📧 Step 4: Skipping email (--skip-email)")
        logger.info("=" * 80)
    else:
        logger.info("=" * 80)
        logger.info("📧 Step 4: Sending email...")
        logger.info("=" * 80)

        # Validate email config
        if not EmailSender.validate_config(email_config):
            logger.error("❌ Email configuration invalid. Skipping email send.")
            logger.info("Report files saved successfully. You can send them manually.")
        else:
            # Create email sender
            sender = EmailSender(**email_config)

            # Email subject
            subject = config.get('email', {}).get('subject_template', 'Trading Signals Brief - {date}')
            subject = subject.format(date=report_date)

            # Send email
            success = sender.send_report(subject, text_report)

            if success:
                if email_config['dry_run']:
                    logger.info("✅ Dry-run completed successfully")
                else:
                    logger.info("✅ Email sent successfully")
            else:
                logger.error("❌ Failed to send email")

    # =========================================================================
    # Final summary
    # =========================================================================
    logger.info("=" * 80)
    logger.info("🎉 Nightly signal generation completed successfully!")
    logger.info("=" * 80)
    logger.info("Report files:")
    logger.info(f"  - Data: {data_path}")
    logger.info(f"  - JSON: {json_path}")
    logger.info(f"  - Markdown: {reports_dir / f'{report_date}.md'}")
    if use_claude:
        logger.info("  - Generated by: Claude Code CLI")
    else:
        logger.info("  - Generated by: Template")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
