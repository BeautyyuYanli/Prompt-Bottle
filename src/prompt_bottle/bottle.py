import json
import re
from typing import (
    Iterable,
    List,
    Sequence,
    Union,
    cast,
)

import yaml
from jinja2 import Template
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_assistant_message_param import (
    ContentArrayOfContentPart,
)
from stone_brick.parser.xml import tags_from_text

from prompt_bottle.tags.convert_to import PB_TAG_TO_OPENAI, to_text_part
from prompt_bottle.tags.tags import PBTag
from prompt_bottle.utils import check_type

# from typeguard import check_type

ALL_PART_PARAM = Union[ChatCompletionContentPartParam, ContentArrayOfContentPart]

PLACEHOLDER = "PROMPT_BOTTLE_PLACEHOLDER"


def _encapsulate(value):
    """Surround all {{...}} patterns to be <PLACEHOLDER>{{...}}</PLACEHOLDER>"""
    if isinstance(value, str):
        # Find all {{...}} patterns and wrap them with placeholders
        pattern = r"(\{\{.*?\}\})"
        value = re.sub(pattern, f"<{PLACEHOLDER}>\\1</{PLACEHOLDER}>", value)
        return value
    elif isinstance(value, dict):
        return {k: _encapsulate(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_encapsulate(v) for v in value]
    else:
        return value


def _decapsulate(value: str):
    """Get all <PLACEHOLDER>any string</PLACEHOLDER> patterns, remove the placeholders,
    and dump things in it as a json string"""
    pattern = f"<{PLACEHOLDER}>(.*?)</{PLACEHOLDER}>"

    # Find all matches and replace them with their JSON-decoded content
    def replace_func(match: re.Match):
        content = match.group(1)
        # Encode the content as a JSON string
        return json.dumps(content, ensure_ascii=False)[1:-1]

    return re.sub(pattern, replace_func, value, flags=re.DOTALL)


def _convert_controlled_struct(
    template: Sequence[Union[ChatCompletionMessageParam, str]],
) -> str:
    """Convert the bottle template to a json string, so that it can be rendered by jinja2"""
    string_list: List[str] = []
    for message in template:
        if isinstance(message, str):
            if re.match(r"^\s*\{\{.*\}\}\s*$", message.strip()):
                string_list.append(message + ",")
            elif re.match(r"^\s*\{\%.*\%\}\s*$", message.strip()):
                string_list.append(message)
            else:
                raise ValueError(
                    f"Unknown template string: {message} \nThe string in list can only be {{{{ var }}}} or {{% expression %}}"
                )
        else:
            string_list.append(
                json.dumps(_encapsulate(message), ensure_ascii=False) + ","
            )
    return "[" + "".join(string_list) + "]"


class PromptBottle:
    template: str

    def __init__(
        self,
        template: List[Union[ChatCompletionMessageParam, str]],
    ):
        if isinstance(template, str):
            self.template = template
        else:
            self.template = _convert_controlled_struct(template)

    def render(self, **kwargs) -> List[ChatCompletionMessageParam]:
        return render_string(self.template, **kwargs)

    def render_as_json(self, **kwargs) -> str:
        return json.dumps(self.render(**kwargs))


def render_text(
    text: str, jinja_render: bool = False, **kwargs
) -> List[ChatCompletionContentPartParam]:
    if jinja_render:
        text = Template(text).render(**kwargs)
    parts: List[ChatCompletionContentPartParam] = []

    tags = tags_from_text(text, list(PBTag))
    for tag in tags:
        if isinstance(tag, tuple):
            name, content = tag
            parts.append(PB_TAG_TO_OPENAI[PBTag(name)](content))
        else:
            parts.append(to_text_part(tag))

    return parts


def render_string(template: str, **kwargs) -> List[ChatCompletionMessageParam]:
    expanded = Template(template).render(**kwargs)
    json_expanded = check_type(
        yaml.safe_load(_decapsulate(expanded)), List[ChatCompletionMessageParam]
    )
    return render_struct(json_expanded, **kwargs)


def render_struct(
    template: Sequence[ChatCompletionMessageParam],
    **kwargs,
) -> List[ChatCompletionMessageParam]:
    def render_str_or_parts(
        source: Union[str, Iterable[ALL_PART_PARAM]],
    ):
        if isinstance(source, str):
            return render_text(source, **kwargs)
        new_source: List[ALL_PART_PARAM] = []
        for part in source:
            if part["type"] == "text":
                part = cast(ChatCompletionContentPartTextParam, part)
                new_source.extend(render_text(part["text"], **kwargs))
            else:
                new_source.append(part)
        return new_source

    def render_user_message(message: ChatCompletionUserMessageParam):
        parts = render_str_or_parts(message["content"])
        message["content"] = check_type(parts, List[ChatCompletionContentPartParam])
        return message

    def render_system_message(message: ChatCompletionSystemMessageParam):
        parts = render_str_or_parts(message["content"])
        message["content"] = check_type(parts, List[ChatCompletionContentPartTextParam])
        return message

    def render_assistant_message(message: ChatCompletionAssistantMessageParam):
        content = message.get("content", None)
        if content is None:
            return message
        rendered = render_str_or_parts(content)
        message["content"] = check_type(rendered, List[ContentArrayOfContentPart])
        return message

    answer = list(template)
    for message in answer:
        if message["role"] == "system":
            render_system_message(message)
        elif message["role"] == "user":
            render_user_message(message)
        elif message["role"] == "assistant":
            render_assistant_message(message)
        else:
            pass
    return answer
