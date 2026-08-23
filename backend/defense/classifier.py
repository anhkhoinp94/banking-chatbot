import re
from pathlib import Path
from typing import Any


MODEL_PATH = Path(__file__).with_name("classifier.pkl")
HEURISTIC_PATTERNS = (
	r"ignore (all )?(previous|prior) instructions",
	r"bo qua (tat ca )?(cac )?huong dan",
	r"reveal|show|print|repeat.*(system prompt|instructions)",
	r"system prompt|developer message|internal instructions",
	r"jailbreak|dan (xuat|nhap) vai|role ?play",
)


class InjectionClassifier:
	def __init__(self, model_path: str | Path = MODEL_PATH):
		self.model_path = Path(model_path)
		self.model: Any = None
		if self.model_path.exists():
			import joblib

			self.model = joblib.load(self.model_path)

	def predict(self, message: str) -> bool:
		if self.model is not None:
			return bool(self.model.predict([message])[0] in (1, "1", "injection", "malicious"))
		return any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in HEURISTIC_PATTERNS)
