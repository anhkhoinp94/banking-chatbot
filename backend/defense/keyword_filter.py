import json
import re
import unicodedata
from pathlib import Path


DEFAULT_KEYWORD_CONFIG = Path(__file__).with_name("keywords.json")


def _normalize(value: str) -> str:
	value = unicodedata.normalize("NFKD", value)
	value = "".join(char for char in value if not unicodedata.combining(char))
	return re.sub(r"\s+", " ", value.casefold()).strip()


def load_keywords(config_path: str | Path = DEFAULT_KEYWORD_CONFIG) -> list[str]:
	with Path(config_path).open(encoding="utf-8") as config_file:
		data = json.load(config_file)
	keywords = data.get("keywords", data) if isinstance(data, dict) else data
	if not isinstance(keywords, list) or not all(isinstance(item, str) for item in keywords):
		raise ValueError("Keyword config must contain a list of strings")
	return [_normalize(item) for item in keywords if _normalize(item)]


def find_keyword(message: str, keywords: list[str] | None = None) -> str | None:
	normalized_message = _normalize(message)
	for keyword in keywords if keywords is not None else load_keywords():
		if keyword in normalized_message:
			return keyword
	return None
