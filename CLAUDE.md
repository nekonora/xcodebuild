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
- Implements five MCP tools: `build`, `test`, `list_schemes`, `set_default_scheme`, `get_default_scheme`
- Auto-discovers Xcode projects (.xcworkspace/.xcodeproj) in specified folders
- Supports custom simulator name and iOS version selection
- Captures both stdout and stderr for complete error/warning reporting
- Provides output filtering (all, errors only, warnings only, string match)
- Executes xcodebuild commands and returns build/test results with proper exit code handling

**Key Functions:**
- `find_xcode_project()` - Walks directory tree to locate Xcode projects
- `find_scheme()` - Extracts available build schemes with default scheme support
- `build_destination()` - Builds simulator destination with custom name/version support
- `filter_build_output()` - Filters xcodebuild output based on specified criteria
- `call_tool()` - Main tool handler that orchestrates all operations

**Tool Parameters:**
- `folder` - Path to Xcode project directory (required)
- `scheme` - Build scheme name (optional, uses default or first available)
- `simulator_name` - iOS simulator name like "iPhone 16" (optional, auto-detects if not specified)
- `ios_version` - iOS version like "18.3.1" (optional, auto-detects if not specified)
- `output_filter` - Filter output: "all", "errors_only", "warnings_only", "string_match"
- `filter_string` - String to match when using "string_match" filter

**Entry Points:**
- `src/mcpxcodebuild/__init__.py` - Exports main() function
- `src/mcpxcodebuild/__main__.py` - Module entry point

The server automatically handles Xcode project detection, scheme selection, and simulator targeting, making it easy for AI assistants to build and test iOS projects. It provides both automatic configuration and manual override options for precise control over build environments.