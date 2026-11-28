"""
Universal Intent Classifier & Task Planner — Group 6 AI Agent v2
================================================================
Replaces the keyword-based IntentDetector with a two-layer system:

Layer 1: Fast LLM-based classification (handles unfamiliar queries gracefully)
Layer 2: Task decomposition for complex multi-step goals

Intent types:
  PRODUCT_SEARCH    — Find / compare / verify products on e-commerce sites
  DEEP_RESEARCH     — Multi-source internet research on any topic
  EDUCATIONAL       — Explain concepts, teach, provide tutorials
  BROWSER_ACTION    — Navigate a website, fill forms, perform automated actions
  CONVERSATION      — Greetings, identity questions, capabilities
  GENERAL_KNOWLEDGE — Direct factual/knowledge questions needing no live search
"""

import re
import logging
import asyncio
from typing import Dict, Any, Optional, List

from src.engines.result_controller import ResultCountController

logger = logging.getLogger("group6.planner")


# ---------------------------------------------------------------------------
# Fast keyword signals (run synchronously; LLM is the fallback)
# ---------------------------------------------------------------------------
_CONVERSATION_EXACT = {
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    "how are you", "who are you", "what can you do", "what are you",
    "introduce yourself",
}

_RESEARCH_SIGNALS = [
    "research", "latest news", "current affairs", "what is happening",
    "who is the current", "who is the president", "who is the governor",
    "who is the ceo", "history of", "explain the history",
    "economy of", "gdp of", "population of", "analysis of",
    "compare the best", "compare and contrast", "overview of",
    "developments in", "trends in", "in-depth", "investigate",
    "find out about", "tell me about the latest", "today in",
    "news about", "what happened to", "how is the economy",
]

_BROWSER_SIGNALS = [
    "open whatsapp", "open youtube", "open twitter", "open instagram",
    "open facebook", "open gmail", "open github", "open google",
    "navigate to", "go to the website", "visit the website",
    "sign up on", "sign up for", "register on", "register at",
    "login to", "log in to", "log into", "click on",
    "fill in", "type in the", "submit the form",
    "download from", "upload to", "open the app",
]

_PRODUCT_SIGNALS = [
    "find me", "show me", "get me", "give me", "search for",
    "i want to buy", "i need to buy", "where can i buy",
    "how much does", "price of", "prices of", "cost of",
    "cheap", "affordable", "under ₦", "under n", "below ₦", "below n",
    "best deals", "discount on", "sale on",
]

_PRODUCT_CATEGORIES = [
    "shoe", "shoes", "sneaker", "sneakers", "boot", "boots", "sandal",
    "laptop", "laptops", "computer", "pc", "macbook",
    "phone", "phones", "smartphone", "smartphones", "iphone", "android",
    "tv", "television", "monitor", "screen",
    "watch", "watches", "smartwatch",
    "headphone", "headphones", "earphone", "earbuds", "speaker",
    "fridge", "refrigerator", "washing machine", "air conditioner", "ac",
    "blender", "microwave", "oven", "cooker",
    "shirt", "trouser", "dress", "cloth", "clothing", "fashion",
    "bag", "backpack", "handbag", "purse",
    "book", "textbook",
    "camera", "lens", "tripod",
    "charger", "cable", "power bank",
]

_MARKETPLACE_NAMES = [
    "jumia", "konga", "jiji", "amazon", "ebay", "aliexpress",
    "noon", "kilimall", "slot", "computer village",
]

_EDU_SIGNALS = [
    "explain", "how does", "what is", "what are", "how do",
    "teach me", "tutorial on", "guide to", "introduction to",
    "step by step", "example of", "examples of", "code for",
    "write a", "create a", "build a", "implement",
    "algorithm for", "how to code", "how to program",
    "difference between", "pros and cons of",
]

_EDU_TOPICS = [
    "api", "algorithm", "database", "sql", "python", "javascript",
    "machine learning", "neural network", "deep learning", "ai",
    "data structure", "sorting", "recursion", "object oriented",
    "cloud computing", "networking", "cybersecurity", "blockchain",
    "git", "docker", "kubernetes", "microservices", "rest",
    "normalization", "foreign key", "primary key", "index",
]


