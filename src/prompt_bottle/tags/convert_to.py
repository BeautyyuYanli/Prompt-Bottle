from typing import Callable, Dict

import yaml
from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartInputAudioParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
)
from openai.types.chat.chat_completion_content_part_input_audio_param import InputAudio

from prompt_bottle.tags.tags import PBTag
from prompt_bottle.utils import check_type


def to_image_url_part(url: str) -> ChatCompletionContentPartImageParam:
    return {
        "image_url": {"url": url},
        "type": "image_url",
    }


def to_text_part(content: str) -> ChatCompletionContentPartTextParam:
    return {
        "text": content,
        "type": "text",
    }


def to_audio_part(content: str) -> ChatCompletionContentPartInputAudioParam:
    return {
        "input_audio": check_type(yaml.safe_load(content), type=InputAudio),
        "type": "input_audio",
    }


def to_wav_audio_part(content: str) -> ChatCompletionContentPartInputAudioParam:
    return {
        "input_audio": {"data": content, "format": "wav"},
        "type": "input_audio",
    }


def to_mp3_audio_part(content: str) -> ChatCompletionContentPartInputAudioParam:
    return {
        "input_audio": {"data": content, "format": "mp3"},
        "type": "input_audio",
    }


# Mapping from PBTag to conversion function
PB_TAG_TO_OPENAI: Dict[PBTag, Callable[[str], ChatCompletionContentPartParam]] = {
    PBTag.IMG_URL: to_image_url_part,
    PBTag.TEXT: to_text_part,
    PBTag.WAV_AUDIO: to_wav_audio_part,
    PBTag.MP3_AUDIO: to_mp3_audio_part,
    PBTag.AUDIO: to_audio_part,
}
