from typing import Optional

from prompt_bottle.bottle import PromptBottle


def simple_bottle(system: Optional[str], user: str) -> PromptBottle:
    if system:
        return PromptBottle(
            template=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
    else:
        return PromptBottle(template=[{"role": "user", "content": user}])
