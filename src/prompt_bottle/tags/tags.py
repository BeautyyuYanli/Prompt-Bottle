import json
from enum import Enum
from typing import Any, Dict, Union, cast

import yaml
from openai.types.chat.chat_completion_content_part_input_audio_param import InputAudio


class PBTag(str, Enum):
    IMG_URL = "PROMPT_BOTTLE_IMG_URL"
    TEXT = "PROMPT_BOTTLE_TEXT"
    WAV_AUDIO = "PROMPT_BOTTLE_WAV_AUDIO"
    MP3_AUDIO = "PROMPT_BOTTLE_MP3_AUDIO"
    AUDIO = "PROMPT_BOTTLE_AUDIO"


def pb_tag_regex(tag: PBTag):
    return rf"<{tag.value}>(.*?)</{tag.value}>"


def pb_tag(tag: PBTag, content: Union[str, Dict[str, Any]]):
    if isinstance(content, str):
        return f"<{tag.value}>{content}</{tag.value}>"
    else:
        return (
            f"<{tag.value}>"
            + json.dumps(
                yaml.safe_dump(
                    content, default_flow_style=True, width=float("inf")
                ).strip()
            )[1:-1]
            + f"</{tag.value}>"
        )


def pb_img_url(url: str):
    return pb_tag(PBTag.IMG_URL, url)


def pb_wav_audio(b64: str):
    return pb_tag(PBTag.WAV_AUDIO, b64)


def pb_mp3_audio(b64: str):
    return pb_tag(PBTag.MP3_AUDIO, b64)


def pb_audio(input_audio: InputAudio):
    return pb_tag(PBTag.AUDIO, cast(dict, input_audio))
