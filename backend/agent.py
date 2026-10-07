from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from models import ChatReply, ProductLookup, StockBySize
from tools import catalogue_snapshot, lookup_product, lookup_stock, search_products
from audit import audit_event

HERE = Path(__file__).resolve().parent

def make_agent() -> Agent[None, ChatReply]:
    load_dotenv(HERE.parent / ".env")
    api_key = os.getenv("PORTKEY_API")
    if not api_key:
        raise RuntimeError("PORTKEY_API is missing from the project .env")
    model = OpenAIChatModel("gpt_luna", provider=OpenAIProvider(base_url="https://api.portkey.ai/v1", api_key=api_key))
    agent = Agent(model, output_type=ChatReply, system_prompt=(HERE / "prompts" / "prompt.md").read_text(encoding="utf-8"))

    @agent.tool
    def find_products(ctx: RunContext[None], query: str) -> list[dict]:
        """Find catalogue products matching a shopper's request."""
        results = search_products(query)
        audit_event("find_products", query, f"Returned {len(results)} catalogue matches")
        return results

    @agent.tool
    def show_catalogue(ctx: RunContext[None]) -> list[dict]:
        """Show a representative selection of Campus Customs products."""
        results = catalogue_snapshot()
        audit_event("show_catalogue", "representative selection", f"Returned {len(results)} products")
        return results

    @agent.tool
    def get_product_details(ctx: RunContext[None], query: str) -> list[ProductLookup]:
        """Look up exact product descriptions and prices. Use this for any price or product-detail question."""
        results = lookup_product(query)
        audit_event("get_product_details", query, f"Returned {len(results)} exact detail matches")
        return results

    @agent.tool
    def get_product_stock(ctx: RunContext[None], product_id: str, size: str = "") -> list[StockBySize]:
        """Look up exact inventory quantities by product id, optionally for a requested size. Zero means out of stock."""
        results = lookup_stock(product_id, size)
        audit_event("get_product_stock", f"product_id={product_id}, size={size}", f"Returned {len(results)} stock rows")
        return results

    return agent

async def reply(message: str) -> ChatReply:
    audit_event("agent_run", message, "Started chat run")
    try:
        result = await make_agent().run(message, usage_limits=UsageLimits(request_limit=6, tool_calls_limit=4))
        audit_event("agent_run", message, "Structured ChatReply returned", "structured_output")
        return result.output
    except Exception as error:
        audit_event("agent_run", message, str(error), "error")
        raise
