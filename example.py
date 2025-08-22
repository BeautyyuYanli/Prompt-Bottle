import asyncio
from datetime import datetime

from prompt_bottle import render, to_openai_chat


async def main():
    # Load template
    with open("example.jinja", "r") as f:
        template = f.read()
    
    # Template variables
    template_vars = {
        "assistant_name": "DataBot",
        "assistant_type": "data analysis",
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "tools": ["calculate", "search_database", "generate_chart"],
        "conversation_history": [
            {
                "user": "What's the weather like?",
                "assistant": "I'll check the weather for you.",
                "reasoning": "User is asking for weather information. I need to use the weather tool to get current conditions.",
                "tool_needed": True,
                "tool_name": "get_weather",
                "tool_args": {"location": "current"},
                "tool_response": '{"temperature": "22°C", "condition": "sunny", "humidity": "65%"}'
            },
            {
                "user": "Can you calculate 15 * 23?",
                "assistant": "Let me calculate that for you.",
                "reasoning": "This is a simple multiplication. I'll use the calculate tool to ensure accuracy.",
                "tool_needed": True,
                "tool_name": "calculate",
                "tool_args": {"expression": "15 * 23"},
                "tool_response": "345"
            },
            {
                "user": "Thank you!",
                "assistant": "You're welcome! Is there anything else I can help you with?",
                "reasoning": "User is expressing gratitude. A simple acknowledgment and offer for further assistance is appropriate.",
                "tool_needed": False
            }
        ],
        "current_question": "Can you analyze the sales data and create a summary?"
    }
    
    # Render the template
    # from rich import print
    messages = render(template, **template_vars)
    print(messages)

    messages = await to_openai_chat(messages)
    print(messages)
    


if __name__ == "__main__":
    asyncio.run(main())