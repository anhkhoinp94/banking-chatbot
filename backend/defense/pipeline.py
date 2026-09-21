from dataclasses import dataclass
from typing import Callable

from .classifier import InjectionClassifier
from .keyword_filter import find_keyword, load_keywords
from .output_validator import FALLBACK_MESSAGE, validate_output
from .prompt_sandwich import sandwich_prompt


@dataclass
class DefenseResult:
	answer: str
	blocked_at_layer: str | None
	label: str
	prompt: str


class DefensePipeline:
	def __init__(self, keyword_config=None, classifier=None):
		self.keywords = load_keywords(keyword_config) if keyword_config else load_keywords()
		self.classifier = classifier or InjectionClassifier()

	def process(
		self,
		message: str,
		prompt: str,
		invoke: Callable[[str], object],
		defense_config: dict[str, bool] | None = None,
	) -> DefenseResult:
		config = {"layer1": False, "layer2": False, "layer3": False}
		config.update(defense_config or {})

		if config["layer2"] and (keyword := find_keyword(message, self.keywords)):
			return DefenseResult(FALLBACK_MESSAGE, "layer2", "blocked", prompt)
		if config["layer3"] and self.classifier.predict(message):
			return DefenseResult(FALLBACK_MESSAGE, "layer3", "blocked", prompt)

		effective_prompt = sandwich_prompt(prompt) if config["layer1"] else prompt
		response = invoke(effective_prompt)
		answer = response.content if hasattr(response, "content") else str(response)
		valid, reason = validate_output(answer)
		if not valid:
			return DefenseResult(FALLBACK_MESSAGE, "output_validator", "blocked", effective_prompt)
		return DefenseResult(answer, None, "allowed", effective_prompt)
