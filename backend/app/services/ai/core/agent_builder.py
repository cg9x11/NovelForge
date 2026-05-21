
from typing import List, Optional
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from loguru import logger


def build_agent(
    model: BaseChatModel,
    tools: List[BaseTool],
    system_prompt: str,
    enable_summarization: bool = False,
    max_tokens_before_summary: int = 8192,
):
    middleware = []

    if enable_summarization:
        try:
            middleware.append(
                SummarizationMiddleware(
                    model=model,
                    max_tokens_before_summary=max_tokens_before_summary,
                )
            )
        except Exception as e:


            pass
    pass
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=middleware,
    )

    return agent
