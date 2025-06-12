# xcodebuild MCP Server

A Model Context Protocol server that builds iOS workspace/project that enables seamless workflow working with iOS projects in Visual Studio Code using extensions like Cline or Roo Code.

<a href="https://glama.ai/mcp/servers/5ibnbzxmql">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/5ibnbzxmql/badge" alt="mcpxcodebuild MCP server" />
</a>

### Available Tools

- `build` - Build iOS Xcode workspace/project
    - `folder` (string, required): The full path of the current folder that the iOS Xcode workspace/project sits
    - `scheme` (string, optional): The specific scheme to build (if not provided, first available scheme will be used)
    - `output_filter` (string, optional): Filter output - 'all' (default), 'errors_only', 'warnings_only', or 'string_match'
    - `filter_string` (string, optional): String to match when output_filter is 'string_match' (required for string_match filter)
- `test` - Run test for iOS Xcode workspace/project
    - `folder` (string, required): The full path of the current folder that the iOS Xcode workspace/project sits
    - `scheme` (string, optional): The specific scheme to build (if not provided, first available scheme will be used)
    - `output_filter` (string, optional): Filter output - 'all' (default), 'errors_only', 'warnings_only', or 'string_match'
    - `filter_string` (string, optional): String to match when output_filter is 'string_match' (required for string_match filter)
- `list_schemes` - List all available schemes for the iOS Xcode workspace/project
    - `folder` (string, required): The full path of the current folder that the iOS Xcode workspace/project sits
- `set_default_scheme` - Set a default scheme to use for future builds and tests (avoids having to specify scheme each time)
    - `folder` (string, required): The full path of the current folder that the iOS Xcode workspace/project sits
    - `scheme` (string, required): The scheme to set as default for future builds/tests
- `get_default_scheme` - Show the currently configured default scheme
    - No parameters required

## Installation


### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *mcpxcodebuild*.

### Using PIP

Alternatively you can install `mcpxcodebuild` via pip:

```
pip install mcpxcodebuild
```

After installation, you can run it as a script using:

```
python -m  mcpxcodebuild
```

## Configuration

### Configure for Claude Desktop App

Add to your Claude settings:

<details>
<summary>Using uvx</summary>

```json
"mcpServers": {
  "mcpxcodebuild": {
    "command": "uvx",
    "args": ["mcpxcodebuild"]
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
"mcpServers": {
  "mcpxcodebuild": {
    "command": "python",
    "args": ["-m", "mcpxcodebuild"]
  }
}
```
</details>

### Configure for Claude Code

Add to your Claude Code configuration by editing `~/.config/claude/claude_desktop_config.json`:

<details>
<summary>Local development setup</summary>

For local development, first install the package locally:
```bash
uv pip install -e .
```

Then add to your config:
```json
{
  "mcpServers": {
    "xcodebuild": {
      "command": "python",
      "args": ["-m", "mcpxcodebuild"]
    }
  }
}
```

Restart Claude Code for the changes to take effect.
</details>

<details>
<summary>Using uvx</summary>

```json
{
  "mcpServers": {
    "xcodebuild": {
      "command": "uvx",
      "args": ["mcpxcodebuild"]
    }
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
{
  "mcpServers": {
    "xcodebuild": {
      "command": "python",
      "args": ["-m", "mcpxcodebuild"]
    }
  }
}
```
</details>

## Usage with Claude Code

Once configured, you can use the xcodebuild MCP server with Claude Code for seamless iOS development workflows. Here are some example interactions:

### Discovering Available Schemes

First, discover what schemes are available in your iOS project:

```
List the available schemes for my iOS project in /path/to/my/ios/project
```

Claude Code will use the `list_schemes` tool to show you all available schemes, such as:
- MyApp
- MyAppTests
- MyAppUITests

### Setting a Default Scheme (Recommended Workflow)

For a more streamlined workflow, set a default scheme once:

```
Set MyApp as the default scheme for my project in /path/to/my/ios/project
```

Check your current default scheme:

```
What is the current default scheme?
```

Once set, you can build and test without specifying the scheme each time!

### Building with Default Scheme

After setting a default scheme, simply build without specifying the scheme:

```
Build my iOS project in /path/to/my/ios/project
```

This will use your configured default scheme automatically!

### Building with Specific Scheme

Build your project using a specific scheme:

```
Build my iOS project in /path/to/my/ios/project using the MyApp scheme
```

**Example with scheme name parameter:**
```
Build the MyApp scheme in /Users/john/MyiOSApp
```

### Running Tests

Run tests for your project (with optional scheme selection):

```
Run tests for my iOS project in /path/to/my/ios/project
```

or with a specific scheme:

```
Run tests for my iOS project in /path/to/my/ios/project using the MyAppTests scheme
```

### Output Filtering

Filter the build/test output to focus on specific information:

**Show only errors:**
```
Build my iOS project in /path/to/my/ios/project and show only errors
```

**Show only warnings:**
```
Build my iOS project in /path/to/my/ios/project and show only warnings
```

**Filter by specific string:**
```
Build my iOS project in /path/to/my/ios/project and show only lines containing "MyClassName"
```

**Example filtering patterns:**
```
Build with errors only: Build /Users/john/MyiOSApp with errors_only filter
Build with warnings only: Build /Users/john/MyiOSApp with warnings_only filter  
Build with string match: Build /Users/john/MyiOSApp filtering for "error:" text
Build with custom filter: Build /Users/john/MyiOSApp and show lines containing "deprecated"
```

**Show all output (default):**
```
Build my iOS project in /path/to/my/ios/project with full output
```

### Workflow Examples

**Recommended workflow with default scheme:**
```
1. List available schemes for my project in /path/to/my/ios/project
2. Set MyApp as the default scheme for my project
3. Build the project (uses default scheme automatically)
4. Run tests (uses default scheme automatically)
```

**Traditional workflow specifying schemes each time:**
```
1. List available schemes for my project in /path/to/my/ios/project
2. Build the project using the MyApp scheme
3. Run tests using the MyAppTests scheme
```

**Mixed workflow (default + override):**
```
1. Set MyApp as default scheme
2. Build the project (uses MyApp)
3. Run tests using the MyAppTests scheme (overrides default for this one command)
```

**Focused debugging workflow:**
```
1. Build the project and show only errors
2. If errors found, fix them and rebuild
3. Build again and show only warnings
4. Run tests and show only lines containing "failed"
```

**Error handling:**
- If you specify an invalid scheme, Claude Code will provide a helpful error message listing all available schemes
- If you use string_match filter without providing a filter_string, you'll get a clear error message
- If no matches are found for your filter, you'll get appropriate "No X found" messages

## License

xcodebuild MCP tool is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.