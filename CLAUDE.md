# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Dependencies and Setup
- Install dependencies: `uv sync` (uses uv package manager)
- Run development tools: `uv run pyright` for type checking, `uv run ruff` for linting

### Testing and Building
- Install package locally: `uv pip install -e .`
- Run as module: `python -m mcpxcodebuild` 
- Package for distribution: `uv build`

## Architecture Overview

This is a Model Context Protocol (MCP) server that provides iOS Xcode build capabilities for AI assistants. The project structure is minimal:

### Core Components

**src/mcpxcodebuild/server.py** - Main MCP server implementation
- Implements two MCP tools: `build` and `test`
- Auto-discovers Xcode projects (.xcworkspace/.xcodeproj) in specified folders
- Automatically finds build schemes and available iOS simulators
- Executes xcodebuild commands and returns build/test results with error filtering

**Key Functions:**
- `find_xcode_project()` - Walks directory tree to locate Xcode projects
- `find_scheme()` - Extracts available build schemes from xcodebuild -list
- `find_available_simulator()` - Finds available iOS simulators via xcrun simctl
- `call_tool()` - Main tool handler that orchestrates build/test operations

**Entry Points:**
- `src/mcpxcodebuild/__init__.py` - Exports main() function
- `src/mcpxcodebuild/__main__.py` - Module entry point

The server automatically handles Xcode project detection, scheme selection, and simulator targeting, making it easy for AI assistants to build and test iOS projects without manual configuration.