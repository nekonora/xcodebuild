#!/bin/bash

# Launch script for mcpxcodebuild MCP server
# This ensures the server runs with the correct environment

cd "$(dirname "$0")"
exec uv run python -m mcpxcodebuild