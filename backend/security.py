"""Small, dependency-free API-key validation helpers."""
import hmac
from typing import Optional


def api_key_is_valid(provided: Optional[str], expected: Optional[str]) -> bool:
    """Fail closed for missing keys and compare configured keys in constant time."""
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided, expected)
