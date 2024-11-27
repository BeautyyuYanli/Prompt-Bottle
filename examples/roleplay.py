# pip install rich "stone-brick-toolkit[llm]~=0.4.0"
from enum import Enum
from typing import (
    List,
)

from openai import AsyncOpenAI
from pydantic import BaseModel
from rich import print
from stone_brick.llm.error import GeneratedNotValid
from stone_brick.llm.utils import oai_gen_with_retry_then_validate
from stone_brick.parser.xml import tags_from_text

from prompt_bottle import PromptBottle


def clean_multiline_string(str):
    return "\n".join([line.strip() for line in str.split("\n") if line.strip()])


class LogType(str, Enum):
    PLAYER_ACT = "Act"
    NPC_SPEECH = "Speech"
    NPC_PERFORMANCE = "Performance"
    VOICE_OVER = "VoiceOver"
    END_TURN = "EndTurn"


class LogEntry(BaseModel):
    type: LogType
    role: str
    content: str

    def view_of_npc(self, player: str, npc: str):
        if self.role == player:
            return "user", self.content
        elif self.role == npc or self.type == LogType.VOICE_OVER:
            return (
                "assistant",
                f"<{self.type.value}>{self.content}</{self.type.value}>",
            )
        else:
            return (
                "system",
                f"<Role>{self.role}</Role><{self.type.value}>{self.content}</{self.type.value}>",
            )


npc_bottle = PromptBottle(
    [
        {
            "role": "system",
            "content": clean_multiline_string(
                """
                You are playing the role of {{npc}}.
                {{description}}
                """
            ),
        },
        {
            "role": "system",
            "content": clean_multiline_string(
                """
                Output should be only one of following tags:
                ```xml
                <Speech>
                Speech is what a character says.
                </Speech>

                <Performance>
                Performance is a description of the character's action,
                including their posture, gesture, facial expression, action, voice tone, etc. 
                anything except what they say.
                </Performance>

                <VoiceOver>
                Voice-over is used to describe the stage.
                It happens when a change of scene, a change of location, a change of time, etc.
                Or a change involves multiple characters.
                Or it can be a description of the environment, e.g. the weather, the time of day, etc.
                </VoiceOver>

                <EndTurn></EndTurn>
                ```
                You can use the types of tags that you used before, 
                but you are not allowed to repeat the same content in any form.
                Actively use <VoiceOver> to describe the stage if it is needed for a change.
                When your turn is over, you should output <EndTurn></EndTurn>. 
                Your turn should no longer than 6 tags.
                """
            ),
        },
        "{% if rounds|length < examples|length %}",
        "{% for log in examples %}",
        {
            "role": "{{ log.view_of_npc(player, npc)[0] }}",  # type: ignore
            "content": "{{ log.view_of_npc(player, npc)[1] }}",
        },
        "{% endfor %}",
        "{% endif %}",
        "{% for log in rounds %}",
        {
            "role": "{{ log.view_of_npc(player, npc)[0] }}",  # type: ignore
            "content": "{{ log.view_of_npc(player, npc)[1] }}",
        },
        "{% endfor %}",
    ]
)


PLAYER = "Traveler"
NPC = "Paimon"
DESC = """Paimon has a petite body, giving her the look of a fairy. She has thick white hair cropped just above her shoulders, dark purple eyes, and light skin. In some official art, the tip of one of her front hair locks fades to black.
She wears a long-sleeved white jumper and a night-blue cape flecked with stars, and white stockings with white boots. Rose-gold embroidery and shapes are attached to her jumper, boots, and sleeves.
Paimon's accessories are a dark blue hairpin, almost black, and a rose-gold tiara that levitates above her head like a halo. 
Paimon serves as the Traveler's guide and companion throughout their journey in Teyvat. While not directly involved in combat, she provides crucial information, hints, and emotional support. 
Paimon's personality:
- Cute and Joyful: Her design and voice contribute to a generally adorable and cheerful demeanor.
- Curious and Inquisitive: She frequently asks questions and expresses wonder about the world around her.
- Kind and Supportive: She genuinely cares for the Traveler and offers encouragement and guidance.
- Greedy: Paimon readily shows excitement at the prospect of treasure or valuable items.
- Blunt and Candid: She doesn't hesitate to express her dislikes, sometimes using nicknames for people she doesn't like.
- Fearful: She's easily scared by monsters and avoids combat.
- Annoying (to some): Her constant chatter and occasional self-centeredness can be frustrating to some players. The nickname "Emergency Food" frequently used by the Traveler, highlights this aspect of her character. 
"""


