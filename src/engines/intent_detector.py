import re
from typing import Dict, Any, Optional
from src.engines.result_controller import ResultCountController


class IntentDetector:
    """
    Intelligent Intent Detection Engine:
    Accurately classifies incoming user queries into specialized operational modes:
    - PRODUCT_SEARCH: E-commerce shopping & price retrieval (Jumia, Konga, etc.)
    - DEEP_RESEARCH: Complex multi-source internet research, current events, comparative analysis
    - EDUCATIONAL: Explaining technical concepts, programming, math, science, tutorials
    - GENERAL_KNOWLEDGE: Direct facts, history, geography, definitions
    - BROWSER_ACTION: Real browser actions (open WhatsApp, register on website, click, fill forms)
    - CONVERSATION: Casual greeting, assistant identity, pleasantries
    """

    @classmethod
    def detect(cls, query: str) -> Dict[str, Any]:
        q_raw = query.strip()
        q_lower = q_raw.lower()

        # Extract strict result count if requested
        requested_count = ResultCountController.extract_requested_count(q_raw, default=None)

        # 1. Casual / Greetings
        if q_lower in ("hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you", "who are you", "what can you do"):
            return {
                "intent": "CONVERSATION",
                "target_site": "none",
                "clean_topic": q_raw,
                "requested_count": requested_count,
                "ack": "Hello! I am your Group 6 AI Assistant. How can I help you today?"
            }

        # 2. Deep Research & In-depth Analysis (takes priority over shopping if research is requested)
        research_triggers = ["research", "current affairs", "what is happening", "economy of", "history of", "latest developments", "compare", "analysis", "why is", "overview of", "who is the current president"]
        if any(trig in q_lower for trig in research_triggers) or (q_lower.startswith("research ") or "in-depth" in q_lower):
            return {
                "intent": "DEEP_RESEARCH",
                "target_site": "web",
                "clean_topic": q_raw,
                "requested_count": requested_count,
                "ack": "Conducting deep multi-source research across authoritative databases."
            }

        # 3. Explicit Live Browser Navigation / App Interaction (User wants a site opened or interactive task)
        browser_triggers = ["open whatsapp", "navigate to jumia website for registration", "open youtube", "visit website", "sign up", "signup", "register on", "login to", "log in to", "click on", "type into"]
        if any(trig in q_lower for trig in browser_triggers) or (q_lower.startswith("open ") and any(site in q_lower for site in ["whatsapp", "youtube", "twitter", "facebook", "gmail", "github", "portal"])):
            return {
                "intent": "BROWSER_ACTION",
                "target_site": "web",
                "clean_topic": q_raw,
                "requested_count": requested_count,
                "ack": "Launching the live browser to execute this action for you right away."
            }

        # 4. Product Search Intent (Jumia, shopping, products, shoes, phones, laptops, prices)
        product_keywords = ["jumia", "konga", "amazon", "buy ", "purchase", "shopping", "price of", "prices of", "shoes", "sneakers", "laptop", "laptops", "phone", "phones", "smartphone", "smartphones", "watches", "tvs", "earbuds", "headphones"]
        has_product_kw = any(k in q_lower for k in product_keywords)
        is_shopping_action = any(v in q_lower for v in ["find me ", "show me ", "give me ", "search for ", "list ", "recommend "]) and has_product_kw
        has_jumia = "jumia" in q_lower

        if has_jumia or is_shopping_action or (has_product_kw and any(p in q_lower for p in ["under ", "below ", "cost", "affordable", "cheap"])):
            target = "jumia" if ("jumia" in q_lower or not ("konga" in q_lower or "amazon" in q_lower)) else "web"
            return {
                "intent": "PRODUCT_SEARCH",
                "target_site": target,
                "clean_topic": q_raw,
                "requested_count": requested_count or 3,
                "ack": f"Starting verified product discovery on Jumia Nigeria."
            }

        # 5. Educational / Technical Assistance Intent
        edu_triggers = ["how do apis work", "what is an api", "api", "database normalization", "python programming", "write code", "tutorial", "algorithm", "data structure", "machine learning", "neural network", "sql", "git"]
        if any(trig in q_lower for trig in edu_triggers):
            return {
                "intent": "EDUCATIONAL",
                "target_site": "none",
                "clean_topic": q_raw,
                "requested_count": requested_count,
                "ack": "Understood. Preparing a comprehensive educational explanation with practical examples."
            }

        # 6. Default General Knowledge / Direct Inquiry
        return {
            "intent": "GENERAL_KNOWLEDGE",
            "target_site": "none",
            "clean_topic": q_raw,
            "requested_count": requested_count,
            "ack": "Processing your inquiry and synthesizing an authoritative response."
        }
