"""OpenAI model lists and constants."""


# Base models
BASE_MODELS: list[str] = [
    "gpt-4",
    "gpt-3.5-turbo",
    "gpt-4-turbo",
    "gpt-4o",
    "gpt-4o-mini",
]

# Reasoning models
REASONING_MODELS: list[str] = ["o1", "o3-mini", "o3", "o4-mini"]

# GPT-4.1 family
GPT_41_FAMILY: list[str] = ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]

# GPT-5 family
GPT_5_FAMILY: list[str] = ["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-pro"]

# GPT-5.1 Codex family
GPT_51_FAMILY: list[str] = [
    "gpt-5.1",
    "gpt-5.1-codex",
    "gpt-5.1-codex-mini",
    "gpt-5.1-codex-max",
]

# GPT-5.2 family
GPT_52_FAMILY: list[str] = ["gpt-5.2", "gpt-5.2-pro"]

# Supported models
SUPPORTED_MODELS: list[str] = [
    "gpt-5.2",
    "gpt-5.2-pro",
    "gpt-5.2-instant",
    "gpt-4.1",
    "gpt-4o",
    "gpt-5.1-codex-mini",
    "gpt-4o-mini",
    "gpt-4.1-nano",
    "gpt-3.5-turbo",
]


def get_all_possible_models() -> list[str]:
    """Returns all possible models."""
    return (
        BASE_MODELS
        + REASONING_MODELS
        + GPT_41_FAMILY
        + GPT_5_FAMILY
        + GPT_51_FAMILY
        + GPT_52_FAMILY
    )
