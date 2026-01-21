"""
EventBuilder module for aggregating observations into events.

Provides core event aggregation logic including:
- Grouping observations by entity_id within a configurable time window
- Event type classification based on observation sources
- 4D score calculation with coverage bonus
- Primary/Secondary event hierarchy support
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..database import Database, get_database
from ..models import (
    Event,
    EventStatus,
    EventType,
    EventTypeHistory,
    Observation,
    SourceType,
)

logger = logging.getLogger(__name__)


# Default time window for grouping observations into events (hours)
DEFAULT_TIME_WINDOW_HOURS = 72

# Maximum coverage bonus
MAX_COVERAGE_BONUS = 20

# Points per independent source for coverage bonus
COVERAGE_BONUS_PER_SOURCE = 5


class EventBuilder:
    """
    Aggregates observations into events by entity_id within a configurable time window.

    The EventBuilder groups observations for the same entity that occur within a
    specified time window, classifies events by type based on their constituent
    observations, and calculates attention scores with coverage bonuses.
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        time_window_hours: float = DEFAULT_TIME_WINDOW_HOURS,
    ):
        """
        Initialize EventBuilder.

        Args:
            db: Database instance. Uses singleton if not provided.
            time_window_hours: Time window for grouping observations (default 72h).
        """
        self.db = db or get_database()
        self.time_window_hours = time_window_hours
        self._time_window = timedelta(hours=time_window_hours)

    def build_events(
        self,
        observations: List[Observation],
        existing_events: Optional[List[Event]] = None,
    ) -> List[Event]:
        """
        Build events from a list of observations.

        Groups observations by entity_id within the configured time window,
        then creates or updates events for each group.

        Args:
            observations: List of observations to process.
            existing_events: Optional list of existing events to potentially update.
                            If not provided, queries database for open events.

        Returns:
            List of created or updated Event objects.
        """
        if not observations:
            logger.debug("No observations to process")
            return []

        # Group observations by entity_id
        grouped = self._group_observations_by_entity(observations)

        # Load existing open events if not provided
        if existing_events is None:
            existing_events = self.db.get_open_events()

        # Map existing events by primary_entity_id for quick lookup
        existing_by_entity: Dict[UUID, Event] = {}
        for event in existing_events:
            if event.primary_entity_id:
                existing_by_entity[event.primary_entity_id] = event

        events: List[Event] = []

        for entity_id, obs_list in grouped.items():
            if entity_id is None:
                # Skip observations without entity_id
                logger.debug(f"Skipping {len(obs_list)} observations without entity_id")
                continue

            # Check if there's an existing event for this entity within the time window
            existing_event = existing_by_entity.get(entity_id)

            if existing_event and self._within_time_window(existing_event, obs_list):
                # Update existing event
                event = self._update_event(existing_event, obs_list)
            else:
                # Create new event
                event = self._create_event(entity_id, obs_list)

            events.append(event)

        logger.info(f"Built {len(events)} events from {len(observations)} observations")
        return events

    def _group_observations_by_entity(
        self, observations: List[Observation]
    ) -> Dict[Optional[UUID], List[Observation]]:
        """
        Group observations by entity_id.

        Args:
            observations: List of observations to group.

        Returns:
            Dictionary mapping entity_id to list of observations.
        """
        grouped: Dict[Optional[UUID], List[Observation]] = defaultdict(list)

        for obs in observations:
            grouped[obs.entity_id].append(obs)

        return grouped

    def _within_time_window(
        self, event: Event, observations: List[Observation]
    ) -> bool:
        """
        Check if any observation falls within the time window of an event.

        Args:
            event: Existing event to check against.
            observations: New observations to check.

        Returns:
            True if any observation is within the time window of the event.
        """
        for obs in observations:
            obs_time = obs.effective_at or obs.observed_at
            event_time = event.last_update_at or event.start_at

            time_diff = abs((obs_time - event_time).total_seconds())
            if time_diff <= self._time_window.total_seconds():
                return True

        return False

    def _create_event(
        self, entity_id: UUID, observations: List[Observation]
    ) -> Event:
        """
        Create a new event from observations.

        Args:
            entity_id: The entity ID for this event.
            observations: List of observations for this event.

        Returns:
            New Event object.
        """
        # Determine primary ticker from observations
        primary_ticker = self._get_primary_ticker(observations)

        # Classify event type
        event_type = self._classify_event_type(observations)

        # Calculate 4D scores
        anomaly, catalyst, flow, confidence = self._calculate_4d_scores(observations)

        # Calculate attention score with coverage bonus
        attention = self._calculate_attention_score(
            anomaly, catalyst, flow, confidence, observations
        )

        # Determine timestamps
        start_at = min(
            obs.effective_at or obs.observed_at for obs in observations
        )
        last_update_at = max(
            obs.effective_at or obs.observed_at for obs in observations
        )

        # Generate template title (LLM title generation is handled separately in US-001c)
        title_template = self._generate_template_title(
            primary_ticker, event_type, attention
        )

        event = Event(
            id=uuid4(),
            primary_entity_id=entity_id,
            primary_ticker=primary_ticker,
            title=title_template,
            event_type=event_type,
            status=EventStatus.NEW,
            confidence=confidence / 100.0,  # Convert to 0-1 scale
            start_at=start_at,
            last_update_at=last_update_at,
            # 4D scores
            anomaly_score=anomaly,
            catalyst_score=catalyst,
            flow_score=flow,
            confidence_score=confidence,
            # Title metadata
            title_template=title_template,
            title_source="template",
            # Observation IDs
            observation_ids=[obs.id for obs in observations],
        )

        return event

    def _update_event(self, event: Event, observations: List[Observation]) -> Event:
        """
        Update an existing event with new observations.

        Args:
            event: Existing event to update.
            observations: New observations to add.

        Returns:
            Updated Event object.
        """
        # Add new observation IDs
        existing_ids = set(event.observation_ids)
        for obs in observations:
            if obs.id not in existing_ids:
                event.observation_ids.append(obs.id)

        # Get all observations for recalculation
        all_obs = self._get_all_observations_for_event(event)

        # Re-classify event type if needed
        new_type = self._classify_event_type(all_obs)
        old_type = event.event_type

        if new_type != old_type:
            # Track type change
            event.event_type = new_type
            self._record_type_change(event, old_type, new_type, observations[0].id)

        # Recalculate 4D scores
        anomaly, catalyst, flow, confidence = self._calculate_4d_scores(all_obs)
        event.anomaly_score = anomaly
        event.catalyst_score = catalyst
        event.flow_score = flow
        event.confidence_score = confidence
        event.confidence = confidence / 100.0

        # Update timestamp
        latest_obs_time = max(
            obs.effective_at or obs.observed_at for obs in observations
        )
        if latest_obs_time > event.last_update_at:
            event.last_update_at = latest_obs_time

        # Transition to ongoing if was new and now has updates after 1h
        if event.status == EventStatus.NEW:
            time_since_start = (event.last_update_at - event.start_at).total_seconds()
            if time_since_start > 3600:  # 1 hour
                event.status = EventStatus.ONGOING

        return event

    def _get_all_observations_for_event(self, _event: Event) -> List[Observation]:
        """
        Get all observations linked to an event.

        Args:
            _event: Event to get observations for (unused, placeholder for future).

        Returns:
            List of Observation objects.
        """
        # This would ideally query the database, but for now we work with observation_ids
        # In a real implementation, you'd query event_observations table
        # For simplicity, we return empty list - calling code should provide observations
        return []

    def _get_primary_ticker(self, observations: List[Observation]) -> Optional[str]:
        """
        Get the primary ticker from observations.

        Uses the most common ticker, or the first non-None ticker.

        Args:
            observations: List of observations.

        Returns:
            Primary ticker symbol or None.
        """
        ticker_counts: Dict[str, int] = defaultdict(int)

        for obs in observations:
            if obs.entity_ticker:
                ticker_counts[obs.entity_ticker] += 1

        if not ticker_counts:
            return None

        # Return most common ticker
        return max(ticker_counts.items(), key=lambda x: x[1])[0]

    def _classify_event_type(self, observations: List[Observation]) -> EventType:
        """
        Classify event type based on observation sources.

        Classification rules:
        - market_anomaly: Only EQUITIES/CRYPTO observations with anomaly indicators
        - catalyst_news: NEWS source dominant
        - catalyst_filing: SEC source dominant
        - flow_congress: CONGRESS source dominant
        - flow_13f: HEDGEFUND source dominant
        - prediction_shift: POLYMARKET source dominant
        - mixed: Multiple significant source types
        - uncertain: Cannot determine clear type

        Args:
            observations: List of observations to classify.

        Returns:
            EventType enum value.
        """
        if not observations:
            return EventType.UNCERTAIN

        # Count observations by source type
        source_counts: Dict[SourceType, int] = defaultdict(int)
        for obs in observations:
            source_counts[obs.source] += 1

        total = len(observations)

        # Define dominance threshold (40% of observations)
        dominance_threshold = 0.4

        # Check for dominance
        dominant_sources: List[Tuple[SourceType, float]] = []
        for source, count in source_counts.items():
            ratio = count / total
            if ratio >= dominance_threshold:
                dominant_sources.append((source, ratio))

        # If multiple dominant sources, it's mixed
        if len(dominant_sources) > 1:
            return EventType.MIXED

        # If single dominant source, classify accordingly
        if len(dominant_sources) == 1:
            source, _ = dominant_sources[0]
            return self._source_to_event_type(source)

        # No clear dominance - check for specific patterns
        # Market anomaly if mostly market data with high quality scores
        market_sources = {SourceType.EQUITIES, SourceType.CRYPTO}
        market_count = sum(source_counts.get(s, 0) for s in market_sources)
        if market_count / total >= 0.5:
            # Check if observations indicate anomaly
            has_anomaly = any(
                obs.payload.get("is_anomaly", False) or
                abs(obs.payload.get("price_change_pct", 0)) > 3 or
                obs.payload.get("volume_ratio", 1) > 2
                for obs in observations
            )
            if has_anomaly:
                return EventType.MARKET_ANOMALY

        # If we have a mix of different sources without dominance
        if len(source_counts) > 2:
            return EventType.MIXED

        # Cannot classify
        return EventType.UNCERTAIN

    def _source_to_event_type(self, source: SourceType) -> EventType:
        """
        Map a dominant source type to an event type.

        Args:
            source: The dominant source type.

        Returns:
            Corresponding EventType.
        """
        mapping = {
            SourceType.EQUITIES: EventType.MARKET_ANOMALY,
            SourceType.CRYPTO: EventType.MARKET_ANOMALY,
            SourceType.NEWS: EventType.CATALYST_NEWS,
            SourceType.SEC: EventType.CATALYST_FILING,
            SourceType.CONGRESS: EventType.FLOW_CONGRESS,
            SourceType.HEDGEFUND: EventType.FLOW_13F,
            SourceType.POLYMARKET: EventType.PREDICTION_SHIFT,
            SourceType.BROKER: EventType.FLOW,
            SourceType.X_SENTIMENT: EventType.CATALYST,
        }
        return mapping.get(source, EventType.UNCERTAIN)

    def _calculate_4d_scores(
        self, observations: List[Observation]
    ) -> Tuple[float, float, float, float]:
        """
        Calculate 4-dimensional scores from observations.

        The scores are:
        - anomaly_score: Based on market data observations
        - catalyst_score: Based on news, SEC filings, Polymarket
        - flow_score: Based on Congress trades, 13F filings
        - confidence_score: Based on data quality and source diversity

        Args:
            observations: List of observations to score.

        Returns:
            Tuple of (anomaly, catalyst, flow, confidence) scores (0-100 each).
        """
        anomaly = self._calculate_anomaly_score(observations)
        catalyst = self._calculate_catalyst_score(observations)
        flow = self._calculate_flow_score(observations)
        confidence = self._calculate_confidence_score(observations)

        return anomaly, catalyst, flow, confidence

    def _calculate_anomaly_score(self, observations: List[Observation]) -> float:
        """
        Calculate anomaly score from market-related observations.

        Factors:
        - Price change percentage (40%)
        - Volume vs average (30%)
        - Volatility indicators (20%)
        - Quality score weight (10%)

        Args:
            observations: List of observations.

        Returns:
            Anomaly score (0-100).
        """
        score = 50.0  # Baseline
        market_obs = [
            obs for obs in observations
            if obs.source in {SourceType.EQUITIES, SourceType.CRYPTO}
        ]

        if not market_obs:
            return score

        for obs in market_obs:
            payload = obs.payload or {}

            # Price change contribution (40% weight)
            price_change = abs(payload.get("price_change_pct", 0))
            if price_change > 10:
                score += 20 * obs.quality_score
            elif price_change > 5:
                score += 15 * obs.quality_score
            elif price_change > 3:
                score += 10 * obs.quality_score
            elif price_change > 1:
                score += 5 * obs.quality_score

            # Volume contribution (30% weight)
            volume_ratio = payload.get("volume_ratio", 1.0)
            if volume_ratio > 5:
                score += 15 * obs.quality_score
            elif volume_ratio > 3:
                score += 10 * obs.quality_score
            elif volume_ratio > 2:
                score += 5 * obs.quality_score

            # Volatility contribution (20% weight)
            vol_change = abs(payload.get("volatility_change_pct", 0))
            if vol_change > 100:
                score += 10 * obs.quality_score
            elif vol_change > 50:
                score += 5 * obs.quality_score

        return min(max(score, 0), 100)

    def _calculate_catalyst_score(self, observations: List[Observation]) -> float:
        """
        Calculate catalyst score from news, filings, and prediction markets.

        Factors:
        - SEC filings (high weight for 8-K)
        - News articles (medium weight)
        - Polymarket probability shifts (medium weight)
        - Social sentiment (low weight)

        Args:
            observations: List of observations.

        Returns:
            Catalyst score (0-100).
        """
        score = 50.0  # Baseline

        weights = {
            SourceType.SEC: 20,
            SourceType.NEWS: 10,
            SourceType.POLYMARKET: 15,
            SourceType.X_SENTIMENT: 5,
        }

        for obs in observations:
            base_weight = weights.get(obs.source, 0)
            if base_weight == 0:
                continue

            # Apply freshness decay
            now = datetime.now(timezone.utc)
            obs_time = obs.observed_at
            if obs_time.tzinfo is None:
                obs_time = obs_time.replace(tzinfo=timezone.utc)
            age_hours = (now - obs_time).total_seconds() / 3600
            decay = max(0, 1.0 - (age_hours / 72))  # Full decay over 72h

            impact = base_weight * decay * obs.quality_score

            # Boost for specific conditions
            if obs.source == SourceType.SEC:
                form = obs.payload.get("form", "")
                if form == "8-K":
                    impact *= 1.5  # Material events
                elif form in ["10-K", "10-Q"]:
                    impact *= 1.2

            if obs.source == SourceType.POLYMARKET:
                prob_change = abs(obs.payload.get("probability_change", 0))
                if prob_change > 10:
                    impact *= 1.5

            score += impact

        return min(max(score, 0), 100)

    def _calculate_flow_score(self, observations: List[Observation]) -> float:
        """
        Calculate flow score from Congress trades and 13F filings.

        Factors:
        - Congress trades (high weight for recent, large trades)
        - 13F position changes (medium weight)
        - Broker activity (low weight)

        Args:
            observations: List of observations.

        Returns:
            Flow score (0-100).
        """
        score = 50.0  # Baseline

        for obs in observations:
            if obs.source == SourceType.CONGRESS:
                payload = obs.payload or {}
                tx_type = payload.get("type", "").lower()

                # Base impact for Congress trade
                impact = 15 * obs.freshness_score * obs.quality_score

                if "purchase" in tx_type:
                    score += impact
                elif "sale" in tx_type:
                    score -= impact * 0.5  # Sales have less negative impact

            elif obs.source == SourceType.HEDGEFUND:
                # 13F filings (typically older data)
                impact = 10 * obs.freshness_score * obs.quality_score

                payload = obs.payload or {}
                change_pct = payload.get("position_change_pct", 0)

                if change_pct > 25:
                    score += impact
                elif change_pct < -25:
                    score -= impact * 0.5
                else:
                    score += impact * 0.3  # Small position, small impact

            elif obs.source == SourceType.BROKER:
                # Broker activity (if available)
                impact = 5 * obs.freshness_score * obs.quality_score
                score += impact

        return min(max(score, 0), 100)

    def _calculate_confidence_score(self, observations: List[Observation]) -> float:
        """
        Calculate confidence score based on data quality and source diversity.

        Factors:
        - Number of unique sources (+10 per source, max +30)
        - Average quality score
        - Average freshness score
        - Cross-source verification bonus

        Args:
            observations: List of observations.

        Returns:
            Confidence score (0-100).
        """
        if not observations:
            return 20.0

        score = 40.0  # Baseline

        # Source diversity bonus
        unique_sources = set(obs.source for obs in observations)
        source_bonus = min(len(unique_sources) * 10, 30)
        score += source_bonus

        # Average quality score
        avg_quality = sum(obs.quality_score for obs in observations) / len(observations)
        score += avg_quality * 15  # Up to +15 for perfect quality

        # Average freshness score
        avg_freshness = sum(obs.freshness_score for obs in observations) / len(observations)
        score += avg_freshness * 10  # Up to +10 for perfect freshness

        # Cross-source verification bonus
        # If we have both market data and catalyst data, boost confidence
        has_market = any(
            obs.source in {SourceType.EQUITIES, SourceType.CRYPTO}
            for obs in observations
        )
        has_catalyst = any(
            obs.source in {SourceType.NEWS, SourceType.SEC, SourceType.POLYMARKET}
            for obs in observations
        )
        has_flow = any(
            obs.source in {SourceType.CONGRESS, SourceType.HEDGEFUND}
            for obs in observations
        )

        verification_count = sum([has_market, has_catalyst, has_flow])
        if verification_count >= 2:
            score += 10
        if verification_count == 3:
            score += 5

        return min(max(score, 0), 100)

    def _calculate_attention_score(
        self,
        anomaly: float,
        catalyst: float,
        flow: float,
        confidence: float,
        observations: List[Observation],
    ) -> float:
        """
        Calculate attention score from 4D scores with coverage bonus.

        Formula: 0.3*anomaly + 0.3*catalyst + 0.25*flow + 0.15*confidence + coverage_bonus
        Coverage bonus: +5 per independent source, max +20

        Args:
            anomaly: Anomaly score (0-100).
            catalyst: Catalyst score (0-100).
            flow: Flow score (0-100).
            confidence: Confidence score (0-100).
            observations: List of observations for coverage calculation.

        Returns:
            Attention score (0-100).
        """
        # Base score from 4D components
        base_score = (
            anomaly * 0.3 +
            catalyst * 0.3 +
            flow * 0.25 +
            confidence * 0.15
        )

        # Coverage bonus: +5 per independent source, max +20
        unique_sources = set(obs.source for obs in observations)
        coverage_bonus = min(
            len(unique_sources) * COVERAGE_BONUS_PER_SOURCE,
            MAX_COVERAGE_BONUS
        )

        total_score = base_score + coverage_bonus
        return min(max(total_score, 0), 100)

    def _generate_template_title(
        self,
        ticker: Optional[str],
        event_type: EventType,
        attention_score: float,
    ) -> str:
        """
        Generate a template-based title for the event.

        Format: '{symbol}: {event_type} ({attention_score})'

        Args:
            ticker: Symbol/ticker for the entity.
            event_type: Classified event type.
            attention_score: Calculated attention score.

        Returns:
            Template title string.
        """
        symbol = ticker or "Unknown"
        type_display = event_type.value.replace("_", " ").title()
        return f"{symbol}: {type_display} ({attention_score:.0f})"

    def _record_type_change(
        self,
        event: Event,
        old_type: EventType,
        new_type: EventType,
        trigger_observation_id: UUID,
    ) -> None:
        """
        Record an event type change in the history table.

        Args:
            event: The event that changed.
            old_type: Previous event type.
            new_type: New event type.
            trigger_observation_id: ID of observation that triggered the change.
        """
        history = EventTypeHistory(
            id=uuid4(),
            event_id=event.id,
            old_type=old_type.value,
            new_type=new_type.value,
            changed_at=datetime.now(timezone.utc),
            trigger_observation_id=trigger_observation_id,
        )

        try:
            self.db.insert_event_type_history(history)
            logger.debug(
                f"Recorded type change for event {event.id}: "
                f"{old_type.value} -> {new_type.value}"
            )
        except Exception as e:
            logger.warning(f"Failed to record type change: {e}")

    def create_secondary_event(
        self,
        primary_event: Event,
        observations: List[Observation],
    ) -> Event:
        """
        Create a secondary event linked to a primary event.

        Secondary events are related developments that don't warrant their own
        primary event but should be tracked separately.

        Args:
            primary_event: The primary event to link to.
            observations: Observations for the secondary event.

        Returns:
            New secondary Event object.
        """
        if not primary_event.primary_entity_id:
            raise ValueError("Primary event must have an entity_id")

        # Create event using standard method
        secondary = self._create_event(
            primary_event.primary_entity_id,
            observations,
        )

        # Link to primary
        secondary.parent_event_id = primary_event.id

        return secondary

    def persist_events(self, events: List[Event]) -> int:
        """
        Persist events to the database.

        Inserts events and links their observations in the event_observations table.

        Args:
            events: List of events to persist.

        Returns:
            Number of events persisted.
        """
        count = 0
        for event in events:
            try:
                # Insert event
                self.db.insert_event(event)

                # Link observations
                for obs_id in event.observation_ids:
                    self.db.link_observation_to_event(event.id, obs_id)

                count += 1
            except Exception as e:
                logger.error(f"Failed to persist event {event.id}: {e}")

        logger.info(f"Persisted {count}/{len(events)} events to database")
        return count
