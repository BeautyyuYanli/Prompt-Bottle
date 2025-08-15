from minijinja import render_str
from qwq_tag import QwqTag
from typing import Iterable, Literal, Union, Annotated, Self
from enum import StrEnum
from rich import print
from pydantic import BaseModel, AfterValidator, model_validator

class RolesType(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class ControlAttr(BaseModel):
    role: RolesType

def stage_jinja_render(text: str, **kwargs) -> str:
    return render_str(text, **kwargs)

def stage_split_history(text: str) -> Iterable[tuple[RolesType, list[str | QwqTag]]]:
    res = QwqTag.from_str(text)
    for tag in res:
        if (
            isinstance(tag, QwqTag)
            and tag.name == "div"
            and (role := tag.attr.get("role", None))
            and role in RolesType
        ):
            yield (
                # ControlAttr.model_validate(tag.attr),
                RolesType(role),
                tag.content,
            )
        else:
            yield (
                # ControlAttr.model_validate(getattr(tag, "attr", {"role": RolesType.SYSTEM})),
                RolesType.SYSTEM,
                [tag],
            )
        
def stage_process(messages: Iterable[tuple[RolesType, list[str | QwqTag]]]) -> Iterable:
    for msg in messages:
        content = msg[1]
        for idx, item in enumerate(content):
            if isinstance(item, QwqTag):
                pass
            else: #noqa: PLR5501
                pass
                # if msg[0].nospace:
                #     content[idx] = re.sub(r'\s+', '', item)
        yield msg[0], content
# def stage_prompt_bottle(world: str) -> str:
#     return PromptBottle(world)


# def stage_openai(world: str) -> str:
#     return OpenAI(world)

with open("testing.html", "r") as f:
    content = f.read()

res = stage_jinja_render(
    content,
    system_prompt="Hello",
    history=[
        {"user": "Hello", "assistant": "World"},
    ],
)
res2 = stage_split_history(res)
res3 = stage_process(res2)
print(list(res3))