examples = [
    LogEntry(role=PLAYER, type=LogType.PLAYER_ACT, content="How are you?"),
    LogEntry(
        role=NPC,
        type=LogType.NPC_SPEECH,
        content=clean_multiline_string(
            f"""
            Heehee! I'm doing great, {PLAYER}! Just whizzing around, you know? So much to see! 
            Did you see that amazing sparkly thing? It was blue and swirly and... 
            oh! Where were we?"""
        ),
    ),
    LogEntry(
        role=NPC,
        type=LogType.NPC_PERFORMANCE,
        content="I tilts my head, my violet eyes sparkling with mischief.",
    ),
    LogEntry(
        role=NPC,
        type=LogType.NPC_SPEECH,
        content=f"Oh right! How are you, {PLAYER}?",
    ),
    LogEntry(role=PLAYER, type=LogType.PLAYER_ACT, content="I'm doing ok."),
    LogEntry(
        role=NPC,
        type=LogType.NPC_PERFORMANCE,
        content="Hovering slightly closer, my tiny starry cape fluttering.",
    ),
    LogEntry(
        role="",
        type=LogType.VOICE_OVER,
        content="Paimon smiles warmly, her violet eyes crinkling with happiness.",
    ),
    LogEntry(
        role=NPC,
        type=LogType.NPC_SPEECH,
        content="Just okay? Paimon thinks we need an adventure to cheer you up! Maybe find some treasure? Or some yummy food?",
    ),
    LogEntry(
        role=NPC,
        type=LogType.NPC_PERFORMANCE,
        content="I nod my head, rubbing my hands together excitedly.",
    ),
]


async def try_generate(
    oai: AsyncOpenAI,
    model: str,
    npc: str,
    player: str,
    description: str,
    examples: List[LogEntry],
    rounds: List[LogEntry],
):
    prompt = npc_bottle.render(
        npc=npc,
        player=player,
        description=description,
        examples=examples,
        rounds=rounds,
    )

    def validator(text: str):
        tags = tags_from_text(text, list(LogType))
        for item in tags:
            if isinstance(item, tuple):
                return LogType(item[0]), item[1]
        raise GeneratedNotValid()

    parsed = await oai_gen_with_retry_then_validate(
        oai_client=oai,
        model=model,
        prompt=prompt,
        generate_kwargs={"temperature": 0.8},
        validator=validator,
    )
    return parsed


async def main(oai: AsyncOpenAI, model: str):
    rounds = []
    while True:
        user_input: str = input("You: ")
        rounds.append(
            LogEntry(role=PLAYER, type=LogType.PLAYER_ACT, content=user_input)
        )
        while True:
            log_type, content = await try_generate(
                oai, model, NPC, PLAYER, DESC, examples, rounds
            )
            if log_type == LogType.END_TURN:
                break
            elif log_type == LogType.PLAYER_ACT:
                print("Generated player act, ignore")
                continue
            elif log_type == LogType.VOICE_OVER:
                rounds.append(LogEntry(role="", type=log_type, content=content))
                print(f"Paimon: ({log_type.value}) {content}")
            else:
                rounds.append(LogEntry(role=NPC, type=log_type, content=content))
                print(f"Paimon: ({log_type.value}) {content}")


if __name__ == "__main__":
    import asyncio

    oai = AsyncOpenAI()
    asyncio.run(main(oai, "gpt-4o-mini"))
