import json
import logging
import os
import re

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

IMPACT_THRESHOLD = int(os.getenv("IMPACT_THRESHOLD", "80"))

_SYSTEM_PROMPT = """\
You are an AI research impact evaluator.
Use the web_search tool to look up real-world reception of the paper before scoring.
Search for GitHub repos, Twitter/X discussions, blog posts, and community reactions.
Search at least once using the paper title.

After gathering evidence, output ONLY a JSON object (no other text):
{{"score": int, "reason": str}}

Scoring criteria (0-100):
- Originality: new paradigm vs incremental improvement
- Generality: broad AI impact vs narrow domain
- Community interest: likely to trend in 1 week
- Business relevance: applicability to AI/data companies like SK AX"""

_HUMAN_TEMPLATE = """\
Evaluate the following AI paper and return a JSON score.

Title: {title}
Abstract: {abstract}
arXiv ID: {arxiv_id}"""

_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)


def _build_agent() -> AgentExecutor:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    tools = []
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        tools.append(TavilySearchResults(max_results=5, name="web_search"))
    else:
        logger.warning("TAVILY_API_KEY not set — impact agent will score without web search")

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("human", _HUMAN_TEMPLATE),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=5)


def _parse_result(output: str) -> dict:
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        match = _JSON_RE.search(output)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"score": 0, "reason": "parse_error"}


def _score_one(agent: AgentExecutor, paper: dict) -> dict:
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    arxiv_id = paper.get("paper_id", "").replace("arxiv:", "")

    try:
        result = agent.invoke({
            "title": title,
            "abstract": abstract,
            "arxiv_id": arxiv_id,
        })
        parsed = _parse_result(result.get("output", ""))
    except Exception as exc:
        logger.warning("Impact agent failed for '%s': %s", title[:60], exc)
        parsed = {"score": 0, "reason": "agent_error"}

    return {
        **paper,
        "impact_score": int(parsed.get("score", 0)),
        "impact_reason": parsed.get("reason", ""),
    }


def score_papers(papers: list[dict]) -> list[dict]:
    """Stage 2: Score each paper 0-100 using GPT-4o agent with Tavily web search."""
    if not papers:
        return []

    agent = _build_agent()
    scored = []
    for paper in papers:
        scored.append(_score_one(agent, paper))
        logger.debug("Scored '%s': %d", paper.get("title", "")[:60], scored[-1]["impact_score"])

    logger.info(
        "impact_agent: scored %d papers, %d >= threshold(%d)",
        len(scored),
        sum(1 for p in scored if p["impact_score"] >= IMPACT_THRESHOLD),
        IMPACT_THRESHOLD,
    )
    return scored
