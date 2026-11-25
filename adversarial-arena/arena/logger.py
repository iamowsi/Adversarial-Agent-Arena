import json
import sqlite3
from pathlib import Path
from arena.models import ArenaReport, RoundResult

class ArenaLogger:
    def __init__(self, sqlite_path: Path, jsonl_path: Path) -> None:
        self.sqlite_path = sqlite_path
        self.jsonl_path = jsonl_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, round_id INTEGER,
                    scenario TEXT, defender_down INTEGER, reasons TEXT,
                    detected_attack INTEGER, elapsed_seconds REAL, total_tokens INTEGER, created_at TEXT
                )
            """)
            conn.commit()

    def log_round(self, run_id: str, result: RoundResult) -> None:
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"run_id": run_id, "round": result.model_dump(mode="json")}) + "\n")
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                "INSERT INTO rounds (run_id, round_id, scenario, defender_down, reasons, detected_attack, elapsed_seconds, total_tokens, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (run_id, result.config.round_id, result.config.scenario, int(result.verdict.defender_down),
                 json.dumps([r.value for r in result.verdict.reasons]), int(result.verdict.defender_detected_attack),
                 result.elapsed_seconds, result.total_tokens),
            )
            conn.commit()

    def save_report(self, report: ArenaReport, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
