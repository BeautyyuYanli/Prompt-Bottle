from rich import print

from prompt_bottle import PromptBottle, pb_img_url

bottle = PromptBottle(
    [
        {
            "role": "system",
            "content": "You are a helpful assistant in the domain of {{ domain }}",
        },
        "{% for round in rounds %}",
        {
            "role": "user",
            "content": "Question: {{ round[0] }}",
        },
        {
            "role": "assistant",
            "content": "Answer: {{ round[1] }}",
        },
        "{% endfor %}",
        {"role": "user", "content": "Question: {{ final_question }}"},
    ]
)

prompt = bottle.render(
    domain="math",
    rounds=[
        ("1+1", "2"),
        (
            f"What is this picture? {pb_img_url('https://upload.wikimedia.org/wikipedia/en/a/a9/Example.jpg')}",
            "This is an example image by Wikipedia",
        ),
    ],
    final_question="8*8",
)

print(prompt)

from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=prompt,
)

print(response.choices[0].message.content)
