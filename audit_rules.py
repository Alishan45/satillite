import re

forbidden_words = [
    "delve", "tapestry", "testament", "pivotal", "underscore", "underscores", "underscoring",
    "intricate", "meticulously", "vibrant", "realm", "beacon", "multifaceted", "foster", "fosters", "fostering",
    "showcase", "showcases", "showcasing", "bolster", "bolsters", "garner", "interplay", "enduring",
    "crucial", "vital", "landscape", "dynamic", "nuanced", "watershed moment", "turning point",
    "deeply rooted", "rich heritage", "steadfast", "paradigm", "synergy", "leverage",
    "moreover", "furthermore", "in addition", "consequently", "nonetheless",
    "it is important to note", "it is worth mentioning", "notably", "crucially", "in today's fast-paced world",
    "studies show", "experts say", "researchers argue", "observers note",
    "groundbreaking", "breathtaking", "remarkable", "seamless", "transformative", "revolutionary",
    "in conclusion", "to summarize", "overall,"
]

banned_patterns = [
    (r"\bnot only\b", "Negative parallelism ('not only')"),
    (r"\bnot just\b", "Negative parallelism ('not just')"),
    (r"\brather than\b", "Negative parallelism ('rather than')"),
    (r"—", "Em dash"),
    (r"\bserves as\b", "Inflated copulative ('serves as')"),
    (r"\bstands as\b", "Inflated copulative ('stands as')"),
    (r"\brepresents\b", "Inflated copulative ('represents')"),
    (r"\bmarks\b", "Inflated copulative ('marks')"),
    (r"\bboasts\b", "Inflated copulative ('boasts')"),
    (r"\bfeatures\b", "Inflated copulative ('features')"),
    (r",\s+[a-z]+ing\b", "Trailing -ing clause"),
    (r"\*\*[^*]+:\*\*", "Bold term bullet format")
]

def audit(text):
    text_lower = text.lower()
    errors = []
    for word in forbidden_words:
        matches = list(re.finditer(rf"\b{re.escape(word)}\b", text_lower))
        for m in matches:
            errors.append(f"Forbidden word/phrase found: '{word}' at index {m.start()}")
    for pat, desc in banned_patterns:
        matches = list(re.finditer(pat, text_lower if pat != r"—" else text))
        for m in matches:
            snippet = text[max(0, m.start()-20):min(len(text), m.end()+20)].replace('\n', ' ')
            errors.append(f"{desc}: matched '{m.group(0)}' in context: '...{snippet}...'")
    return errors

if __name__ == "__main__":
    print("Audit tool defined.")
