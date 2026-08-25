import re


def tokenize(text: str) -> list[str]:
    return re.findall(r"[\w]{2,}", (text or "").lower())
