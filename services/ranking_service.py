import re


def normalize_query(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())[:300]


def highlight(text: str, query: str, size: int = 240) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return ""
    terms = [re.escape(x) for x in normalize_query(query).split() if len(x) > 1]
    if terms:
        pattern = re.compile("(" + "|".join(terms) + ")", re.I)
        match = pattern.search(clean)
        start = max(0, (match.start() if match else 0) - 70)
        clean = clean[start:start + size]
        clean = pattern.sub(r"<mark>\1</mark>", clean)
    return clean + ("…" if len(clean) >= size else "")
