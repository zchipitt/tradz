"""
Tests for DailyBriefEmailGenerator.

Ensures email content matches UI brief format.
"""
import pytest
from datetime import datetime
from src.tradz.daily_brief_emailer import DailyBriefEmailGenerator


class TestDailyBriefEmailGenerator:
    """Test DailyBriefEmailGenerator functionality."""

    @pytest.fixture
    def generator(self):
        """Create a DailyBriefEmailGenerator instance."""
        return DailyBriefEmailGenerator()

    @pytest.fixture
    def sample_brief_data(self):
        """Create sample DailyBriefContent data."""
        return {
            'date': '2024-01-21',
            'generation_method': 'claude',
            'executive_summary': '<p>Markets showed mixed performance today with strong earnings in tech sector.</p>',
            'top_events': [
                {
                    'event_id': 'evt-123',
                    'title': 'AAPL Surges 8% on Strong Earnings Beat',
                    'event_type': 'market_anomaly',
                    'anomaly_score': 85.5,
                    'catalyst_score': 75.0,
                    'flow_score': 60.0,
                    'confidence_score': 90.0,
                    'attention_score': 78.5,
                    'observation_count': 5,
                    'last_update_at': datetime(2024, 1, 21, 15, 30)
                },
                {
                    'event_id': 'evt-456',
                    'title': 'BTC Breaks $45K on ETF Inflows',
                    'event_type': 'catalyst_news',
                    'anomaly_score': 70.0,
                    'catalyst_score': 80.0,
                    'flow_score': 85.0,
                    'confidence_score': 75.0,
                    'attention_score': 78.0,
                    'observation_count': 8,
                    'last_update_at': datetime(2024, 1, 21, 16, 0)
                }
            ],
            'trade_ideas': [
                {
                    'event_id': 'evt-123',
                    'ticker': 'AAPL',
                    'direction': 'long',
                    'entry_zone': '$185-190',
                    'target': '$210',
                    'stop_loss': '$175',
                    'confidence_level': 85.0,
                    'rationale': 'Strong earnings momentum with high confidence'
                }
            ],
            'research_ideas': [
                {
                    'event_id': 'evt-789',
                    'ticker': 'TSLA',
                    'questions': ['Is the delivery guidance achievable?', 'How will margins hold?'],
                    'evidence_to_watch': ['Q4 delivery numbers', 'Margin expansion'],
                    'current_score': 65.0,
                    'potential_score': 85.0
                }
            ],
            'open_loops': [
                {'question': 'Will FED cut rates in March?', 'status': 'open'},
                {'question': 'Impact of new China regulations', 'status': 'in_progress'}
            ],
            'data_quality': [
                {'name': 'Equities', 'status': 'ok', 'record_count_24h': 150},
                {'name': 'Crypto', 'status': 'degraded', 'record_count_24h': 85}
            ],
            'run_id': 'run-123-456'
        }

    def test_generate_html_report(self, generator, sample_brief_data):
        """Test HTML report generation matches UI format."""
        html = generator.generate_html_report(sample_brief_data, '2024-01-21')

        # Verify essential sections are present
        assert 'Tradz Daily Brief - 2024-01-21' in html
        assert 'AAPL Surges 8% on Strong Earnings Beat' in html
        assert 'BTC Breaks $45K on ETF Inflows' in html
        assert 'Executive Summary' in html
        assert 'Top Events' in html
        assert 'Trade Ideas' in html
        assert 'Research Ideas' in html
        assert 'Open Loops' in html
        assert 'Data Quality' in html
        assert 'CLAUDE' in html  # Generation method badge
        assert 'run-123-456' in html  # Run ID present (may be split across lines)

        # Verify 4D scores are rendered
        assert 'A: 86' in html or 'A: 85' in html  # Anomaly score (rounded)
        assert 'C: 75' in html  # Catalyst score
        assert 'F: 60' in html  # Flow score
        assert 'CF: 90' in html  # Confidence score
        assert 'Total: 78' in html  # Attention score

        # Verify trade idea details
        assert 'AAPL - LONG' in html or 'AAPL - Long' in html
        assert 'Entry Zone' in html
        assert '$185-190' in html
        assert 'Target' in html
        assert '$210' in html
        assert 'Stop Loss' in html
        assert '$175' in html

        # Verify data quality indicators
        assert 'Equities' in html
        assert 'ok' in html or 'OK' in html
        assert 'Crypto' in html
        assert 'degraded' in html or 'DEGRADED' in html

    def test_generate_plain_text_report(self, generator, sample_brief_data):
        """Test plain text report generation."""
        text = generator.generate_plain_text_report(sample_brief_data, '2024-01-21')

        # Verify structure
        assert 'TRADZ DAILY BRIEF - 2024-01-21' in text
        assert 'EXECUTIVE SUMMARY' in text
        assert 'TOP EVENTS' in text
        assert 'TRADE IDEAS' in text
        assert 'RESEARCH IDEAS' in text
        assert 'DATA QUALITY' in text
        assert 'DISCLAIMER' in text

        # Verify event details
        assert 'AAPL Surges 8% on Strong Earnings Beat' in text
        assert 'Type: market_anomaly' in text or 'Type: MARKET_ANOMALY' in text
        assert 'Attention Score: 79' in text or 'Attention Score: 78' in text

        # Verify trade idea
        assert 'AAPL' in text
        assert 'LONG' in text or 'long' in text
        assert '$185-190' in text
        assert '$210' in text
        assert '$175' in text

    def test_generate_email_content(self, generator, sample_brief_data):
        """Test combined email content generation."""
        plain_text, html_content = generator.generate_email_content(
            sample_brief_data,
            '2024-01-21'
        )

        # Verify both formats are generated
        assert plain_text is not None
        assert html_content is not None
        assert isinstance(plain_text, str)
        assert isinstance(html_content, str)

        # Verify they contain similar content
        assert 'AAPL' in plain_text
        assert 'AAPL' in html_content
        assert 'BTC' in plain_text
        assert 'BTC' in html_content

    def test_empty_sections(self, generator):
        """Test that empty sections are handled gracefully."""
        brief_data = {
            'date': '2024-01-21',
            'generation_method': 'template',
            'executive_summary': '',
            'top_events': [],
            'trade_ideas': [],
            'research_ideas': [],
            'open_loops': [],
            'data_quality': [],
            'run_id': 'run-123'
        }

        text = generator.generate_plain_text_report(brief_data, '2024-01-21')
        html = generator.generate_html_report(brief_data, '2024-01-21')

        # Should not crash
        assert isinstance(text, str)
        assert isinstance(html, str)
        assert 'TRADZ DAILY BRIEF' in text
        assert 'Tradz Daily Brief' in html

    def test_html_contains_all_styles(self, generator, sample_brief_data):
        """Test that HTML contains proper styling for email clients."""
        html = generator.generate_html_report(sample_brief_data, '2024-01-21')

        # Verify CSS styling present
        assert '<style>' in html
        assert 'font-family:' in html
        assert 'background-color:' in html
        assert 'border-radius:' in html
        assert 'padding:' in html

        # Verify responsive design elements
        assert 'max-width: 800px' in html
        assert 'margin: 0 auto' in html

