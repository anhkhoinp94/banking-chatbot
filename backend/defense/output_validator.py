import re


FALLBACK_MESSAGE = "Tôi không thể cung cấp câu trả lời đó."
SYSTEM_PROMPT_PATTERNS = (
	r"system prompt",
	r"developer message",
	r"chỉ được trả lời dựa trên",
	r"CONTEXT:.*QUESTION:",
)
FORBIDDEN_PATTERNS = (
	r"hướng dẫn (hack|tấn công|xâm nhập)",
	r"mã độc|ransomware|phishing",
	r"ma túy|vũ khí|buôn người",
)


def validate_output(answer: str) -> tuple[bool, str | None]:
	for pattern in SYSTEM_PROMPT_PATTERNS:
		if re.search(pattern, answer, flags=re.IGNORECASE | re.DOTALL):
			return False, "output_system_prompt_leak"
	for pattern in FORBIDDEN_PATTERNS:
		if re.search(pattern, answer, flags=re.IGNORECASE | re.DOTALL):
			return False, "output_forbidden_topic"
	return True, None
