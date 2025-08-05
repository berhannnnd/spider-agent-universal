import random
import json
import os
import time
import logging
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from typing import Dict, Any, List

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from file_manager import FileManager
from message_processor import MessageProcessor

# Configure logging - 禁用 httpx 和其他库的 INFO 日志
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def debug_print(debug: bool, *args: str, end="\n", include_timestamp=False) -> None:
    """Print debug information with optional timestamp"""
    if not debug:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = " ".join(map(str, args))
    if not include_timestamp:
        print(f"{message}", end=end)
    else:
        print(f"[{timestamp}] {message}", end=end)

class UniversalAgentPromptBuilder:
    """Universal prompt builder that works with any database type"""
    
    def __init__(self, system_prompt_path: str, databases_path: str = None, 
                 documents_path: str = None, database_type: str = "mysql"):
        self.system_prompt_path = system_prompt_path
        self.databases_path = databases_path
        self.documents_path = documents_path
        self.database_type = database_type
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file"""
        try:
            with open(self.system_prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Could not load system prompt: {e}")
            return "You are a helpful AI assistant with access to database and system tools."
    
    def _load_external_knowledge(self, instance: Dict[str, Any]) -> str:
        """Load external knowledge if available"""
        if not self.documents_path or not instance.get("external_knowledge"):
            return ""
        
        try:
            knowledge_file = os.path.join(self.documents_path, instance["external_knowledge"])
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            logger.warning(f"Could not load external knowledge: {e}")
        
        return ""
    
    def _load_database_info(self, db_id: str) -> str:
        """Load database schema information"""
        if not self.databases_path or not db_id or db_id == "GENERAL":
            return f"Connected to {self.database_type} database. Use execute_database_sql to query."
        
        try:
            db_file = os.path.join(self.databases_path, db_id, "database_description", "schema.sql")
            if os.path.exists(db_file):
                with open(db_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            logger.warning(f"Could not load database info: {e}")
        
        return f"Connected to {self.database_type} database '{db_id}'. Use execute_database_sql to query."
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for context"""
        if not history:
            return ""
        
        context_parts = ["Previous conversation context:"]
        for i, exchange in enumerate(history[-5:], 1):  # Only last 5 exchanges
            context_parts.append(f"Exchange {i}:")
            context_parts.append(f"User: {exchange['user']}")
            assistant_response = exchange['assistant']
            if len(assistant_response) > 200:
                assistant_response = assistant_response[:200] + "..."
            context_parts.append(f"Assistant: {assistant_response}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def build_initial_prompt(self, instance: Dict[str, Any], conversation_history: List[Dict] = None) -> List[Dict[str, str]]:
        """Build initial prompt for the instance"""
        messages = []
        
        # System message
        system_content = self.system_prompt
        
        # Add database info
        db_info = self._load_database_info(instance.get("db_id", ""))
        if db_info:
            system_content += f"\n\nDatabase Information:\n{db_info}"
        
        # Add external knowledge
        external_knowledge = self._load_external_knowledge(instance)
        if external_knowledge:
            system_content += f"\n\nExternal Knowledge:\n{external_knowledge}"
        
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history if in chat mode
        if conversation_history:
            history_context = self._format_conversation_history(conversation_history)
            if history_context:
                messages.append({"role": "user", "content": history_context})
        
        # Add user instruction
        user_instruction = instance.get("instruction", "")
        if user_instruction:
            messages.append({"role": "user", "content": user_instruction})
        
        return messages

class LLMAgent:
    def __init__(self, args):
        self.args = args
        
        # Debug: Print environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print(f"✅ OpenAI API Key loaded: {api_key[:10]}...")
        else:
            print("❌ OpenAI API Key not found in environment variables")
        
        self.model_client = OpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        self.file_manager = FileManager(args)
        # Fix: MessageProcessor only takes args parameter
        self.message_processor = MessageProcessor(args)
        
        # Initialize prompt builder based on strategy
        if args.prompt_strategy == "universal-agent":
            self.prompt_builder = UniversalAgentPromptBuilder(
                system_prompt_path=args.system_prompt_path,
                databases_path=getattr(args, 'databases_path', None),
                documents_path=getattr(args, 'documents_path', None),
                database_type=getattr(args, 'database_type', 'mysql')
            )
        else:
            # Fallback to original spider-agent
            try:
                from prompt_builders import get_prompt_builder
                self.prompt_builder = get_prompt_builder(args.prompt_strategy)
            except ImportError:
                # Use universal builder as fallback
                self.prompt_builder = UniversalAgentPromptBuilder(
                    system_prompt_path=args.system_prompt_path,
                    databases_path=getattr(args, 'databases_path', None),
                    documents_path=getattr(args, 'documents_path', None),
                    database_type=getattr(args, 'database_type', 'mysql')
                )
        
        self.processed_instances = defaultdict(int)
        
        logger.info(f"Initialized LLMAgent with model: {args.model}")
    
    def call_llm(self, messages, instance_id=None, round_num=None, use_stream=True, debug=True):
        """Call LLM with retry mechanism and optional streaming"""
        max_retries = 500
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if use_stream:
                    # Streaming response with real-time printing
                    response = self.model_client.chat.completions.create(
                        model=self.args.model,
                        messages=messages,
                        temperature=self.args.temperature,
                        top_p=self.args.top_p,
                        max_tokens=self.args.max_new_tokens,
                        stream=True,
                    )

                    full_message = ChatCompletionMessage(
                        role="assistant",
                        content=""
                    )
                    choice = Choice(
                        index=0,
                        message=full_message,
                        finish_reason="stop"
                    )
                    first_token = True

                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content is not None:
                            if first_token:
                                debug_print(debug, "assistant :> ", end="")
                                first_token = False
                            full_message.content += chunk.choices[0].delta.content
                            debug_print(debug, f"{chunk.choices[0].delta.content}", end="", include_timestamp=False)

                        if chunk.choices and chunk.choices[0].finish_reason:
                            choice.finish_reason = chunk.choices[0].finish_reason
                            break
                    
                    # Print newline after streaming is complete
                    if debug:
                        print()
                    
                    content = full_message.content
                else:
                    # Non-streaming response
                    response = self.model_client.chat.completions.create(
                        model=self.args.model,
                        messages=messages,
                        temperature=self.args.temperature,
                        top_p=self.args.top_p,
                        max_tokens=self.args.max_new_tokens,
                        stream=False,
                    )
                    content = response.choices[0].message.content
                
                return content
                
            except Exception as e:
                retry_count += 1
                wait_time = min(2 ** retry_count, 60)
                logger.warning(f"LLM call failed (attempt {retry_count}/{max_retries}): {str(e)}")
                
                if retry_count >= max_retries:
                    return f"ERROR: Failed to get LLM response after {max_retries} attempts: {str(e)}"
                
                time.sleep(wait_time)
    
    def start_chat_mode(self):
        """Start interactive chat mode"""
        print("🤖 Universal AI Assistant")
        print("=" * 50)
        print(f"Connected to: {getattr(self.args, 'database_type', 'No database')}")
        print("Type 'exit' or 'quit' to end the conversation")
        print("Type 'help' for available commands")
        print("=" * 50)
        
        conversation_history = []
        
        while True:
            try:
                user_input = input("\nuser: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                if user_input.lower() == 'clear':
                    conversation_history = []
                    print("🧹 Conversation history cleared!")
                    continue
                
                if not user_input:
                    continue
                
                # Create a chat instance
                instance = {
                    "instance_id": f"chat_{int(time.time())}",
                    "instruction": user_input,
                    "db_id": getattr(self.args, 'database_type', 'GENERAL'),
                    "external_knowledge": None
                }
                
                # Process the message
                result = self._process_chat_instance(instance, conversation_history)
                
                # Add to conversation history
                conversation_history.append({
                    "user": user_input,
                    "assistant": result.get("final_answer", "No response generated"),
                    "timestamp": time.time()
                })
                
                # Keep only last 10 exchanges to manage context length
                if len(conversation_history) > 10:
                    conversation_history = conversation_history[-10:]
                
                print("=============================================")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                logger.error(f"Chat error: {str(e)}")
    
    def _show_help(self):
        """Show help information"""
        print("\n📖 Available Commands:")
        print("  help     - Show this help message")
        print("  clear    - Clear conversation history")
        print("  exit     - Exit the chat")
        print("\n🛠️ Available Tools:")
        print("  - execute_database_sql: Run SQL queries")
        print("  - execute_bash: Run system commands")
        print("  - terminate: Complete current task")
        print("\n💡 Example queries:")
        print("  - 'Show me all tables in the database'")
        print("  - 'What files are in the current directory?'")
        print("  - 'Calculate the sum of 1 to 100'")
    
    def _process_chat_instance(self, instance: Dict[str, Any], history: List[Dict]) -> Dict[str, Any]:
        """Process a single chat instance"""
        try:
            # Build initial prompt with conversation history
            messages = self.prompt_builder.build_initial_prompt(
                instance, 
                conversation_history=history
            )
            
            conversation_history = deepcopy(messages)
            terminated = False
            final_answer = ""
            
            for round_num in range(self.args.max_rounds):
                # Use streaming for chat mode
                llm_response = self.call_llm(
                    messages, 
                    instance["instance_id"], 
                    round_num + 1, 
                    use_stream=True, 
                    debug=True
                )
                
                if llm_response.startswith("ERROR:"):
                    final_answer = f"Error: {llm_response}"
                    break
                
                result = self.message_processor.process_round(
                    llm_response, instance, messages, conversation_history
                )
                
                # Extract final answer from assistant response
                if not final_answer:
                    # Get the last assistant message
                    for msg in reversed(conversation_history):
                        if msg.get("role") == "assistant":
                            final_answer = msg.get("content", "")
                            break
                
                if result.get("terminated"):
                    terminated = True
                    break
                
                if result.get("continue"):
                    continue
            
            return {
                "final_answer": final_answer or "No response generated",
                "terminated": terminated,
                "conversation": conversation_history
            }
            
        except Exception as e:
            error_msg = f"Error processing chat: {str(e)}"
            logger.error(error_msg)
            return {"final_answer": error_msg, "error": True}
    
    def process_single_item(self, item, rollout_idx):
        """Process a single item with specified rollout index"""
        instance_id = item["instance_id"]

        if self.processed_instances[instance_id] >= self.args.rollout_number:
            print(f"Skipping {instance_id} rollout {rollout_idx + 1} (already completed {self.processed_instances[instance_id]} valid rollouts)")
            return None
        
        try:
            messages = self.prompt_builder.build_initial_prompt(item)
            conversation_history = deepcopy(messages)
            terminated = False
            
            for round_num in range(self.args.max_rounds):
                print(f"Processing {instance_id} rollout {rollout_idx + 1}, round {round_num + 1}")

                # Use non-streaming for batch processing
                llm_response = self.call_llm(
                    messages, 
                    instance_id, 
                    round_num + 1, 
                    use_stream=False, 
                    debug=False
                )
                
                if llm_response.startswith("ERROR:"):
                    print(f"Failed to get valid LLM response for {instance_id}")
                    error_result = {
                        "instance_id": instance_id,
                        "rollout_idx": rollout_idx,
                        "error": llm_response,
                        "round_failed": round_num + 1,
                        "terminated": False
                    }
                    self.file_manager.add_single_result(error_result)
                    return error_result
                
                result = self.message_processor.process_round(
                    llm_response, item, messages, conversation_history
                )
                
                if result.get("terminated"):
                    terminated = True
                    break
                
                if result.get("continue"):
                    continue
            
            result = {
                "instance_id": instance_id,
                "rollout_idx": rollout_idx,
                "conversation": conversation_history,
                "final_messages": messages,
                "terminated": terminated
            }
            
            self.file_manager.add_single_result(result)
            
            status = "TERMINATED" if terminated else "INCOMPLETE"
            print(f"Completed: {instance_id} (rollout {rollout_idx + 1}/{self.args.rollout_number}) - {status}")
            
            return result
            
        except Exception as e:
            error_result = {
                "instance_id": instance_id,
                "rollout_idx": rollout_idx,
                "error": str(e),
                "terminated": False
            }
            
            self.file_manager.add_single_result(error_result)
            print(f"Error processing {instance_id} rollout {rollout_idx + 1}: {str(e)}")
            return error_result
    
    def run(self):
        """Main execution function"""
        # Check if chat mode is enabled
        if getattr(self.args, 'chat_mode', False):
            self.start_chat_mode()
            return
        
        # Original batch processing mode
        existing_results = self.file_manager.load_existing_results()
        self.processed_instances = self.file_manager.processed_instances
        os.makedirs(self.args.output_folder, exist_ok=True)
        
        with open(self.args.input_file, 'r', encoding='utf-8') as f:
            items = [json.loads(line) for line in f]

        random.shuffle(items)
        
        tasks_to_process = []
        for item in items:
            instance_id = item["instance_id"]
            current_valid_rollouts = self.processed_instances[instance_id]
            
            for rollout_idx in range(current_valid_rollouts, self.args.rollout_number):
                tasks_to_process.append((item, rollout_idx))
        
        total_expected = len(items) * self.args.rollout_number
        total_existing = sum(self.processed_instances.values())
        
        print(f"Total items: {len(items)}")
        print(f"Rollout number: {self.args.rollout_number}")
        print(f"Prompt strategy: {self.args.prompt_strategy}")
        print(f"Total expected tasks: {total_expected}")
        print(f"Valid completed tasks: {total_existing}")
        print(f"Tasks to process: {len(tasks_to_process)}")
        
        if not tasks_to_process:
            print("All rollouts have been completed successfully!")
            return
        
        completed_count = 0
        with ThreadPoolExecutor(max_workers=self.args.num_threads) as executor:
            future_to_task = {
                executor.submit(self.process_single_item, item, rollout_idx): (item, rollout_idx)
                for item, rollout_idx in tasks_to_process
            }
            
            for future in as_completed(future_to_task):
                item, rollout_idx = future_to_task[future]
                try:
                    result = future.result()
                    if result is not None:
                        completed_count += 1
                        print(f"Progress: {completed_count}/{len(tasks_to_process)} completed")
                except Exception as e:
                    print(f"Unexpected error processing {item['instance_id']} rollout {rollout_idx + 1}: {str(e)}")
        
        print(f"All processing completed! Results saved to: {self.args.output_folder}")
        print(f"Total processed in this run: {completed_count}")