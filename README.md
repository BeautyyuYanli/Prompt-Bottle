<div align="center">

<img src="https://github.com/user-attachments/assets/a3145acc-ae14-4b5a-b6e5-0e11ef488450" width=200>

# Prompt Bottle

An LLM-targeted template engine, built upon Jinja.

</div>

## Features

- Use Jinja syntax to build template for LLM inputs list
- Painless multimodal support for LLM inputs
- Use OpenAI chat completion API

## Quick Start

Install the package via pip:

```bash
pip install prompt_bottle
```

Then, we can create a "Prompt Bottle" using Jinja syntax:

```python
from prompt_bottle import PromptBottle

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
```

Then we can render it as we do with Jinja.

<details>
<summary>Render the bottle and send to OpenAI:</summary>

```python
from prompt_bottle import pb_img_url

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

from rich import print  # pip install rich

print(prompt)
```

<details>
<summary>It prints the rendered prompt:</summary>

```python
[
    {
        'content': [{'text': 'You are a helpful assistant in the domain of math', 'type': 'text'}],
        'role': 'system'
    },
    {'content': [{'text': 'Question: 1+1', 'type': 'text'}], 'role': 'user'},
    {'role': 'assistant', 'content': [{'text': 'Answer: 2', 'type': 'text'}]},
    {
        'content': [
            {'text': 'Question: What is this picture? ', 'type': 'text'},
            {
                'image_url': {'url': 'https://upload.wikimedia.org/wikipedia/en/a/a9/Example.jpg'},
                'type': 'image_url'
            }
        ],
        'role': 'user'
    },
    {
        'role': 'assistant',
        'content': [{'text': 'Answer: This is an example image by Wikipedia', 'type': 'text'}]
    },
    {'content': [{'text': 'Question: 8*8', 'type': 'text'}], 'role': 'user'}
]
```
</details>

Finally, we can send the prompt to OpenAI:

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=prompt,
)

print(response.choices[0].message.content)
```

The response is:

```
Answer: 64
```

</details>


## Concepts

**Prompt Bottle**

The template of the prompt. It is a list of **Template Messages**. It can be rendered as python dict or JSON string.

**Template Message**

A message is either an OpenAI message dict, or a Jinja control block like `{% for ... %}` or `{% if ... %}`. 

If it is a text message, it will be rendered by Jinja firstly, like `{{ variable }}`. And then it will be rendered by `Multimodal Tag`.

**Multimodal Tag**

The tag inside a text can render the text message as multimodal parts. The tag looks like `<PROMPT_BOTTLE_IMG_URL>https://your.image.url</PROMPT_BOTTLE_IMG_URL>`, or using `pb_img_url("https://your.image.url")` function to get it.

All the **Multimodal Tags** can be found in [prompt_bottle.tags.tags](./src/prompt_bottle/tags/tags.py).

**Presets**

Some common prompt templates are provided in [prompt_bottle.presets](./src/prompt_bottle/presets).
