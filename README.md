<div align="center">

<img src="https://github.com/user-attachments/assets/d7ab6301-e0b2-4573-b232-0bc7d498e95a" width=200>

# Prompt Bottle

**A powerful prompt template engine built upon Jinja**

[![PyPI version](https://badge.fury.io/py/prompt-bottle.svg)](https://badge.fury.io/py/prompt-bottle)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## Features ✨

- **🎯 Jinja-Powered Templates**: Leverage the full power of Jinja2 templating for dynamic prompt generation
- **🎭 Role-Based Messaging**: Structure conversations with system, user, assistant, and tool roles
- **🤖 Pydantic-AI Compatible**: Returns structured pydantic-ai ModelMessage objects for seamless integration
- **🔄 Format Conversion**: Convert to OpenAI chat API (or other APIs) through pydantic-ai's message mapping

## Installation 📦

```bash
pip install prompt-bottle
```

## Quick Start 🚀

### Basic Usage

```python
from prompt_bottle import render

# Simple template
template = """
You are a helpful assistant.
<div role="user">{{ user_message }}</div>
"""

messages = render(template, user_message="Hello, world!")
print(messages)
```

## Core Concepts 📚

### Template Example
```jinja
You are a helpful assistant.
{{ system_instructions }}

{% for item in conversation %}
<div role="user">{{ item.message }}</div>
<div role="assistant">
  <think>{{ item.reasoning }}</think>
  {{ item.response }}
</div>
{% endfor %}

<div role="user">
  <Instruction>
  Now you are required to answer the query based on the context.
  Your output must be quoted in <Answer></Answer> tags.
  </Instruction>
  <Context>
  {{ context }}
  </Context>
  <Query>
  {{ query }}
  </Query>
</div>
```
💡 **Check out [`example.py`](example.py) and [`example.jinja`](example.jinja) for a comprehensive example with all features!**

> [!WARNING]
> You can use any HTML-like tags in your prompt, other than the reserved tags. However, all tags **must be properly closed** (e.g., `<instruct> content </instruct>` not `<instruct> content`) to avoid parsing errors.

### Roles
Prompt Bottle supports four main roles:

- **`system`**: System instructions and configuration. Default of raw text.
- **`user`**: User messages and queries  
- **`assistant`**: AI assistant responses
- **`tool`**: Tool execution results

### Response Types
Assistant responses can include multiple content tags:

- **`<text>`**: Regular text content. Default of raw text.
- **`<tool_call>`**: Function/tool invocations
- **`<think>`**: Reasoning and thought processes

### Request Types
TODO: Will support multimodal input in the future.


## API Reference 📖

### `render(template: str, **kwargs) -> list[ModelMessage]`
Renders a Jinja template with the provided variables and returns structured messages.

**Parameters:**
- `template`: Jinja template string
- `**kwargs`: Template variables

**Returns:** List of pydantic-ai ModelMessage objects (ModelRequest/ModelResponse)

### `to_openai_chat(messages: list[ModelMessage], **model_kwargs) -> list[dict]`
Converts structured messages to OpenAI chat completion format.

**Parameters:**
- `messages`: List of ModelMessage objects from render()
- `**model_kwargs`: OpenAI model configuration (default model: gpt-4o)

**Returns:** List of OpenAI-formatted message dictionaries

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links 🔗

[velin](https://github.com/moeru-ai/velin): Vue.js based prompt template engine
