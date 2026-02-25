"""
Lightweight observability and KPI tracking.

Provides:
- run IDs for each search execution
- structured JSON log events
- per-run counters/attributes
- in-memory snapshots for API health checks
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional


@dataclass
class RunState:
    """State container for one tracked run."""

    run_id: str
    component: str
    started_at: float
    params: Dict[str, Any] = field(default_factory=dict)
    counters: Dict[str, float] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    ended_at: Optional[float] = None
    status: str = "running"

    def to_summary(self) -> Dict[str, Any]:
        """Serialize a stable summary payload for UI/API output."""
        ended_at_value = self.ended_at
        if ended_at_value is not None:
            end_ts = float(ended_at_value)
            ended_at_iso = datetime.fromtimestamp(end_ts).isoformat()
        else:
            end_ts = float(time.time())
            ended_at_iso = None

        started_at = float(self.started_at)
        duration = max(0.0, end_ts - started_at)

        return {
            "run_id": self.run_id,
            "component": self.component,
            "status": self.status,
            "started_at": datetime.fromtimestamp(started_at).isoformat(),
            "ended_at": ended_at_iso,
            "duration_seconds": float(f"{duration:.2f}"),
            "params": self.params,
            "counters": self.counters,
            "attributes": self.attributes,
        }


class ObservabilityTracker:
    """Thread-safe in-memory tracker with structured event logging."""

    def __init__(self, max_history: int = 200):
        self.max_history = max_history
        self._active_runs: Dict[str, RunState] = {}
        self._history: List[Dict[str, Any]] = []
        self._lock = Lock()

    def start_run(self, component: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Start a new run and return its run id."""
        run_id_raw = uuid.uuid4().hex
        run_id = "".join(run_id_raw[i] for i in range(12))
        state = RunState(
            run_id=run_id,
            component=component,
            started_at=time.time(),
            params=params or {},
        )
        with self._lock:
            self._active_runs[run_id] = state
        self.event(run_id, "run_started", component=component)
        return run_id

    def event(self, run_id: str, event: str, **fields: Any) -> None:
        """Emit a structured JSON log line for a run event."""
        payload = {
            "timestamp": datetime.now().isoformat(),
            "run_id": run_id,
            "event": event,
            **fields,
        }
        try:
            print(f"[OBS] {json.dumps(payload, ensure_ascii=False, default=str)}")
        except Exception:
            print(f"[OBS] run_id={run_id} event={event}")

    def incr(self, run_id: str, key: str, value: float = 1.0) -> None:
        """Increment a numeric counter for a run."""
        with self._lock:
            state = self._active_runs.get(run_id)
            if not state:
                return
            state.counters[key] = float(state.counters.get(key, 0.0) + value)

    def set_attr(self, run_id: str, key: str, value: Any) -> None:
        """Set or overwrite an attribute on the active run."""
        with self._lock:
            state = self._active_runs.get(run_id)
            if not state:
                return
            state.attributes[key] = value

    def end_run(self, run_id: str, status: str = "ok", **final_attrs: Any) -> Dict[str, Any]:
        """Finish an active run and return its summary."""
        with self._lock:
            state = self._active_runs.pop(run_id, None)
            if not state:
                return {}

            state.ended_at = time.time()
            state.status = status
            if final_attrs:
                state.attributes.update(final_attrs)
            summary = state.to_summary()
            self._history.append(summary)
            while len(self._history) > self.max_history:
                self._history.pop(0)

        self.event(run_id, "run_finished", status=status, duration_seconds=summary.get("duration_seconds", 0))
        return summary

    def snapshot(self) -> Dict[str, Any]:
        """Return a compact snapshot for health endpoints."""
        with self._lock:
            active_summaries = [state.to_summary() for state in self._active_runs.values()]
            recent: List[Dict[str, Any]] = []
            history_len = len(self._history)
            start_idx = history_len - 10 if history_len > 10 else 0
            idx = start_idx
            while idx < history_len:
                recent.append(self._history[idx])
                idx += 1

        return {
            "active_runs": len(active_summaries),
            "recent_runs": recent,
            "currently_running": active_summaries,
        }


observability_tracker = ObservabilityTracker()