class IntentDetector:
    """
    Universal Intent Classifier.
    Uses fast keyword matching first; falls back to LLM classification
    for queries that cannot be reliably classified by rules alone.
    """

    @classmethod
    def detect(cls, query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Classify query synchronously using keyword rules (fast path)."""
        return cls._keyword_classify(query)

    @classmethod
    async def detect_async(cls, query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify query using keywords first; use LLM if ambiguous.
        Returns full intent dict with confidence.
        """
        result = cls._keyword_classify(query)
        if result.get("confidence", "high") == "low" and api_key:
            try:
                llm_result = await cls._llm_classify(query, api_key)
                result.update(llm_result)
            except Exception as e:
                logger.warning(f"LLM classification failed, using keyword result: {e}")
        return result

    @classmethod
    def _keyword_classify(cls, query: str) -> Dict[str, Any]:
        q_raw = query.strip()
        q_lower = q_raw.lower()

        # Extract result count
        requested_count = ResultCountController.extract_requested_count(q_raw, default=None)

        # Helper for whole-word boundary matching
        def has_word(pattern_list: List[str], text: str) -> bool:
            for p in pattern_list:
                if re.search(r"\b" + re.escape(p) + r"\b", text):
                    return True
            return False

        # 1. Casual / Greetings (takes top priority)
        greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "how are you", "who are you", "what can you do", "what are you",
            "introduce yourself", "how do you do", "nice to meet you"
        ]
        if has_word(greetings, q_lower) or any(q_lower.startswith(g) for g in ["hello", "hi ", "hey ", "good "]):
            return cls._make(
                "CONVERSATION", q_raw, requested_count,
                "Hello! I'm your Group 6 Autonomous AI Agent. How can I assist you today?",
                confidence="high"
            )

        # 2. Deep Research (high-priority — catches "who is the current X", "history of", etc.)
        if any(sig in q_lower for sig in _RESEARCH_SIGNALS):
            return cls._make(
                "DEEP_RESEARCH", q_raw, requested_count,
                "Initiating multi-source internet research across authoritative databases.",
                confidence="high"
            )

        # 3. Browser Action (explicit navigation / site interaction)
        if any(sig in q_lower for sig in _BROWSER_SIGNALS):
            return cls._make(
                "BROWSER_ACTION", q_raw, requested_count,
                "Launching browser to execute this task on the target website.",
                confidence="high"
            )

        # 4. Product Search (using strict word boundary matching)
        has_product_cat = has_word(_PRODUCT_CATEGORIES, q_lower)
        has_marketplace = has_word(_MARKETPLACE_NAMES, q_lower)
        has_shopping_action = any(sig in q_lower for sig in _PRODUCT_SIGNALS) and has_product_cat
        has_price_signal = any(p in q_lower for p in ["price", "cost", "how much", "cheap", "affordable", "buy"])

        if has_marketplace or has_shopping_action or (has_product_cat and has_price_signal):
            target = "jumia"
            for m in _MARKETPLACE_NAMES:
                if re.search(r"\b" + re.escape(m) + r"\b", q_lower):
                    target = m
                    break
            return cls._make(
                "PRODUCT_SEARCH", q_raw, requested_count or 3,
                f"Starting verified product discovery on {'Jumia Nigeria' if target == 'jumia' else target.title()}.",
                confidence="high",
                extra={"target_marketplace": target}
            )

        # 5. Educational / Technical (requires whole-word topic matching to avoid 'api' matching 'capital')
        has_edu_signal = any(sig in q_lower for sig in _EDU_SIGNALS)
        has_edu_topic = has_word(_EDU_TOPICS, q_lower)
        if (has_edu_signal and has_edu_topic) or ("explain how" in q_lower and len(q_lower) > 20):
            return cls._make(
                "EDUCATIONAL", q_raw, requested_count,
                "Preparing a structured educational explanation with practical examples.",
                confidence="high"
            )

        # 6. General factual question
        factual_starts = ["what is", "who is", "where is", "when was", "how many", "which is",
                          "what was", "who was", "what does", "define", "meaning of"]
        if any(q_lower.startswith(fs) for fs in factual_starts):
            return cls._make(
                "GENERAL_KNOWLEDGE", q_raw, requested_count,
                "Synthesizing an authoritative response from knowledge base.",
                confidence="medium"
            )

        # 7. Low-confidence fallback — might need LLM disambiguation
        # If it mentions product-category words alone, still try product search
        if has_product_cat:
            return cls._make(
                "PRODUCT_SEARCH", q_raw, requested_count or 3,
                "Starting product discovery and verification.",
                confidence="medium",
                extra={"target_marketplace": "jumia"}
            )

        return cls._make(
            "GENERAL_KNOWLEDGE", q_raw, requested_count,
            "Processing your inquiry and formulating an authoritative response.",
            confidence="low"
        )

    @classmethod
    async def _llm_classify(cls, query: str, api_key: str) -> Dict[str, Any]:
        """Use Gemini to classify ambiguous queries."""
        from google import genai
        import asyncio

        client = genai.Client(api_key=api_key)
        prompt = f"""Classify this user query into exactly one of these categories:
PRODUCT_SEARCH, DEEP_RESEARCH, EDUCATIONAL, BROWSER_ACTION, GENERAL_KNOWLEDGE, CONVERSATION

Query: "{query}"

Respond with ONLY the category name, nothing else."""

        for model in ["gemini-flash-lite-latest", "gemini-3.5-flash-lite"]:
            try:
                res = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=prompt,
                )
                if res and res.text:
                    intent = res.text.strip().upper().split()[0]
                    valid = {"PRODUCT_SEARCH", "DEEP_RESEARCH", "EDUCATIONAL",
                             "BROWSER_ACTION", "GENERAL_KNOWLEDGE", "CONVERSATION"}
                    if intent in valid:
                        return {"intent": intent, "confidence": "llm"}
            except Exception:
                continue
        return {}

    @classmethod
    def _make(cls, intent: str, query: str, count, ack: str,
              confidence: str = "high", extra: dict = None) -> Dict[str, Any]:
        result = {
            "intent": intent,
            "clean_topic": query,
            "requested_count": count,
            "ack": ack,
            "confidence": confidence,
        }
        if extra:
            result.update(extra)
        return result


