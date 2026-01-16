"""
Tradz - Multi-Source Trading Intelligence System

A daily automated trading signal generation system powered by
multi-source data aggregation and Claude AI.
"""

__version__ = "2.0.0"

from .aggregator import DataAggregator
from .claude_reporter import ClaudeReporter, check_claude_available
from .signals import SignalGenerator
from .report import ReportGenerator
from .emailer import EmailSender

__all__ = [
    'DataAggregator',
    'ClaudeReporter',
    'check_claude_available',
    'SignalGenerator',
    'ReportGenerator',
    'EmailSender',
]
