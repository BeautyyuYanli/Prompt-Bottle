from unittest import TestCase

from prompt_bottle import (
    PromptBottle,
    pb_audio,
    pb_img_url,
    pb_mp3_audio,
    pb_wav_audio,
)


class TestBottle(TestCase):
    def test_text_tag_render(self):
        bottle = PromptBottle(
            [
                {
                    "role": "user",
                    "content": "{{arg0}}{{arg1}}{{arg2}}{{arg3}}{{arg4}}{{arg5}}{{arg6}}",
                },
            ]
        )
        rendered = bottle.render(
            arg0=pb_audio(
                {
                    "data": "Hello",
                    "format": "wav",
                }
            ),
            arg1="Hello",
            arg2=pb_img_url("https://example.com/image.png"),
            arg3="!",
            arg4=pb_mp3_audio("mp3b64"),
            arg5=pb_wav_audio("wavb64"),
            arg6="World!",
        )
        assert rendered == [
            {
                "content": [
                    {
                        "input_audio": {"data": "Hello", "format": "wav"},
                        "type": "input_audio",
                    },
                    {"text": "Hello", "type": "text"},
                    {
                        "image_url": {"url": "https://example.com/image.png"},
                        "type": "image_url",
                    },
                    {"text": "!", "type": "text"},
                    {
                        "input_audio": {"data": "mp3b64", "format": "mp3"},
                        "type": "input_audio",
                    },
                    {
                        "input_audio": {"data": "wavb64", "format": "wav"},
                        "type": "input_audio",
                    },
                    {"text": "World!", "type": "text"},
                ],
                "role": "user",
            }
        ]
        return rendered

    def test_audio_by_raw_string(self):
        bottle = PromptBottle([{"role": "user", "content": "{{arg0}}"}])
        rendered = bottle.render(
            arg0="<PROMPT_BOTTLE_AUDIO>{data: anything, format: mp3}</PROMPT_BOTTLE_AUDIO>"
        )
        assert rendered == [
            {
                "content": [
                    {
                        "input_audio": {"data": "anything", "format": "mp3"},
                        "type": "input_audio",
                    },
                ],
                "role": "user",
            }
        ]
        return rendered


if __name__ == "__main__":
    from rich import print

    # print(TestBottle().test_text_tag_render())
    print(TestBottle().test_audio_by_raw_string())
