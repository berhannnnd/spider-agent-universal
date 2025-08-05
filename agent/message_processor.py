import re
import os
import requests
import json
from copy import deepcopy
from datetime import datetime

def debug_print(debug: bool, *args: str, end="\n", include_timestamp=True) -> None:
    if not debug:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = " ".join(map(str, args))
    if not include_timestamp:
        print(f"\033[90m{message}\033[0m", end=end)
    else:
        print(f"\033[97m[\033[90m{timestamp}\033[97m]\033[90m {message}\033[0m", end=end)

class MessageProcessor:
    def __init__(self, args):
        self.args = args
    
    def process_round(self, llm_response, item, messages, conversation_history):
        assistant_content, tool_calls, preserved_content = self.parse_assistant_message(llm_response, item)

        if not tool_calls:
            messages.append({"role": "assistant", "content": llm_response})
            conversation_history.append({
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": []
            })
            
            format_prompt = "Please follow the <tool_call> tag format and return a <tool_call> tag containing function name and parameters."
            user_msg = {"role": "user", "content": format_prompt}
            messages.append(user_msg)
            conversation_history.append(user_msg)
            return {"continue": True}
        
        messages.append({"role": "assistant", "content": preserved_content})
        conversation_history.append({
            "role": "assistant",
            "content": assistant_content,
            "tool_calls": tool_calls
        })
        
        if any(tc["name"] == "terminate" for tc in tool_calls):
            return {"terminated": True}
        
        non_terminate_tool_calls = [tc for tc in tool_calls if tc["name"] != "terminate"]
        
        if non_terminate_tool_calls:
            # 执行工具调用
            exec_results = self.execute_tool_calls(non_terminate_tool_calls)
            
            for i, (tool_call, exec_result) in enumerate(zip(non_terminate_tool_calls, exec_results)):
                result_content = exec_result.get("content", str(exec_result))
                
                conversation_history.append({
                    "role": "tool",
                    "content": result_content
                })
                
                messages.append({
                    "role": "user", 
                    "content": result_content
                })
        
        return {"continue": True}
    
    def parse_assistant_message(self, content, item):
        """Parse assistant message, separate content and tool_calls"""
        tool_call_pattern = r'<tool_call>(.*?)</tool_call>'
        matches = list(re.finditer(tool_call_pattern, content, re.DOTALL))
        
        if not matches:
            return content, [], content
        
        first_match = matches[0]
        pre_tool_call_content = content[:first_match.start()].strip()
        first_tool_call_end = first_match.end()
        preserved_content = content[:first_tool_call_end]
        
        tool_calls = self.parse_tool_calls(preserved_content, item)
        
        return pre_tool_call_content, tool_calls, preserved_content
    
    def parse_tool_calls(self, content, item):
        """Parse tool calls and add work_dir parameter for execute_bash"""
        tool_calls = []
        pattern = r'<tool_call>(.*?)</tool_call>'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            match = matches[0]
            
            # 尝试标准 XML 格式
            func_match = re.search(r'<function=([^>]+)>', match)
            if func_match:
                function_name = func_match.group(1)
                
                param_pattern = r'<parameter=([^>]+)>(.*?)</parameter>'
                param_matches = re.findall(param_pattern, match, re.DOTALL)
                
                arguments = {}
                for param_name, param_value in param_matches:
                    arguments[param_name] = param_value.strip()
                
                if function_name == "execute_bash" and "work_dir" not in arguments:
                    arguments["work_dir"] = os.path.join(self.args.databases_path, item['db_id'])
                
                tool_calls.append({
                    "name": function_name,
                    "arguments": arguments
                })
            else:
                # 尝试解析 JSON 格式
                try:
                    # 清理内容，移除多余的空白字符
                    cleaned_match = re.sub(r'\s+', ' ', match.strip())
                    
                    # 尝试提取 JSON 部分
                    json_match = re.search(r'\{.*\}', cleaned_match, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        
                        # 修复可能的格式问题
                        json_str = re.sub(r'"\s*\n\s*"', '", "', json_str)  # 修复换行问题
                        json_str = re.sub(r':\s*"([^"]*)\s*\n\s*"', r': "\1"', json_str)  # 修复值中的换行
                        
                        tool_data = json.loads(json_str)
                        if "function" in tool_data and "parameters" in tool_data:
                            function_name = tool_data["function"]
                            arguments = tool_data["parameters"]
                            
                            if function_name == "execute_bash" and "work_dir" not in arguments:
                                arguments["work_dir"] = os.path.join(self.args.databases_path, item['db_id'])
                            
                            tool_calls.append({
                                "name": function_name,
                                "arguments": arguments
                            })
                except Exception as e:
                    debug_print(True, f"工具调用解析失败: {str(e)}")
        
        return tool_calls
    
    def execute_tool_calls(self, tool_calls):
        """Execute tool calls via API"""
        if not tool_calls:
            return []
        
        # 显示工具调用信息（使用 debug_print）
        for tool_call in tool_calls:
            debug_print(True, f"正在调用工具: {tool_call['name']} 输入参数: {tool_call['arguments']} ...")
            
        url = f"http://{self.args.api_host}:{self.args.api_port}/execute"
        request_body = {"tool_calls": tool_calls}
        
        try:
            response = requests.post(
                url, 
                json=request_body, 
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            api_response = response.json()
            
            if isinstance(api_response, list):
                results = api_response
            elif isinstance(api_response, dict):
                results = [api_response]
            else:
                results = [{"error": f"Unexpected API response format: {api_response}"}]
            
            # 显示工具调用结果（使用 debug_print）
            for i, (tool_call, result) in enumerate(zip(tool_calls, results)):
                result_content = result.get("content", str(result))
                display_result = result_content[:50] + "..." if len(result_content) > 50 else result_content
                debug_print(True, f"工具调用结果: {display_result}")
            
            return results
                
        except Exception as e:
            error_result = {"error": f"API error: {str(e)}"}
            debug_print(True, f"工具调用失败: {str(e)}")
            return [error_result] * len(tool_calls)