class TaskPlanner:
    """
    Decomposes complex multi-step goals into an ordered list of sub-tasks.
    Used when the query involves multiple operations or decision branches.
    """

    @staticmethod
    async def decompose(goal: str, api_key: str) -> List[Dict[str, Any]]:
        """
        Breaks a complex goal into ordered steps.
        Each step has: step_num, description, intent, requires_browser
        Returns list of steps, or single step if goal is simple.
        """
        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = f"""You are a task planner for an autonomous AI web agent.

Analyze this goal and determine whether it requires multiple distinct steps or is a single task.

Goal: "{goal}"

If it is a SINGLE task, respond with:
SINGLE: <brief description>

If it requires MULTIPLE steps, list them as:
STEP 1: <description> | TYPE: <RESEARCH|BROWSE|PRODUCT|KNOWLEDGE>
STEP 2: <description> | TYPE: <RESEARCH|BROWSE|PRODUCT|KNOWLEDGE>
(maximum 5 steps)

Be concise. Only split when genuinely necessary."""

        for model in ["gemini-flash-lite-latest", "gemini-3.5-flash-lite"]:
            try:
                res = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=prompt,
                )
                if res and res.text:
                    return TaskPlanner._parse_plan(res.text.strip(), goal)
            except Exception as e:
                logger.warning(f"Task planning model {model} failed: {e}")
                continue

        return [{"step_num": 1, "description": goal, "type": "GENERAL", "requires_browser": False}]

    @staticmethod
    def _parse_plan(text: str, original_goal: str) -> List[Dict[str, Any]]:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return [{"step_num": 1, "description": original_goal, "type": "GENERAL"}]

        if lines[0].upper().startswith("SINGLE:"):
            return [{"step_num": 1, "description": original_goal, "type": "GENERAL"}]

        steps = []
        for line in lines:
            m = re.match(r"STEP\s+(\d+):\s*(.+?)\s*\|\s*TYPE:\s*(\w+)", line, re.IGNORECASE)
            if m:
                step_type = m.group(3).upper()
                steps.append({
                    "step_num": int(m.group(1)),
                    "description": m.group(2).strip(),
                    "type": step_type,
                    "requires_browser": step_type in ("BROWSE", "PRODUCT"),
                })
        return steps if steps else [{"step_num": 1, "description": original_goal, "type": "GENERAL"}]
