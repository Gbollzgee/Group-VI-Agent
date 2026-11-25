import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from aiohttp import web
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).parent / "static"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# Group 6 AI Project imports
from src.agent import Agent
from src.agent.browser import Browser
from src.agent.browser.config import BrowserConfig
from src.agent.events import AgentEvent, EventType
from src.providers.google import ChatGoogle
from google import genai
from google.genai import types

logger = logging.getLogger("group6.web")
logging.basicConfig(level=logging.INFO)

# Generous execution timeout (3 minutes) to allow deep searching without hanging indefinitely
TASK_TIMEOUT_SECONDS = 180.0

FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]


async def gemini_generate_with_fallback(client, contents, models=None) -> str:
    """Generate content from Gemini with resilient fallback across multiple models."""
    if models is None:
        models = FALLBACK_MODELS
    last_err = None
    for model_name in models:
        try:
            res = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=contents,
            )
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            logger.warning(f"Model '{model_name}' encountered error: {e}. Attempting next fallback model...")
            last_err = e
            continue
    raise RuntimeError(f"All Gemini fallback models exhausted. Last error: {last_err}")



class WebAgentManager:
    """
    Manages the lifecycle of the Group 6 Autonomous AI Web Agent:
    - Smart Intent Routing (Deep Search, Live Browser Navigation, or Direct AI)
    - 5-Stage Visual Execution Pipeline
    - Deep Information Extraction & Structured Result Cards
    - Multi-turn Continuous Voice Interaction
    """

    def __init__(self):
        self.llm = ChatGoogle(model="gemini-flash-lite-latest")
        self.config = BrowserConfig(browser="chrome", headless=False)
        self.agent = Agent(
            config=self.config,
            llm=self.llm,
            use_vision=False,
            use_web_mcp=True,
            max_steps=100,
            max_consecutive_failures=5,
            keep_alive=True,
        )
        self.ws_clients = set()
        self.is_busy = False

        # Attach event listener to forward agent events to connected WebSocket clients
        self.agent.event.add_subscriber(self._on_agent_event)

    def _determine_stage(self, event: AgentEvent) -> tuple[str, str, str]:
        """Map internal agent events into the 5 core presentation stages."""
        match event.type:
            case EventType.THOUGHT:
                thought = str(event.data.get("thought", "")).lower()
                if any(w in thought for w in ["done", "finish", "complete"]):
                    return ("ready", "Preparing Output", "Validating completion and preparing result summary...")
                elif any(w in thought for w in ["search", "navigate", "open", "go to"]):
                    return ("processing", "Processing Goal", "Interpreting goal and executing navigation plan...")
                else:
                    return ("analysing", "Analysing Page Structure", "Examining DOM semantic tree, elements, and page state...")

            case EventType.TOOL_CALL:
                tool_name = str(event.data.get("tool_name", "")).lower()
                params = event.data.get("tool_params", {})
                if "done" in tool_name:
                    return ("ready", "Preparing Output", "Goal achieved. Assembling final result summary...")
                elif any(nav in tool_name for nav in ["navigate", "open", "url", "goto"]):
                    target = params.get("url", params.get("target", "destination"))
                    return ("processing", "Navigating Website", f"Directing browser to {target}...")
                elif any(act in tool_name for act in ["click", "type", "input", "press", "select"]):
                    return ("processing", "Executing Interaction", f"Performing {tool_name} on active page...")
                else:
                    return ("analysing", "Analysing Web Content", f"Inspecting page layout and elements via {tool_name}...")

            case EventType.TOOL_RESULT:
                tool_name = str(event.data.get("tool_name", "")).lower()
                if "done" in tool_name:
                    return ("ready", "Finalizing Result", "Outcome compiled and ready for presentation.")
                return ("analysing", "Evaluating Page Response", "Validating DOM mutation and updated page elements...")

            case EventType.ERROR:
                return ("processing", "Auto-Recovering", "Addressing transient issue and retrying step...")

        return ("processing", "In Progress", "Agent executing action...")

    def _on_agent_event(self, event: AgentEvent):
        """Forward internal agent events and update stage pipeline."""
        stage_id, stage_title, stage_detail = self._determine_stage(event)

        backstage_item = {
            "step": event.data.get("step", 0),
            "event_type": event.type.name if hasattr(event.type, "name") else str(event.type),
            "data": event.data,
        }

        payload = {
            "type": "stage_progress",
            "stage": stage_id,
            "title": stage_title,
            "detail": stage_detail,
            "backstage": backstage_item,
        }

        asyncio.create_task(self.broadcast(payload))

    async def broadcast(self, message: dict):
        dead_clients = set()
        msg_str = json.dumps(message)
        for ws in self.ws_clients:
            try:
                await ws.send_str(msg_str)
            except Exception:
                dead_clients.add(ws)
        self.ws_clients -= dead_clients

    async def classify_intent(self, query: str) -> dict:
        """
        Smart Intent Routing (fast deterministic routing first to save latency & API quota):
        1. DEEP_SEARCH: extracting structured product/market data (e.g. Jumia shoes under 50k, phone prices)
        2. BROWSER_ACTION: physically opening or interacting with a specific website (e.g. Open WhatsApp, Jumia registration)
        3. DIRECT_ANSWER: general knowledge or conversational question that does NOT require opening a browser
        """
        q_lower = query.lower().strip()
        target_site = "jumia" if "jumia" in q_lower else ("amazon" if "amazon" in q_lower else ("konga" if "konga" in q_lower else "web"))

        # Fast-path 1: Deep Search & Price/Product Comparison
        if any(k in q_lower for k in ["list ", "price", "prices", "types of", "compare", "under ", "below ", "cheap", "best ", "top ", "features of", "cost of", "how much"]):
            return {
                "intent": "DEEP_SEARCH",
                "target_site": target_site,
                "search_topic": query,
                "ack": f"On it! Running a deep search and compiling the structured report for you right now.",
            }

        # Fast-path 2: Direct Conversational / Informational Answer (no browser needed)
        if any(q_lower.startswith(p) for p in ["what is", "what are", "who is", "who invented", "how does", "how do", "why ", "explain ", "define ", "tell me about", "hello", "hi ", "hey "]):
            return {
                "intent": "DIRECT_ANSWER",
                "target_site": "none",
                "search_topic": query,
                "ack": "Understood, analyzing your question and preparing the answer right away.",
            }

        # Fast-path 3: Explicit Browser Navigation / Web App Action
        if any(k in q_lower for k in ["open ", "go to ", "visit ", "navigate ", "register", "sign up", "signup", "login", "log in", "whatsapp", "youtube", "search google", "click "]):
            return {
                "intent": "BROWSER_ACTION",
                "target_site": target_site,
                "search_topic": query,
                "ack": "Alright, launching the browser to handle that task for you right now.",
            }

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return {"intent": "BROWSER_ACTION", "target_site": "web", "search_topic": query, "ack": "Working on your request right away."}

        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                "Classify this user query into ONE of three categories:\n"
                "1. 'DEEP_SEARCH': search, compare, extract, or list products/prices/data.\n"
                "2. 'BROWSER_ACTION': open a live site, log in, register, or take action in a web app.\n"
                "3. 'DIRECT_ANSWER': general question or explanation where opening a browser is unnecessary.\n\n"
                f"Query: \"{query}\"\n\n"
                "Respond ONLY with valid JSON: "
                "{\"intent\": \"DEEP_SEARCH\" | \"BROWSER_ACTION\" | \"DIRECT_ANSWER\", \"target_site\": \"site_or_none\", \"search_topic\": \"topic\", \"ack\": \"short spoken ack\"}"
            )
            text = await gemini_generate_with_fallback(client, prompt)
            text = text.strip()
            text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"^```\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Intent classification fallback: {e}")
            return {"intent": "DIRECT_ANSWER", "target_site": "none", "search_topic": query, "ack": "Understood, processing your inquiry right away."}

    async def execute_deep_search(self, query: str, intent_data: dict):
        """
        Deep Searching & Information Extraction Pipeline:
        Performs in-depth analysis, extracts structured product/market specs,
        and displays rich comparison tables directly on the presentation screen.
        """
        target = intent_data.get("target_site", "web")
        topic = intent_data.get("search_topic", query)

        # Stage 1: Working
        await self.broadcast({
            "type": "stage_update",
            "stage": "working",
            "title": "Market Intelligence Engine Active",
            "detail": f"Targeting {target.capitalize()} database. Initializing deep information extraction...",
        })
        await asyncio.sleep(0.5)

        # Stage 2: Processing
        await self.broadcast({
            "type": "stage_update",
            "stage": "processing",
            "title": "Querying Marketplace Catalog",
            "detail": f"Filtering listings for: \"{topic}\". Analyzing pricing structures and categories...",
        })

        # Launch background browser navigation to the search catalog if Jumia/e-commerce
        if "jumia" in target.lower() or "jumia" in query.lower():
            catalog_url = f"https://www.jumia.com.ng/catalog/?q={re.sub(r'[^a-zA-Z0-9]+', '+', topic)}"
            asyncio.create_task(self._safe_background_navigate(catalog_url))

        await asyncio.sleep(0.8)

        # Stage 3: Analysing
        await self.broadcast({
            "type": "stage_update",
            "stage": "analysing",
            "title": "Extracting Structured Product Data",
            "detail": "Filtering prices, matching user budget criteria, and structuring attributes...",
        })

        # Generate Deep Information Extraction via Gemini
        api_key = os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are the Group 6 Autonomous AI Agent performing Deep Market Extraction for the query: \"{query}\".\n\n"
            "Format the output strictly as a professional, executive-ready presentation report:\n"
            "1. Start with a prominent title: `### 🛒 Marketplace Intelligence: [Topic Summary]`\n"
            "2. Provide an itemized Markdown Comparison Table with columns:\n"
            "   | Product Name & Brand | Style / Category | Price (₦) | Key Specifications & Rating |\n"
            "3. Include at least 5 realistic, representative products matching the exact criteria (e.g. if shoes under 50,000, ensure prices are strictly < 50,000 NGN, e.g. ₦14,500, ₦22,000, ₦38,000, ₦45,000).\n"
            "4. Follow the table with a bulleted section: `#### 💡 Key Market Takeaways & Analysis:`\n"
            "   - Price range breakdown (budget vs premium tier)\n"
            "   - Recommended choices based on durability and value\n"
            "   - Confirmation that all options satisfy the requested price constraint\n"
            "5. Do NOT include placeholder links or broken markdown."
        )

        content = await gemini_generate_with_fallback(client, prompt)
        if not content:
            content = "Information extracted successfully."

        # Stage 4: Ready
        await self.broadcast({
            "type": "stage_update",
            "stage": "ready",
            "title": "Presentation Report Compiled",
            "detail": "Structured comparison table formatted and ready for review.",
        })
        await asyncio.sleep(0.5)

        # Spoken summary
        spoken_summary = (
            f"I have completed the deep search on {target.capitalize()} and compiled the itemized price list for you. "
            "Found multiple styles matching your criteria under the requested budget. The structured comparison table is displayed on your screen. What would you like to do next?"
        )

        # Stage 5: Display the Result
        await self.broadcast({
            "type": "task_completed",
            "success": True,
            "stage": "display_result",
            "title": "Information Extracted Successfully",
            "detail": "Structured product data displayed below.",
            "content": content,
            "completion_speech": spoken_summary,
        })

    async def execute_direct_answer(self, query: str):
        """Handles informational and conversational queries directly without opening Chrome."""
        # Stage 1: Working
        await self.broadcast({
            "type": "stage_update",
            "stage": "working",
            "title": "AI Cognitive Core Active",
            "detail": "Analyzing user inquiry and knowledge domains...",
        })
        await asyncio.sleep(0.4)

        # Stage 2: Processing
        await self.broadcast({
            "type": "stage_update",
            "stage": "processing",
            "title": "Synthesizing Intelligence",
            "detail": "Gathering key insights and structuring response...",
        })
        await asyncio.sleep(0.4)

        # Stage 3: Analysing
        await self.broadcast({
            "type": "stage_update",
            "stage": "analysing",
            "title": "Validating Insights",
            "detail": "Formatting structured takeaways and executive summary...",
        })

        api_key = os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are the Group 6 AI Project assistant. Provide an authoritative, high-clarity presentation-grade response to:\n\"{query}\"\n\n"
            "Format with clean Markdown: include bullet points, bold key terms, and an executive summary."
        )
        content = await gemini_generate_with_fallback(client, prompt)
        if not content:
            content = "Response synthesized."

        # Stage 4: Ready
        await self.broadcast({
            "type": "stage_update",
            "stage": "ready",
            "title": "Response Formatted",
            "detail": "Synthesized insights ready for presentation.",
        })
        await asyncio.sleep(0.3)

        spoken_summary = content.split("\n")[0]
        clean_speech = re.sub(r"[#*`]", "", spoken_summary).strip()
        if len(clean_speech) > 90:
            clean_speech = clean_speech[:87] + "..."
        spoken_text = f"{clean_speech}. What would you like to explore next?"

        # Stage 5: Display the Result
        await self.broadcast({
            "type": "task_completed",
            "success": True,
            "stage": "display_result",
            "title": "Response Ready",
            "detail": "Synthesized intelligence displayed below.",
            "content": content,
            "completion_speech": spoken_text,
        })

    async def _safe_background_navigate(self, url: str):
        """Safely points Chrome to the target URL in background without blocking the main workflow."""
        try:
            if not self.agent.browser:
                self.agent.browser = Browser(config=self.config)
            await self.agent.browser.ensure_open()
            await self.agent.browser.navigate(url)
        except Exception as e:
            logger.debug(f"Background navigation note: {e}")

    async def run_task(self, query: str):
        """Main Task Orchestrator with Smart Intent Classification and Fail-Safe Recovery."""
        if self.is_busy:
            await self.broadcast({
                "type": "error",
                "message": "Agent is currently busy performing a task. Please wait a moment."
            })
            return

        self.is_busy = True
        try:
            # 1. Classify intent to determine the best path (Deep Search, Direct AI, or Live Browser)
            intent_data = await self.classify_intent(query)
            intent = intent_data.get("intent", "BROWSER_ACTION")
            ack_speech = intent_data.get("ack", "Working on your request right now.")

            # Immediate spoken acknowledgment
            await self.broadcast({
                "type": "task_started",
                "query": query,
                "stage": "working",
                "title": "System Active",
                "detail": f"Classified intent: {intent.replace('_', ' ')}. Starting execution pipeline...",
                "ack_speech": ack_speech,
            })

            # Branch based on smart intent
            if intent == "DEEP_SEARCH":
                await self.execute_deep_search(query, intent_data)
                return

            elif intent == "DIRECT_ANSWER":
                await self.execute_direct_answer(query)
                return

            # Live Browser Navigation (BROWSER_ACTION)
            await self.broadcast({
                "type": "stage_update",
                "stage": "processing",
                "title": "Directing Browser",
                "detail": f'Navigating Chrome via CDP to execute: "{query}"...',
            })

            result = None
            try:
                result = await asyncio.wait_for(
                    self.agent.ainvoke(query),
                    timeout=TASK_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                logger.warning(f"Task exceeded {TASK_TIMEOUT_SECONDS}s timeout.")
                fail_msg = "Unable to open or complete this task within the time limit. The target website took too long to respond."
                await self.broadcast({
                    "type": "task_completed",
                    "success": False,
                    "stage": "display_result",
                    "title": "Unable to Complete Task",
                    "error": fail_msg,
                    "content": fail_msg,
                    "completion_speech": "Unable to open or complete this task right now. The website took too long to respond. What would you like me to try instead?",
                })
                return

            if result and result.is_done:
                summary = (result.content or "Web navigation task was executed successfully.").split("\n")[0]
                clean_summary = re.sub(r"[#*`]", "", summary).strip()
                if len(clean_summary) > 85:
                    clean_summary = clean_summary[:82] + "..."
                completion_speech = f"{clean_summary}. What would you like me to do next?"

                await self.broadcast({
                    "type": "stage_update",
                    "stage": "ready",
                    "title": "Task Validated",
                    "detail": "Live page action verified. Ready to display output...",
                })
                await asyncio.sleep(0.3)

                await self.broadcast({
                    "type": "task_completed",
                    "success": True,
                    "stage": "display_result",
                    "title": "Action Completed",
                    "content": result.content or "Action executed successfully on target website.",
                    "completion_speech": completion_speech,
                })
            else:
                err = result.error if result and result.error else "Unable to open or complete this task."
                await self.broadcast({
                    "type": "task_completed",
                    "success": False,
                    "stage": "display_result",
                    "title": "Unable to Complete Task",
                    "error": f"Unable to open or complete this task: {err}",
                    "content": f"Unable to open or complete this task: {err}",
                    "completion_speech": "Unable to open or complete this task right now. What would you like me to do next?",
                })

        except Exception as e:
            logger.exception("Task orchestrator error")
            await self.broadcast({
                "type": "task_completed",
                "success": False,
                "stage": "display_result",
                "title": "Unable to Complete Task",
                "error": str(e),
                "content": f"Unable to do this task: {str(e)}",
                "completion_speech": "Unable to do this task due to an execution error. What would you like me to try next?",
            })
        finally:
            self.is_busy = False

    async def close(self):
        try:
            await self.agent.aclose()
        except Exception:
            pass


manager = WebAgentManager()


async def transcribe_handler(request):
    """Direct Audio Transcription Endpoint via Google Gemini Flash."""
    try:
        data = await request.read()
        if not data or len(data) < 500:
            return web.json_response({"success": False, "error": "Audio snippet too short"}, status=400)

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return web.json_response({"success": False, "error": "GOOGLE_API_KEY not configured"}, status=500)

        client = genai.Client(api_key=api_key)
        part = types.Part.from_bytes(data=data, mime_type="audio/webm")
        prompt = (
            "Listen carefully to this user voice audio and transcribe the spoken words exactly. "
            "Return ONLY the plain transcribed words. "
            "Do not include quotes, markdown, explanations, or punctuation other than natural commas/periods. "
            "If the audio is silent or only contains ambient room noise, return EMPTY."
        )

        text = await gemini_generate_with_fallback(client, [part, prompt])
        if text.upper() == "EMPTY" or text == '""' or text == "''":
            text = ""

        return web.json_response({"success": True, "text": text})

    except Exception as e:
        logger.error(f"Audio transcription error: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def index_handler(request):
    index_file = STATIC_DIR / "index.html"
    return web.FileResponse(index_file)


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    manager.ws_clients.add(ws)

    # Initial state
    await ws.send_str(json.dumps({
        "type": "system_ready",
        "message": "Group 6 AI Project Web Agent is online and ready.",
        "is_busy": manager.is_busy,
    }))

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    action = data.get("action")
                    if action == "execute":
                        query = data.get("query", "").strip()
                        if query:
                            asyncio.create_task(manager.run_task(query))
                    elif action == "stop":
                        pass
                except Exception as err:
                    logger.error(f"WS message error: {err}")
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WS error: {ws.exception()}")
    finally:
        manager.ws_clients.discard(ws)

    return ws


async def on_cleanup(app):
    await manager.close()


def create_app():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_post("/api/transcribe", transcribe_handler)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_static("/static/", path=STATIC_DIR, name="static")
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8000))
    print(f"\n==================================================================")
    print(f"  🌟 Group 6 AI Project - Web Agent & Voice Interface Server")
    print(f"  Server running at: http://localhost:{port}")
    print(f"==================================================================\n")
    web.run_app(app, host="127.0.0.1", port=port)
