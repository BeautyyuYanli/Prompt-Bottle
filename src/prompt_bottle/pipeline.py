from enum import StrEnum
from typing import Iterable

from minijinja import render_str
from pydantic import BaseModel
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    ModelResponse,
    ModelResponsePart,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from qwq_tag import QwqTag


class RolesType(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ResponseType(StrEnum):
    TEXT = "text"
    TOOL_CALL = "tool_call"
    THINK = "think"


class ToolBaseAttr(BaseModel):
    tool_name: str
    tool_call_id: str


def stage_jinja_render(text: str, **kwargs) -> str:
    return render_str(text, **kwargs)


def stage_split_history(
    text: str,
) -> Iterable[tuple[RolesType, dict[str, str], list[str | QwqTag]]]:
    res = QwqTag.from_str(text)
    for tag in res:
        if (
            isinstance(tag, QwqTag)
            and tag.name == "div"
            and (role := tag.attr.get("role", None))
            and any(x.value == role for x in RolesType)
        ):
            yield (
                RolesType(role),
                tag.attr,
                tag.content,
            )
        else:
            yield (
                RolesType.SYSTEM,
                {"role": RolesType.SYSTEM.value},
                [tag],
            )


def _render_assstant(content: list[str | QwqTag]) -> list[ModelResponsePart]:
    parts: list[ModelResponsePart] = []
    for item in content:
        if isinstance(item, QwqTag) and item.name in ResponseType:
            if item.name == ResponseType.TOOL_CALL:
                attr = ToolBaseAttr.model_validate(item.attr)
                parts.append(
                    ToolCallPart(
                        tool_name=attr.tool_name,
                        tool_call_id=attr.tool_call_id,
                        args=item.content_text,
                    )
                )
            elif item.name == ResponseType.THINK:
                parts.append(ThinkingPart(content=item.content_text))
            elif item.name == ResponseType.TEXT:
                if parts and parts[-1].part_kind == "text":
                    parts[-1].content += item.content_text
                else:
                    parts.append(TextPart(content=item.content_text))
            else:
                raise NotImplementedError()
        else:  # noqa: PLR5501
            if parts and parts[-1].part_kind == "text":
                parts[-1].content += str(item)
            else:
                parts.append(TextPart(content=str(item)))
    return parts


def _render_user(content: list[str | QwqTag]) -> list[ModelRequestPart]:
    # TODO: multimodal supporting
    return [UserPromptPart(content=_render_request_plain(content))]


def _render_request_plain(content: list[str | QwqTag]) -> str:
    return "".join(str(item) for item in content)


def stage_process(
    messages: Iterable[tuple[RolesType, dict[str, str], list[str | QwqTag]]],
) -> Iterable[ModelResponsePart | ModelRequestPart]:
    for msg in messages:
        content = msg[2]
        if msg[0] == RolesType.ASSISTANT:
            yield from _render_assstant(content)
        elif msg[0] == RolesType.TOOL:
            tool_attr = ToolBaseAttr.model_validate(msg[1])
            yield ToolReturnPart(
                tool_name=tool_attr.tool_name,
                tool_call_id=tool_attr.tool_call_id,
                content=_render_request_plain(content),
            )
        elif msg[0] == RolesType.SYSTEM:
            yield SystemPromptPart(content=_render_request_plain(content))
        elif msg[0] == RolesType.USER:
            yield from _render_user(content)
        else:
            raise NotImplementedError()


def stage_collect(
    messages: Iterable[ModelResponsePart | ModelRequestPart],
) -> Iterable[ModelMessage]:
    resp: list[ModelResponsePart] = []
    req: list[ModelRequestPart] = []
    
    def merge_continuous_parts(parts_list: list) -> list:
        """Merge continuous parts with the same type."""
        if not parts_list:
            return parts_list
        
        merged = []
        for part in parts_list:
            if (merged and 
                type(merged[-1]) is type(part) and
                hasattr(merged[-1], 'content') and 
                hasattr(part, 'content')):
                # Merge text content for parts of the same type
                merged[-1].content += "\n" + part.content
            else:
                merged.append(part)
        return merged
    
    for msg in messages:
        if isinstance(msg, TextPart | ToolCallPart | ThinkingPart):
            if not resp:
                if req:
                    yield ModelRequest(parts=merge_continuous_parts(req))
                req = []
            resp.append(msg)
        elif isinstance(msg, SystemPromptPart | UserPromptPart | ToolReturnPart):
            if not req:
                if resp:
                    yield ModelResponse(parts=merge_continuous_parts(resp))
                resp = []
            req.append(msg)
    
    # Yield any remaining parts
    if resp:
        yield ModelResponse(parts=merge_continuous_parts(resp))
    if req:
        yield ModelRequest(parts=merge_continuous_parts(req))


def render(text: str, **kwargs) -> list[ModelMessage]:
    res = stage_jinja_render(text, **kwargs)
    res2 = stage_split_history(res)
    res3 = stage_process(res2)
    res4 = list(stage_collect(res3))
    return res4


