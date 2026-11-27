import os
import asyncio
import logging
from typing import Optional, Dict, Any
from google import genai

from src.engines.result_controller import ResultCountController

logger = logging.getLogger("group6.education")


class EducationalEngine:
    """
    Educational & Technical Assistant Engine:
    Provides crystal-clear, structured technical explanations with practical examples,
    code snippets, analogies, and best practices.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")

    async def explain(self, topic: str, requested_count: Optional[int] = None) -> Dict[str, Any]:
        count_instruction = ""
        if requested_count is not None and requested_count > 0:
            count_instruction = f"\nStrict Result Count: Provide EXACTLY {requested_count} examples, steps, or principles as requested.\n"

        prompt = (
            "You are the Group 6 Autonomous AI Educational & Technical Assistant.\n"
            "Provide a comprehensive, high-clarity educational explanation of the topic below.\n\n"
            "Structure your response with:\n"
            "1. **Core Concept & Definition**: Clear, jargon-free introduction.\n"
            "2. **Real-World Analogy**: Relatable analogy to cement understanding.\n"
            "3. **How It Works (Step-by-Step Architecture)**: Key components and flow.\n"
            "4. **Concrete Practical Example(s)**: Real code, payload, or architectural diagram (use markdown code blocks).\n"
            "5. **Best Practices & Key Takeaways**: Production tips and common pitfalls to avoid.\n"
            f"{count_instruction}\n"
            f"Topic: \"{topic}\""
        )

        client = genai.Client(api_key=self.api_key)
        content = ""
        for m in ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash-lite"]:
            try:
                res = await asyncio.to_thread(
                    client.models.generate_content,
                    model=m,
                    contents=prompt,
                )
                if res and res.text:
                    content = res.text.strip()
                    break
            except Exception as e:
                logger.warning(f"Educational model {m} failed: {e}")

        if not content:
            content = f"### Educational Overview: {topic}\n\nUnable to generate full tutorial at this moment."

        spoken_summary = f"Here is a comprehensive breakdown of {topic} with practical examples and core concepts displayed on your screen."

        return {
            "success": True,
            "topic": topic,
            "content": content,
            "summary": spoken_summary,
        }
