"""
Task Memory, Evaluation & Feedback Engine — Group 6 AI Agent v2
================================================================
Provides:
1. TaskMemory       — Short-term conversation context (last N tasks)
2. EvaluationEngine — Records failures, identifies root causes, tracks fixes
3. FeedbackStore    — Persists evaluation records to disk for cross-session learning

This component enables the agent to:
- Remember context from recent interactions
- Record when tasks fail and what caused them
- Identify whether a failure pattern affects multiple capabilities
- Track whether applied fixes resolved the problem
- Provide a feedback loop for continuous improvement
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("group6.memory")

# Default storage location
_DEFAULT_STORE = Path(os.environ.get("GROUP6_DATA_DIR", Path.home() / ".group6_agent"))
_MEMORY_FILE = _DEFAULT_STORE / "task_memory.jsonl"
_EVAL_FILE = _DEFAULT_STORE / "evaluations.jsonl"
_FEEDBACK_FILE = _DEFAULT_STORE / "feedback.json"


def _ensure_dir():
    _DEFAULT_STORE.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Task Memory (short-term conversation context)
# ---------------------------------------------------------------------------
class TaskMemory:
    """
    Stores the last N tasks with their query, intent, outcome, and summary.
    Used to maintain context across consecutive user messages.
    """

    def __init__(self, max_items: int = 10):
        self._memory: List[Dict[str, Any]] = []
        self._max = max_items
        self._load()

    def _load(self):
        try:
            _ensure_dir()
            if _MEMORY_FILE.exists():
                lines = _MEMORY_FILE.read_text(encoding="utf-8").strip().split("\n")
                items = []
                for line in lines[-self._max:]:
                    try:
                        items.append(json.loads(line))
                    except Exception:
                        pass
                self._memory = items
        except Exception as e:
            logger.warning(f"TaskMemory load error: {e}")
            self._memory = []

    def record(self, query: str, intent: str, success: bool, summary: str = ""):
        """Record a completed task."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query[:500],
            "intent": intent,
            "success": success,
            "summary": summary[:300],
        }
        self._memory.append(entry)
        if len(self._memory) > self._max:
            self._memory = self._memory[-self._max:]
        # Persist
        try:
            _ensure_dir()
            with _MEMORY_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"TaskMemory persist error: {e}")

    def get_recent(self, n: int = 3) -> List[Dict[str, Any]]:
        """Get the last n tasks."""
        return self._memory[-n:] if self._memory else []

    def get_context_string(self, n: int = 3) -> str:
        """Return recent task context as a formatted string for prompt injection."""
        recent = self.get_recent(n)
        if not recent:
            return ""
        lines = ["Recent interactions:"]
        for item in recent:
            status = "✅" if item.get("success") else "❌"
            lines.append(f"  {status} [{item.get('intent', '?')}] {item.get('query', '')[:80]}")
        return "\n".join(lines)

    def clear(self):
        self._memory = []
        try:
            _MEMORY_FILE.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Evaluation Engine (failure tracking & root cause analysis)
