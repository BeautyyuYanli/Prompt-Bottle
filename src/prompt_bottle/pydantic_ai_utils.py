from typing import Any

from pydantic_ai.messages import ModelMessage


async def to_openai_chat(source: list[ModelMessage], **model_kwargs: Any):
    from pydantic_ai.models.openai import OpenAIModel

    if "model_name" not in model_kwargs:
        model_kwargs["model_name"] = "gpt-4o"

    return await OpenAIModel(**model_kwargs)._map_messages(source) # type: ignore