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

from prompt_bottle.tags.convert_to import PB_TAG_TO_OPENAI, to_text_part
from prompt_bottle.tags.tags import PBTag, pb_tag_regex
from prompt_bottle.utils import check_type

# from typeguard import check_type

ALL_PART_PARAM = Union[ChatCompletionContentPartParam, ContentArrayOfContentPart]


class PromptBottle:
    template: str

    def __init__(
        self,
        template: Union[
            List[Union[ChatCompletionMessageParam, str]],
            str,
        ],
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
    last_end = 0

    # Combine all tag patterns into one regex
    combined_pattern = "|".join(f"({pb_tag_regex(tag)})" for tag in PBTag)

    # Process all matches in a single pass
    for match in re.finditer(combined_pattern, text):
        if match.start() > last_end:
            # Add normal text before the match
            normal_text = text[last_end : match.start()]
            if normal_text:
                parts.append(to_text_part(normal_text))

        # Find which group matched (which tag)
        matched_groups = [
            (i, g) for i, g in enumerate(match.groups()[1::2]) if g is not None
        ]
        if matched_groups:
            group_index, matched_text = matched_groups[0]
            tag = list(PBTag)[group_index]
            converter = PB_TAG_TO_OPENAI[tag]
            parts.append(converter(matched_text))

        last_end = match.end()

    # Add any remaining normal text
    if last_end < len(text):
        normal_text = text[last_end:]
        if normal_text:
            parts.append(to_text_part(normal_text))

    return parts


def _convert_controlled_struct(
    template: Sequence[Union[ChatCompletionMessageParam, str]],
) -> str:
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
            string_list.append(json.dumps(message, ensure_ascii=False) + ",")
    return "[" + "".join(string_list) + "]"


def render_string(template: str, **kwargs) -> List[ChatCompletionMessageParam]:
    expanded = Template(template).render(**kwargs)
    json_expanded = check_type(
        yaml.safe_load(expanded), List[ChatCompletionMessageParam]
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
