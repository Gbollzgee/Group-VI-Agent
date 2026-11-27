import re
from typing import Optional, List, Any


WORD_TO_NUM = {
    "a": 1,
    "an": 1,
    "one": 1,
    "single": 1,
    "two": 2,
    "couple": 2,
    "pair": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


class ResultCountController:
    """
    Strict Result-Count Instruction Following Controller:
    Detects requested quantities in natural language queries and enforces
    exact result limits on products, research items, lists, and recommendations.
    """

    @classmethod
    def extract_requested_count(cls, query: str, default: Optional[int] = 3) -> Optional[int]:
        """
        Extracts the requested number of items from user query.
        Handles both digits ('3', '2') and natural language expressions ('just two', 'a single option', 'no more than 4').
        Returns None or default if no specific count was requested.
        """
        if not query:
            return default

        q = query.lower().strip()

        # Pattern 1: Explicit phrases with digits or words: "just 2", "only three", "no more than 4", "top 5"
        patterns = [
            r"\b(?:give me|show me|find me|list|recommend|get|bring|provide)\s+(?:just|only|exactly)?\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a\s+single|a)\b",
            r"\b(?:just|only|exactly)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a\s+single|a)\b",
            r"\b(?:no more than|at most|up to|first|top)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b",
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:options|items|products|results|recommendations|shoes|phones|laptops|watches|websites|examples|ideas|reasons|steps|points|facts|sources|articles|universities|cars)\b",
            r"\b(a single|single|a pair of|a couple of)\b",
        ]

        for pat in patterns:
            match = re.search(pat, q)
            if match:
                raw_val = match.group(1).strip()
                if raw_val.isdigit():
                    val = int(raw_val)
                    if val > 0:
                        return min(val, 20)  # reasonable cap
                elif raw_val in WORD_TO_NUM:
                    return WORD_TO_NUM[raw_val]
                elif raw_val in ("a single", "single"):
                    return 1
                elif raw_val in ("a pair of", "a couple of", "couple of"):
                    return 2

        # Pattern 2: Standalone digit followed by item noun (e.g. "3 shoes")
        digit_match = re.search(r"\b(\d+)\s+([a-zA-Z]+)", q)
        if digit_match:
            num = int(digit_match.group(1))
            noun = digit_match.group(2)
            # Avoid parsing years (e.g. 2026, 1960) or prices (50000)
            if 1 <= num <= 20 and not (noun.startswith("year") or noun.startswith("naira") or noun.startswith("ngn") or noun.startswith("k")):
                return num

        return default

    @classmethod
    def enforce_count(cls, items: List[Any], requested_count: Optional[int]) -> List[Any]:
        """
        Strictly slices items to the exact requested count.
        Never returns more items than requested.
        """
        if requested_count is None or requested_count <= 0:
            return items
        return items[:requested_count]
