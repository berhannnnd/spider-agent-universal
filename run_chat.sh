#!/bin/bash

# Universal Agent Chat Mode (Client Only)
# Usage: ./run_chat.sh [database_type]
# Note: Make sure to start the server first with: python servers/serve.py

DATABASE_TYPE=${1:-mysql}

echo "Starting Universal Agent in Chat Mode (Client Only)..."
echo "Database Type: $DATABASE_TYPE"
echo "Note: Make sure the tool server is running on localhost:5000"
echo "To start server: python servers/serve.py"
echo ""

# Wait a moment to let user read the message
sleep 1

# Start the agent in chat mode
cd agent
python main.py \
    --chat_mode \
    --database_type $DATABASE_TYPE \
    --system_prompt_path ../prompts/universal_agent.txt \
    --model gpt-4o \
    --temperature 0.7 \
    --max_rounds 20 \
    --api_host localhost \
    --api_port 5000 \
    --prompt_strategy universal-agent

echo "Universal Agent chat session ended."