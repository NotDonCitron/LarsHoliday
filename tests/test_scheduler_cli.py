import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import parse_args


def test_parse_args_schedule_defaults(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--cities",
            "Amsterdam",
            "--checkin",
            "2026-03-01",
            "--checkout",
            "2026-03-05",
        ],
    )

    args = parse_args()
    assert args.schedule_minutes == 0
    assert args.max_runs == 0


def test_parse_args_schedule_custom(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--cities",
            "Amsterdam",
            "--checkin",
            "2026-03-01",
            "--checkout",
            "2026-03-05",
            "--schedule-minutes",
            "15",
            "--max-runs",
            "3",
        ],
    )

    args = parse_args()
    assert args.schedule_minutes == 15
    assert args.max_runs == 3
