import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.interview_engine.models import InterviewState


class Persistence:
    def __init__(self, base_path: str = "sessions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def save_state(self, state: InterviewState) -> str:
        session_dir = self.base_path / f"session_{state.session_id}"
        session_dir.mkdir(exist_ok=True)

        state_file = session_dir / "state.json"

        state_dict = state.model_dump()
        self._serialize_datetimes(state_dict)

        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False, default=str)

        return str(state_file)

    def load_state(self, session_id: str) -> Optional[InterviewState]:
        session_dir = self.base_path / f"session_{session_id}"
        state_file = session_dir / "state.json"

        if not state_file.exists():
            return None

        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_dict = json.load(f)

            self._deserialize_datetimes(state_dict)
            return InterviewState(**state_dict)

        except Exception as e:
            print(f"Error loading state for session {session_id}: {e}")
            return None

    def save_report(self, session_id: str, report: Dict[str, Any]) -> str:
        session_dir = self.base_path / f"session_{session_id}"
        session_dir.mkdir(exist_ok=True)

        report_file = session_dir / "report.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        return str(report_file)

    def save_raw_llm_response(
        self, session_id: str, question_id: str, raw_response: str
    ) -> str:
        session_dir = self.base_path / f"session_{session_id}"
        responses_dir = session_dir / "responses"
        responses_dir.mkdir(exist_ok=True)

        response_file = responses_dir / f"{question_id}_raw_llm.json"

        response_data = {
            "question_id": question_id,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            "raw_response": raw_response,
        }

        with open(response_file, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)

        return str(response_file)

    def list_sessions(self) -> list[str]:
        sessions = []
        for item in self.base_path.iterdir():
            if item.is_dir() and item.name.startswith("session_"):
                session_id = item.name.replace("session_", "")
                sessions.append(session_id)
        return sorted(sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        session_dir = self.base_path / f"session_{session_id}"
        if not session_dir.exists():
            return None

        state_file = session_dir / "state.json"
        report_file = session_dir / "report.json"

        info = {
            "session_id": session_id,
            "has_state": state_file.exists(),
            "has_report": report_file.exists(),
            "created": None,
            "modified": None,
        }

        if state_file.exists():
            stat = state_file.stat()
            info["created"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
            info["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return info

    def _serialize_datetimes(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, datetime):
                    obj[key] = value.isoformat()
                elif isinstance(value, (dict, list)):
                    self._serialize_datetimes(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, datetime):
                    obj[i] = item.isoformat()
                elif isinstance(item, (dict, list)):
                    self._serialize_datetimes(item)

    def _deserialize_datetimes(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and self._is_iso_datetime(value):
                    try:
                        obj[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                elif isinstance(value, (dict, list)):
                    self._deserialize_datetimes(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and self._is_iso_datetime(item):
                    try:
                        obj[i] = datetime.fromisoformat(item.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                elif isinstance(item, (dict, list)):
                    self._deserialize_datetimes(item)

    def _is_iso_datetime(self, value: str) -> bool:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except (ValueError, AttributeError):
            return False