# ---------------------------------------------------------------------------
class EvaluationEngine:
    """
    Records task failures, identifies responsible components,
    investigates root causes, and tracks whether fixes were applied.

    Principles:
    - A failure in one capability triggers investigation of related capabilities
    - Improvements are tracked and verified through subsequent test runs
    - Unverified feedback NEVER modifies production code automatically
    """

    # Map intents to the components responsible for them
    _COMPONENT_MAP = {
        "PRODUCT_SEARCH": ["product_engine", "intent_detector", "result_controller"],
        "DEEP_RESEARCH": ["research_engine", "intent_detector"],
        "EDUCATIONAL": ["educational_engine", "intent_detector"],
        "BROWSER_ACTION": ["browser", "agent_loop", "tools"],
        "GENERAL_KNOWLEDGE": ["ai_model", "research_engine"],
        "CONVERSATION": ["intent_detector"],
    }

    # Cross-domain impact map — when one component fails, what else might be affected
    _CROSS_DOMAIN_IMPACT = {
        "product_engine": ["All product categories (shoes, laptops, phones, electronics, clothing, appliances)"],
        "intent_detector": ["All task types — misclassification affects all execution paths"],
        "research_engine": ["General knowledge, current events, educational content"],
        "result_controller": ["All count-sensitive responses"],
        "browser": ["All browser-action tasks, product CDP extraction"],
        "ai_model": ["All AI-generated responses"],
    }

    def __init__(self):
        self._records: List[Dict] = []
        self._load()

    def _load(self):
        try:
            _ensure_dir()
            if _EVAL_FILE.exists():
                lines = _EVAL_FILE.read_text(encoding="utf-8").strip().split("\n")
                for line in lines[-100:]:  # Keep last 100 records
                    try:
                        self._records.append(json.loads(line))
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"EvaluationEngine load error: {e}")

    def record_failure(
        self,
        query: str,
        intent: str,
        error: str,
        component: Optional[str] = None,
        expected: str = "",
        actual: str = "",
    ) -> Dict[str, Any]:
        """
        Record a task failure and perform root cause analysis.
        Returns an evaluation record with identified issues and cross-domain impacts.
        """
        responsible_components = self._COMPONENT_MAP.get(intent, ["unknown"])
        if component and component not in responsible_components:
            responsible_components = [component] + responsible_components

        # Identify cross-domain impacts
        cross_domain = []
        for comp in responsible_components:
            impacts = self._CROSS_DOMAIN_IMPACT.get(comp, [])
            cross_domain.extend(impacts)
        cross_domain = list(set(cross_domain))

        # Pattern detection — has this type of failure happened before?
        similar_failures = [
            r for r in self._records
            if r.get("intent") == intent and not r.get("resolved")
        ]
        is_pattern = len(similar_failures) >= 2

        record = {
            "id": f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query[:500],
            "intent": intent,
            "error": error[:500],
            "responsible_components": responsible_components,
            "cross_domain_impact": cross_domain,
            "expected": expected[:300],
            "actual": actual[:300],
            "is_recurring_pattern": is_pattern,
            "similar_failure_count": len(similar_failures),
            "resolved": False,
            "resolution_notes": "",
        }

        self._records.append(record)
        try:
            _ensure_dir()
            with _EVAL_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Evaluation persist error: {e}")

        logger.warning(
            f"[EVAL] Failure recorded | Intent: {intent} | "
            f"Components: {responsible_components} | Recurring: {is_pattern}"
        )
        return record

    def record_success(self, eval_id: str, resolution: str = ""):
        """Mark an evaluation record as resolved."""
        for record in self._records:
            if record.get("id") == eval_id:
                record["resolved"] = True
                record["resolution_notes"] = resolution
                break
        self._rewrite()

    def get_unresolved(self, intent: Optional[str] = None) -> List[Dict]:
        """Get all unresolved failures, optionally filtered by intent."""
        records = [r for r in self._records if not r.get("resolved")]
        if intent:
            records = [r for r in records if r.get("intent") == intent]
        return records

    def get_summary(self) -> str:
        """Return a text summary of recent failures and patterns."""
        total = len(self._records)
        unresolved = len(self.get_unresolved())
        patterns = [r for r in self._records if r.get("is_recurring_pattern") and not r.get("resolved")]
        lines = [
            f"**Evaluation Summary:** {total} total evaluations, {unresolved} unresolved",
        ]
        if patterns:
            lines.append(f"**⚠ Recurring Patterns ({len(patterns)}):**")
            for p in patterns[-3:]:
                lines.append(f"  - [{p['intent']}] {p['query'][:60]}... → {p['error'][:60]}")
        return "\n".join(lines)

    def _rewrite(self):
        try:
            _ensure_dir()
            with _EVAL_FILE.open("w", encoding="utf-8") as f:
                for rec in self._records:
                    f.write(json.dumps(rec) + "\n")
        except Exception as e:
            logger.warning(f"Evaluation rewrite error: {e}")


# ---------------------------------------------------------------------------
# Feedback Store (user-submitted corrections)
# ---------------------------------------------------------------------------
class FeedbackStore:
    """
    Stores user feedback about incorrect or unsatisfactory responses.
    Feedback is recorded but NEVER automatically applied to production code.
    It is reviewed by the evaluation engine and tracked for manual verification.
    """

    def __init__(self):
        self._feedback: List[Dict] = []
        self._load()

    def _load(self):
        try:
            _ensure_dir()
            if _FEEDBACK_FILE.exists():
                data = json.loads(_FEEDBACK_FILE.read_text(encoding="utf-8"))
                self._feedback = data if isinstance(data, list) else []
        except Exception:
            self._feedback = []

    def record(self, query: str, issue: str, expected: str = "", severity: str = "medium") -> str:
        """
        Record user-reported feedback.
        Returns feedback ID for tracking.
        """
        fb_id = f"fb_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        entry = {
            "id": fb_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query[:500],
            "reported_issue": issue[:500],
            "expected_behavior": expected[:300],
            "severity": severity,
            "status": "pending_review",
            "auto_applied": False,  # Always False — safety guarantee
        }
        self._feedback.append(entry)
        self._persist()
        logger.info(f"[FEEDBACK] Recorded: {fb_id} | Severity: {severity} | Query: {query[:60]}")
        return fb_id

    def get_pending(self) -> List[Dict]:
        return [f for f in self._feedback if f.get("status") == "pending_review"]

    def _persist(self):
        try:
            _ensure_dir()
            _FEEDBACK_FILE.write_text(
                json.dumps(self._feedback, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"FeedbackStore persist error: {e}")


# ---------------------------------------------------------------------------
# Global singletons
# ---------------------------------------------------------------------------
task_memory = TaskMemory(max_items=20)
evaluation_engine = EvaluationEngine()
feedback_store = FeedbackStore()
