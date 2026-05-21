
import re
from typing import Optional

_TOKEN_REGEX = re.compile(
    r"""
    ([A-Za-z]+)
    |([0-9])
    |([?-?])
    |(\S)
    """,
    re.VERBOSE,
)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    try:
        return sum(1 for _ in _TOKEN_REGEX.finditer(text))
    except Exception:
        return sum(1 for ch in text if not ch.isspace())


def calc_input_tokens(system_prompt: Optional[str], user_prompt: Optional[str]) -> int:
    sys_part = system_prompt or ""
    usr_part = user_prompt or ""
    return int(round(0.6 * estimate_tokens(sys_part + usr_part)))
