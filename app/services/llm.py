from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, ChatOpenAI

load_dotenv()


def llm_enabled() -> bool:
    provider = os.getenv("LLM_PROVIDER", "none").strip().lower()

    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"))

    if provider == "azure_openai":
        required = (
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
        )
        return all(os.getenv(name) for name in required)

    return False


def get_chat_model():
    provider = os.getenv("LLM_PROVIDER", "none").strip().lower()

    if provider == "openai":
        # The explanation task does not require extended reasoning.
        # reasoning_effort="none" also avoids the Chat Completions
        # function-tool incompatibility for gpt-5.6-luna.
        return ChatOpenAI(
            model=os.environ["OPENAI_MODEL"],
            reasoning_effort="none",
        )

    if provider == "azure_openai":
        return AzureChatOpenAI(
            azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            temperature=0,
        )

    raise RuntimeError(
        "LLM is not configured. Set LLM_PROVIDER to openai or azure_openai."
    )
