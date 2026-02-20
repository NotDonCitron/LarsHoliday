"""
Scraper Health Tracking & Adaptive Strategy Routing

Tracks success/failure metrics per scraping strategy and source,
enabling intelligent strategy selection based on recent performance.

Features:
- Per-source, per-strategy success rate tracking
- Time-windowed metrics (default: last 60 minutes)
- Adaptive strategy ordering based on performance
- Health report generation
- Persistent metrics via JSON
"""

import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ============================================================================
# STRATEGY METRICS
# ============================================================================

@dataclass
class AttemptRecord:
    """Record of a single scraping attempt."""
    timestamp: float
    source: str
    strategy: str
    success: bool
    duration_seconds: float
    result_count: int
    error: Optional[str] = None


class StrategyMetrics:
    """
    Track success/failure per scraping strategy per source.

    Stores attempt records and calculates success rates over
    configurable time windows.
    """

    def __init__(self, storage_file: str = 'scraper_metrics.json', max_records: int = 500):
        self.storage_file = storage_file
        self.max_records = max_records
        self.records: List[AttemptRecord] = []
        self._load()

    def _load(self):
        """Load metrics from disk."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.records = [
                    AttemptRecord(**rec) for rec in data.get('records', [])  # pyre-ignore[6]
                ]
            except (json.JSONDecodeError, IOError, TypeError):
                self.records = []

    def _save(self):
        """Persist metrics to disk."""
        # Trim to max records
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records:]  # pyre-ignore[6]
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {'records': [asdict(r) for r in self.records]},  # pyre-ignore[6]
                    f, indent=2
                )
        except IOError:
            pass

    def record(
        self,
        source: str,
        strategy: str,
        success: bool,
        duration: float,
        result_count: int = 0,
        error: Optional[str] = None
    ):
        """Record an attempt result."""
        attempt = AttemptRecord(
            timestamp=time.time(),
            source=source,
            strategy=strategy,
            success=success,
            duration_seconds=round(duration, 2),  # pyre-ignore[6]
            result_count=result_count,
            error=error[:200] if error else None  # pyre-ignore[6]
        )
        self.records.append(attempt)
        self._save()

    def get_recent_records(
        self,
        source: Optional[str] = None,
        strategy: Optional[str] = None,
        window_minutes: int = 60
    ) -> List[AttemptRecord]:
        """Get records within the time window, optionally filtered."""
        cutoff = time.time() - (window_minutes * 60)
        return [
            r for r in self.records
            if r.timestamp >= cutoff
            and (source is None or r.source == source)
            and (strategy is None or r.strategy == strategy)
        ]

    def get_success_rate(
        self,
        source: str,
        strategy: str,
        window_minutes: int = 60
    ) -> Tuple[float, int]:
        """
        Get success rate for a source+strategy combo.

        Returns:
            (success_rate, total_attempts) — rate is 0.0-1.0, or -1.0 if no data
        """
        records = self.get_recent_records(source, strategy, window_minutes)
        if not records:
            return -1.0, 0  # No data — unknown

        successes = sum(1 for r in records if r.success)
        return successes / len(records), len(records)

    def get_avg_duration(
        self,
        source: str,
        strategy: str,
        window_minutes: int = 60
    ) -> float:
        """Get average duration for successful attempts."""
        records = [
            r for r in self.get_recent_records(source, strategy, window_minutes)
            if r.success
        ]
        if not records:
            return 0.0
        return sum(r.duration_seconds for r in records) / len(records)

    def get_consecutive_failures(self, source: str) -> int:
        """Count consecutive failures from the most recent attempt backward."""
        source_records = [r for r in self.records if r.source == source]
        count = 0
        for record in reversed(source_records):
            if record.success:
                break
            count += 1
        return count


# ============================================================================
# ADAPTIVE ROUTER
# ============================================================================

class AdaptiveRouter:
    """
    Routes scraping requests to the best strategy based on recent metrics.

    Strategy selection logic:
    1. If a strategy has no data, try it (exploration)
    2. If a strategy has >50% success rate recently, prefer it
    3. Order by: success_rate DESC, avg_duration ASC
    4. If a source has 5+ consecutive failures, disable for cooldown
    """

    # Default strategy order when no metrics available
    DEFAULT_STRATEGIES = {
        'airbnb': ['curl-cffi', 'fallback'],  # patchright removed - not compatible with exe
        'booking': ['curl-cffi', 'fallback'],
    }

    # Cooldown: disable a source after N consecutive failures
    FAILURE_COOLDOWN_THRESHOLD = 5
    FAILURE_COOLDOWN_MINUTES = 30

    def __init__(self, metrics: StrategyMetrics):
        self.metrics = metrics

    def get_strategy_order(
        self,
        source: str,
        available_strategies: Optional[List[str]] = None
    ) -> List[str]:
        """
        Return strategies ordered by best recent performance.

        Args:
            source: The data source (e.g., 'airbnb', 'booking')
            available_strategies: List of strategy names to consider.
                If None, uses DEFAULT_STRATEGIES.

        Returns:
            Ordered list of strategy names, best first.
        """
        if available_strategies is None:
            available_strategies = self.DEFAULT_STRATEGIES.get(
                source, ['curl-cffi', 'fallback']
            )

        scored = []
        for strategy in available_strategies:
            rate, count = self.metrics.get_success_rate(source, strategy)
            avg_dur = self.metrics.get_avg_duration(source, strategy)

            # Score: high success rate and low duration are best
            if rate < 0:
                # No data — assign neutral score for exploration
                score = 0.5
            else:
                # Weight: 80% success rate + 20% speed (inverse of normalized duration)
                speed_score = max(0.0, 1.0 - (avg_dur / 60.0))  # Normalize to 60s
                score = 0.8 * rate + 0.2 * speed_score

            scored.append((strategy, score, rate, count))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Always keep 'fallback' last if present
        result = [s[0] for s in scored if s[0] != 'fallback']
        if 'fallback' in available_strategies:
            result.append('fallback')

        return result

    def should_skip_source(self, source: str) -> bool:
        """Check if a source should be temporarily disabled."""
        consecutive = self.metrics.get_consecutive_failures(source)
        if consecutive >= self.FAILURE_COOLDOWN_THRESHOLD:
            # Check if cooldown has elapsed
            source_records = [
                r for r in self.metrics.records if r.source == source
            ]
            if source_records:
                last_attempt = source_records[-1].timestamp
                cooldown_elapsed = (
                    time.time() - last_attempt
                ) > (self.FAILURE_COOLDOWN_MINUTES * 60)
                if not cooldown_elapsed:
                    return True
        return False


# ============================================================================
# HEALTH REPORT
# ============================================================================

class HealthReport:
    """Generate human-readable health reports."""

    def __init__(self, metrics: StrategyMetrics):
        self.metrics = metrics

    def generate(self, window_minutes: int = 60) -> str:
        """Generate a text health report."""
        lines = [
            "",
            "=" * 60,
            "🏥 SCRAPER HEALTH REPORT",
            f"   Window: last {window_minutes} minutes",
            f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ]

        # Group records by source
        records = self.metrics.get_recent_records(window_minutes=window_minutes)
        sources: Dict[str, Dict[str, List[AttemptRecord]]] = defaultdict(  # pyre-ignore[8]
            lambda: defaultdict(list)
        )
        for r in records:
            sources[r.source][r.strategy].append(r)

        if not sources:
            lines.append("\n   No scraping attempts recorded in this window.\n")
            return "\n".join(lines)

        for source, strategies in sorted(sources.items()):
            lines.append(f"\n📡 {source.upper()}")
            lines.append("-" * 40)

            for strategy, recs in sorted(strategies.items()):
                total = len(recs)
                successes = sum(1 for r in recs if r.success)
                rate = successes / total if total else 0
                avg_dur = sum(r.duration_seconds for r in recs) / total
                avg_results = sum(r.result_count for r in recs if r.success) / max(1, successes)

                status = "✅" if rate > 0.5 else "⚠️" if rate > 0.2 else "❌"

                lines.append(
                    f"   {status} {strategy:15s} | "
                    f"rate: {rate:5.0%} ({successes}/{total}) | "
                    f"avg: {avg_dur:5.1f}s | "
                    f"results: {avg_results:.0f}"
                )

                # Show last error if any
                errors = [r.error for r in recs if r.error]
                if errors:
                    lines.append(f"      └─ last error: {errors[-1][:60]}")  # pyre-ignore[6]

        lines.append("\n" + "=" * 60 + "\n")
        return "\n".join(lines)


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

# Shared metrics instance
scraper_metrics = StrategyMetrics()

# Shared adaptive router
adaptive_router = AdaptiveRouter(scraper_metrics)

# Shared health reporter
health_reporter = HealthReport(scraper_metrics)
