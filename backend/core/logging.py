import json
import os
from datetime import datetime, timezone


class RequestLogger:
    def __init__(self, file_path="logs/chat_logs.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def log(
        self,
        prompt_id,
        defense_config,
        blocked_at_layer,
        response,
        label,
    ):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_id": prompt_id,
            "defense_config": defense_config,
            "blocked_at_layer": blocked_at_layer,
            "response": response,
            "label": label,
        }

        logs = []

        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
