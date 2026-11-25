import asyncio
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from src.agent import Agent
from src.agent.browser.config import BrowserConfig
from src.providers.google import ChatGoogle

load_dotenv()

console = Console()

BANNER = """
=================================================================
  🌐  Group 6 AI Project
  Goal-Oriented Autonomous Web Agent
  Design & Implementation for Intelligent Website Navigation
=================================================================
  * Describe your goal in plain language and press Enter.
  * The browser stays open — give as many tasks as you like!
  * Type  exit / quit / q  to end the session.
=================================================================
"""


async def main():
    llm = ChatGoogle(model='gemini-flash-lite-latest')
    config = BrowserConfig(browser='chrome', headless=False)
    agent = Agent(
        config=config,
        llm=llm,
        use_vision=False,
        use_web_mcp=True,
        max_steps=100,
        max_consecutive_failures=5,
        keep_alive=True,
    )

    print(BANNER)

    try:
        while True:
            try:
                user_query = input("Enter your query: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nSession interrupted. Closing...")
                break

            if not user_query:
                continue

            if user_query.lower() in ("exit", "quit", "q"):
                print("\nShutting down agent and closing browser. Goodbye!")
                break

            # Run the agent task — stays inside the SAME event loop every time
            result = await agent.ainvoke(user_query)

            if result.is_done and result.content:
                console.print(Markdown(result.content))
            elif result.error:
                console.print(f"[red]Error:[/red] {result.error}")

            print("\n" + "-" * 65)
            print("  ✅  Task finished. Ready for your next query!")
            print("-" * 65 + "\n")

    finally:
        # Clean shutdown — close browser properly
        try:
            await agent.aclose()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
