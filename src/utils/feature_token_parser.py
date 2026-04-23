from __future__ import annotations


def parse_feature_tokens(value: str | None) -> list[str] | None:
    """
    Parse feature-token strings supporting comma-separated entries and
    '+' composition (e.g. BASELINE_FEATURES+SENTIMENT_FEATURES).
    """
    if value is None:
        return None

    tokens: list[str] = []
    seen: set[str] = set()
    for chunk in str(value).split(","):
        part = chunk.strip()
        if not part:
            continue
        for raw_token in part.split("+"):
            token = raw_token.strip()
            if not token or token in seen:
                continue
            tokens.append(token)
            seen.add(token)
    return tokens or None


def normalize_feature_tokens(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None

    tokens: list[str] = []
    seen: set[str] = set()
    for value in values:
        parsed = parse_feature_tokens(str(value))
        if not parsed:
            continue
        for token in parsed:
            if token in seen:
                continue
            tokens.append(token)
            seen.add(token)
    return tokens or None
