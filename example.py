from prompt_bottle import render, to_openai_chat


async def main():
    with open("example.jinja", "r") as f:
        content = f.read()

    res = render(
        content,
        system_prompt="Hello",
        history=[
            {"user": "Hello", "assistant": "World"},
        ],
    )

    print(res)
    res = await to_openai_chat(res)
    return res


if __name__ == "__main__":
    import asyncio
    from rich import print
    print(asyncio.run(main()))