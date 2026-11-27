def normalize_text(text: str) -> str:
    if not text:
        return ""

    return "".join(" " if char.isspace() else char for char in text)
