from fnmatch import fnmatch


def match(name: str, patterns: list[tuple[str, bool]]) -> tuple[bool, bool]:
    """Check if name matches patterns (gitignore-style, last match wins).

    Args:
        name: string to match
        patterns: list of (pattern, excluded) tuples

    Returns:
        (matched, excluded) tuple
        - matched: True if name matches any pattern
        - excluded: True if the last matching pattern is an exclusion
    """
    matched = False
    excluded = False
    for pattern, is_excluded in patterns:
        if fnmatch(name, pattern):
            matched = True
            excluded = is_excluded
    return matched, excluded


def match_any(name: str, patterns: list[tuple[str, bool]]) -> bool:
    """Check if name matches any allowed pattern (not excluded).

    Args:
        name: string to match
        patterns: list of (pattern, excluded) tuples

    Returns:
        True if name matches an allowed (non-excluded) pattern
    """
    matched, excluded = match(name, patterns)
    return matched and not excluded
