import json
from datetime import datetime
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

client = OpenAI(
    api_key="sk-MO8z6DgjbgqwhsmqXN0ltmpVl7E13x72skt2C19LCAJDJvaE", 
    base_url="http://47.251.106.113:3010/v1" 
)

model = "o4-mini"

def debug_print(debug: bool, *args: str, end="\n", include_timestamp=True) -> None:
    if not debug:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = " ".join(map(str, args))
    if not include_timestamp:
        print(f"\033[90m{message}\033[0m", end=end)
    else:
        print(f"\033[97m[\033[90m{timestamp}\033[97m]\033[90m {message}\033[0m", end=end)


def get_current_weather(location):
    return f"""{location}天气预报:{location} 明天20度，大部分时间气温在20-25度之间，有雾霾，降雨概率10%。"""



available_functions = {
    "get_current_weather": get_current_weather,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "查天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "查询地址",
                    },
                },
                "required": ["location"],
            },
        },
    }
]


def call_llm(client, model, messages, use_stream=False, debug=True, tools=tools):
    if use_stream:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
            stream=True,
        )

        full_message = ChatCompletionMessage(
            role="assistant",
            content=""
        )
        choice = Choice(
            index=0,
            message=full_message,
            finish_reason="stop"  # noqa
        )
        first_token = True
        content_length = 0

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                content_length += len(chunk.choices[0].delta.content)
                if content_length > 50:
                    debug_print(debug, "", include_timestamp=False)
                    content_length = 0
                    first_token = True

                if first_token:
                    debug_print(debug, f"{chunk.choices[0].delta.role} :> ", end="")
                    first_token = False
                full_message.content += chunk.choices[0].delta.content
                debug_print(debug, f"{chunk.choices[0].delta.content.strip()}", end="", include_timestamp=False)

            if chunk.choices and chunk.choices[0].delta.tool_calls:
                if not full_message.tool_calls:
                    full_message.tool_calls = []

                for tool_call in chunk.choices[0].delta.tool_calls:
                    tool_call_id = tool_call.id
                    if not tool_call_id and full_message.tool_calls:
                        tool_call_id = full_message.tool_calls[-1].id

                    function_name = tool_call.function.name
                    function_arguments = tool_call.function.arguments

                    existing_tool_call = next((tc for tc in full_message.tool_calls if tc.id == tool_call_id), None)
                    if not existing_tool_call and tool_call_id:
                        full_message.tool_calls.append(
                            ChatCompletionMessageToolCall(
                                id=tool_call_id,
                                type="function",
                                function=Function(
                                    name=function_name or "",
                                    arguments=function_arguments or "",
                                ),
                            )
                        )
                    elif existing_tool_call:
                        if function_name:
                            existing_tool_call.function.name = function_name
                        if function_arguments:
                            existing_tool_call.function.arguments += function_arguments
                    else:
                        continue

            if chunk.choices and chunk.choices[0].finish_reason:
                choice.finish_reason = chunk.choices[0].finish_reason  # noqa
                break
        response_message = full_message
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
            stream=False,
        )
        choice = response.choices[0]
        response_message = response.choices[0].message

        debug_print(debug, f"{response_message.role} :> {response_message.content.strip()}")

    messages.append(response_message)
    tool_calls = response_message.tool_calls

    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)

            debug_print(debug, f"正在调用工具: {function_name} 输入参数: {function_args} ...")

            function_response = function_to_call(**function_args)
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                }
            )
            debug_print(debug, f"工具调用结果: {str(function_response)[:50]}...")

    return choice


def run_conversation():
    messages = [{
        "role": "user",
        "content": f"""这是用户对话的历史信息：
        """
    }]
    history = InMemoryHistory()
    auto_suggest = AutoSuggestFromHistory()
    while True:
        try:
            user_input = prompt(
                "user: ",
                history=history,
                auto_suggest=auto_suggest,
                enable_history_search=True
            )
            if user_input == "quit":
                break
            # messages.append({"role": "user", "content": user_input})
            messages.append({"role": "user", "content": user_input})
            for message in messages:
                if isinstance(message, ChatCompletionMessage):
                    if message.tool_calls:
                        message.content = ""
            function_call_state = True
            while function_call_state:
                function_call_state = False
                use_stream = True
                response_message = call_llm(client, model, messages, use_stream)
                if response_message.finish_reason == "tool_calls":
                    function_call_state = True
            print("\n=============================================")
        except (EOFError, KeyboardInterrupt) as e:
            print("\n程序退出")
            break

if __name__ == "__main__":
    run_conversation()

