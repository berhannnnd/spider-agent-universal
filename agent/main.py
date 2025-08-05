import argparse
from llm_agent import LLMAgent

def main():
    parser = argparse.ArgumentParser()
    
    # Data paths
    parser.add_argument("--input_file", required=False, help="Input jsonl file path (optional for chat mode)")
    parser.add_argument("--output_folder", default="./chat_logs", help="Output folder path")
    parser.add_argument("--system_prompt_path", default="../prompts/universal_agent.txt", help="System prompt file path")
    parser.add_argument("--databases_path", required=False, help="Databases directory path (optional)")
    parser.add_argument("--documents_path", required=False, help="Documents directory path (optional)")
    
    # Chat mode settings
    parser.add_argument("--chat_mode", action="store_true", help="Enable interactive chat mode")
    parser.add_argument("--database_type", default="mysql", choices=["mysql", "postgresql", "sqlite", "snowflake"], 
                       help="Database type to connect to")
    
    # LLM settings
    parser.add_argument("--model", default="gpt-4", help="Model name")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature")
    parser.add_argument("--top_p", type=float, default=0.9, help="Top-p")
    parser.add_argument("--max_new_tokens", type=int, default=4096, help="Max new tokens")
    
    # Execution settings
    parser.add_argument("--api_host", default="localhost", help="API host")
    parser.add_argument("--api_port", default="5000", help="API port")
    parser.add_argument("--max_rounds", type=int, default=20, help="Max conversation rounds")
    parser.add_argument("--num_threads", type=int, default=4, help="Number of threads")
    parser.add_argument("--rollout_number", type=int, default=1, help="Number of rollouts per example")
    
    parser.add_argument("--prompt_strategy", default="universal-agent", 
                       choices=["universal-agent", "spider-agent"],
                       help="Prompt building strategy")
    
    args = parser.parse_args()
    
    agent = LLMAgent(args)
    
    if args.chat_mode:
        agent.start_chat_mode()
    else:
        agent.run()

if __name__ == "__main__":
    main()