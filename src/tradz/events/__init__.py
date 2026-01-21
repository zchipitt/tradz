"""
Events module for aggregating observations into trackable events.

This module provides the EventBuilder class for creating and managing events
from observations, including classification, scoring, and hierarchy management.
"""
from .builder import EventBuilder

__all__ = ["EventBuilder"]
