from typing import TYPE_CHECKING, Any

from pydantic_ai.messages import ModelMessage

if TYPE_CHECKING:
    from openai.types.chat.chat_completion_message_param import (
        ChatCompletionMessageParam,
    )


async def to_openai_chat(
    source: list[ModelMessage], **model_kwargs: Any
) -> "list[ChatCompletionMessageParam]":
    from pydantic_ai.models.openai import OpenAIChatModel  # noqa

    if "model_name" not in model_kwargs:
        model_kwargs["model_name"] = "gpt-4o"

    return await OpenAIChatModel(**model_kwargs)._map_messages(source)
