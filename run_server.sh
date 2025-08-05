#!/bin/bash

# Universal Agent Tool Server
# Usage: ./run_server.sh

echo "Starting Universal Agent Tool Server..."
echo "Server will run on localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the tool server
python servers/serve.py --host localhost --port 5000 --workers 4