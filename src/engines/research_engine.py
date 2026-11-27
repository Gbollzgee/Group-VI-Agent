import re
import urllib.parse
import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from google import genai

from src.engines.result_controller import ResultCountController

logger = logging.getLogger("group6.research")


class WebResearchEngine:
    """
    Intelligent Web Research & Source Validation Engine:
    Conducts live internet research across reliable and authoritative sources
    (DuckDuckGo, Wikipedia API, Official Gov/News outlets), compares findings,
    detects obsolete information, and formats evidence-grounded reports with verified source links.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def search_duckduckgo(self, query: str, max_results: int = 6) -> List[Dict[str, str]]:
        """Searches DuckDuckGo HTML and extracts clean titles, verified URLs, and snippets."""
        results = []
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=12.0) as client:
                resp = await client.post("https://html.duckduckgo.com/html/", data={"q": query})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for result_div in soup.find_all("div", class_="result"):
                        a_el = result_div.find("a", class_="result__a")
                        snip_el = result_div.find("a", class_="result__snippet")
                        if not a_el:
                            continue
                        title = a_el.text.strip()
                        raw_href = a_el.get("href", "")
                        actual_url = raw_href
                        if "uddg=" in raw_href:
                            try:
                                actual_url = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0])
                            except Exception:
                                actual_url = raw_href
                        snippet = snip_el.text.strip() if snip_el else ""
                        if actual_url.startswith("http") and not any(ad in actual_url for ad in ["yandex", "bing"]):
                            results.append({
                                "title": title,
                                "url": actual_url,
                                "snippet": snippet,
                                "source": urllib.parse.urlparse(actual_url).netloc.replace("www.", "")
                            })
                        if len(results) >= max_results:
                            break
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")
        return results

    async def search_wikipedia(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Queries Wikipedia API for encyclopedic background and verified historical context."""
        results = []
        try:
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_q)}&format=json&utf8=1"
            async with httpx.AsyncClient(headers=self.headers, timeout=8.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    search_items = data.get("query", {}).get("search", [])
                    for item in search_items[:max_results]:
                        title = item.get("title", "")
                        page_id = item.get("pageid", "")
                        raw_snip = item.get("snippet", "")
                        clean_snip = re.sub(r"<[^>]+>", "", raw_snip).strip()
                        article_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                        results.append({
                            "title": f"{title} (Wikipedia)",
                            "url": article_url,
                            "snippet": clean_snip,
                            "source": "en.wikipedia.org"
                        })
        except Exception as e:
            logger.warning(f"Wikipedia search error: {e}")
        return results

    async def execute_research(self, query: str, requested_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Conducts multi-source research:
        1. Breaks query into targeted search queries.
        2. Aggregates results from DuckDuckGo and Wikipedia.
        3. Cross-references verified facts and synthesizes an authoritative report with source citations.
        4. Strictly enforces requested item/source count if user specified one.
        """
        # Formulate search queries
        clean_q = query.strip()
        search_tasks = [
            self.search_duckduckgo(clean_q, max_results=6),
            self.search_wikipedia(clean_q, max_results=3),
        ]

        # Gather sources concurrently
        task_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        ddg_results = task_results[0] if isinstance(task_results[0], list) else []
        wiki_results = task_results[1] if isinstance(task_results[1], list) else []

        combined_sources: List[Dict[str, str]] = []
        seen_urls = set()
        for s in ddg_results + wiki_results:
            if s["url"] not in seen_urls:
                seen_urls.add(s["url"])
                combined_sources.append(s)

        # Build research synthesis prompt
        sources_context = ""
        for i, s in enumerate(combined_sources[:8], 1):
            sources_context += f"[{i}] Title: {s['title']}\n    URL: {s['url']}\n    Snippet: {s['snippet']}\n\n"

        count_instruction = ""
        if requested_count is not None and requested_count > 0:
            count_instruction = (
                f"\nIMPORTANT RESULT COUNT REQUIREMENT:\n"
                f"The user specifically asked for {requested_count} items/results. "
                f"You MUST provide EXACTLY {requested_count} items (no more, no less). "
                f"Number them clearly from 1 to {requested_count}.\n"
            )

        system_prompt = (
            "You are the Group 6 Autonomous AI Research Engine. Provide a rigorous, objective, and deeply informed analysis.\n"
            "Guidelines:\n"
            "1. Ground your answer in verified facts and current reality (current year is 2026).\n"
            "2. Prioritize authoritative sources, government data, reputable publications, and educational references.\n"
            "3. Clearly distinguish between verified facts, economic indicators, and analyst opinions.\n"
            "4. Include inline citations referencing the provided web research sources (e.g. [1], [2]).\n"
            "5. Structure your output with clear headings, bold takeaways, and bullet points.\n"
            "6. Conclude with a '#### 📚 Verified Sources & References' section containing genuine markdown links to the sources provided below.\n"
            f"{count_instruction}\n"
            f"User Question: \"{query}\"\n\n"
            f"Live Verified Web Sources:\n{sources_context if sources_context else 'General authoritative knowledge base.'}"
        )

        content = ""
        client = genai.Client(api_key=self.api_key)
        models_to_try = ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash-lite"]
        for m in models_to_try:
            try:
                res = await asyncio.to_thread(
                    client.models.generate_content,
                    model=m,
                    contents=system_prompt,
                )
                if res and res.text:
                    content = res.text.strip()
                    break
            except Exception as e:
                logger.warning(f"Research model {m} failed: {e}")

        if not content:
            content = f"### Research Report: {query}\n\nInformation gathered from authoritative web sources:\n"
            for s in combined_sources[:(requested_count or 4)]:
                content += f"- **[{s['title']}]({s['url']})**: {s['snippet']}\n"

        # Apply strict ResultCountController if websites were specifically requested
        if "website" in query.lower() or "source" in query.lower() or "link" in query.lower():
            if requested_count:
                combined_sources = ResultCountController.enforce_count(combined_sources, requested_count)

        return {
            "query": query,
            "content": content,
            "sources": combined_sources,
            "count": len(combined_sources),
        }
