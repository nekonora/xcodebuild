from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ErrorData,
    TextContent,
    Tool,
    INVALID_PARAMS,
)
from typing import Annotated, Optional
from pydantic import Field
from pydantic import BaseModel
from enum import Enum
import subprocess
import os
import json
from mcp.shared.exceptions import McpError

# Global default scheme configuration
default_scheme: Optional[str] = None

class OutputFilter(str, Enum):
    ALL = "all"
    ERRORS_ONLY = "errors_only"
    WARNINGS_ONLY = "warnings_only"
    ERRORS_AND_WARNINGS = "errors_and_warnings"
    STRING_MATCH = "string_match"

def find_xcode_project():
    for root, dirs, files in os.walk("."):
        dirs.sort(reverse = True)
        for dir in dirs:
            if dir.endswith(".xcworkspace") or dir.endswith(".xcodeproj"):
                return os.path.join(root, dir)
    return None

def get_available_schemes(project_type: str, project_name: str) -> list[str]:
    schemes_result = subprocess.run(["xcodebuild",
                                    "-list",
                                    project_type,
                                    project_name],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    check=False).stdout.decode("utf-8")
    
    schemes_lines = schemes_result.splitlines()
    schemes = []
    in_schemes_section = False
    for line in schemes_lines:
        if "Schemes:" in line:
            in_schemes_section = True
            continue
        if in_schemes_section:
            scheme = line.strip()
            if scheme:
                schemes.append(scheme)
    
    return schemes

def find_scheme(project_type: str, project_name: str, requested_scheme: Optional[str] = None) -> str:
    global default_scheme
    available_schemes = get_available_schemes(project_type, project_name)
    
    # Priority: requested_scheme > default_scheme > first available
    scheme_to_use = requested_scheme or default_scheme
    
    if scheme_to_use:
        if scheme_to_use in available_schemes:
            return scheme_to_use
        else:
            raise ValueError(f"Scheme '{scheme_to_use}' not found. Available schemes: {', '.join(available_schemes)}")
    
    if available_schemes:
        return available_schemes[0]
    else:
        return ""

def filter_build_output(lines: list[str], output_filter: OutputFilter, filter_string: Optional[str] = None) -> str:
    """Filter xcodebuild output based on the specified filter type"""
    
    if output_filter == OutputFilter.ALL:
        # Return all output but with size limits to prevent overwhelming AI agents
        MAX_LINES = 200
        if len(lines) > MAX_LINES:
            summary_lines = [
                f"[Output truncated - showing last {MAX_LINES} lines of {len(lines)} total lines]",
                ""
            ]
            filtered_lines = summary_lines + lines[-MAX_LINES:]
        else:
            filtered_lines = lines
    elif output_filter == OutputFilter.ERRORS_ONLY:
        # Only lines containing "error:"
        filtered_lines = [line for line in lines if "error:" in line.lower()]
    elif output_filter == OutputFilter.WARNINGS_ONLY:
        # Only lines containing "warning:"
        filtered_lines = [line for line in lines if "warning:" in line.lower()]
    elif output_filter == OutputFilter.ERRORS_AND_WARNINGS:
        # Lines containing either "error:" or "warning:"
        filtered_lines = [line for line in lines if "error:" in line.lower() or "warning:" in line.lower()]
    elif output_filter == OutputFilter.STRING_MATCH:
        # Lines containing the specified string
        if not filter_string:
            raise ValueError("filter_string is required when output_filter is 'string_match'")
        filtered_lines = [line for line in lines if filter_string.lower() in line.lower()]
    else:
        # Default to errors and warnings if unknown filter
        filtered_lines = [line for line in lines if "error:" in line.lower() or "warning:" in line.lower()]
    
    if not filtered_lines:
        if output_filter == OutputFilter.ERRORS_ONLY:
            return "No errors found"
        elif output_filter == OutputFilter.WARNINGS_ONLY:
            return "No warnings found"
        elif output_filter == OutputFilter.ERRORS_AND_WARNINGS:
            return "No errors or warnings found"
        elif output_filter == OutputFilter.STRING_MATCH:
            return f"No lines matching '{filter_string}' found"
        else:
            return "No output"
    
    return "\n".join(filtered_lines)

def find_available_simulator() -> str:
    devices_result = subprocess.run(["xcrun", "simctl", "list", "devices", "--json"], stdout=subprocess.PIPE, check=False)
    devices_json = json.loads(devices_result.stdout.decode("utf-8"))
    
    for runtime_id, devices in devices_json["devices"].items():
        if "iOS" in runtime_id:
            for device in devices:
                if device["isAvailable"]:
                    # Extract the exact OS version from the runtime ID
                    # Format: com.apple.CoreSimulator.SimRuntime.iOS-18-3-1 -> 18.3.1
                    ios_version = runtime_id.split("iOS-")[-1].replace("-", ".")
                    return f'platform=iOS Simulator,name={device["name"]},OS={ios_version}'
    return ""

def build_destination(simulator_name: Optional[str] = None, ios_version: Optional[str] = None) -> str:
    """Build the destination string for xcodebuild command"""
    if simulator_name and ios_version:
        # Use provided simulator name and iOS version
        return f'platform=iOS Simulator,name={simulator_name},OS={ios_version}'
    elif simulator_name or ios_version:
        # If only one is provided, we need to find a matching simulator
        devices_result = subprocess.run(["xcrun", "simctl", "list", "devices", "--json"], stdout=subprocess.PIPE, check=False)
        devices_json = json.loads(devices_result.stdout.decode("utf-8"))
        
        for runtime_id, devices in devices_json["devices"].items():
            if "iOS" in runtime_id:
                runtime_ios_version = runtime_id.split("iOS-")[-1].replace("-", ".")
                
                # Skip if iOS version is specified but doesn't match
                if ios_version and runtime_ios_version != ios_version:
                    continue
                    
                for device in devices:
                    if device["isAvailable"]:
                        # Skip if simulator name is specified but doesn't match
                        if simulator_name and device["name"] != simulator_name:
                            continue
                        
                        return f'platform=iOS Simulator,name={device["name"]},OS={runtime_ios_version}'
        
        # If no matching simulator found, raise an error
        criteria = []
        if simulator_name:
            criteria.append(f"name={simulator_name}")
        if ios_version:
            criteria.append(f"OS={ios_version}")
        raise ValueError(f"No available simulator found matching criteria: {', '.join(criteria)}")
    else:
        # Use auto-detection (existing behavior)
        return find_available_simulator()
class BuildParams(BaseModel):
    """Parameters"""
    folder: Annotated[str, Field(description="The full path of the current folder that the iOS Xcode workspace/project sits")]
    scheme: Annotated[Optional[str], Field(description="The specific scheme to build (optional - if not provided, first available scheme will be used)", default=None)]
    simulator_name: Annotated[Optional[str], Field(description="The iOS simulator name to use (e.g., 'iPhone 16', 'iPad Pro') - if not provided, first available simulator will be used", default=None)]
    ios_version: Annotated[Optional[str], Field(description="The iOS version to use (e.g., '18.3.1', '17.5') - if not provided, version from first available simulator will be used", default=None)]
    output_filter: Annotated[OutputFilter, Field(description="Filter output: 'all' (limited to last 200 lines), 'errors_only', 'warnings_only', 'errors_and_warnings' (recommended for AI agents), or 'string_match'", default=OutputFilter.ALL)]
    filter_string: Annotated[Optional[str], Field(description="String to match when output_filter is 'string_match' (required for string_match filter)", default=None)]

class Folder(BaseModel):
    """Parameters"""
    folder: Annotated[str, Field(description="The full path of the current folder that the iOS Xcode workspace/project sits")]

class SchemeConfig(BaseModel):
    """Parameters for setting default scheme"""
    folder: Annotated[str, Field(description="The full path of the current folder that the iOS Xcode workspace/project sits")]
    scheme: Annotated[str, Field(description="The scheme to set as default for future builds/tests")]

server = Server("build")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name = "build",
            description = "Build the iOS Xcode workspace/project in the folder",
            inputSchema = BuildParams.model_json_schema(),
        ),
        Tool(
            name="test",
            description="Run test for the iOS Xcode workspace/project in the folder",
            inputSchema=BuildParams.model_json_schema(),
        ),
        Tool(
            name="list_schemes",
            description="List all available schemes for the iOS Xcode workspace/project in the folder",
            inputSchema=Folder.model_json_schema(),
        ),
        Tool(
            name="set_default_scheme",
            description="Set a default scheme to use for future builds and tests (avoids having to specify scheme each time)",
            inputSchema=SchemeConfig.model_json_schema(),
        ),
        Tool(
            name="get_default_scheme",
            description="Show the currently configured default scheme",
            inputSchema={"type": "object"},
        )
    ]
@server.call_tool()
async def call_tool(name, arguments: dict) -> list[TextContent]:
    global default_scheme
    
    if name == "set_default_scheme":
        try:
            args = SchemeConfig(**arguments)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
        os.chdir(args.folder)
        xcode_project_path = find_xcode_project()
        if not xcode_project_path:
            return [TextContent(type="text", text="No Xcode project found in the specified folder")]
        
        project_name = os.path.basename(xcode_project_path)
        project_type = "-workspace" if xcode_project_path.endswith(".xcworkspace") else "-project"
        
        # Validate that the scheme exists
        available_schemes = get_available_schemes(project_type, project_name)
        if args.scheme not in available_schemes:
            return [TextContent(type="text", text=f"Scheme '{args.scheme}' not found. Available schemes: {', '.join(available_schemes)}")]
        
        # Set the default scheme
        default_scheme = args.scheme
        return [TextContent(type="text", text=f"Default scheme set to '{args.scheme}'. Future builds and tests will use this scheme unless explicitly overridden.")]
    
    if name == "get_default_scheme":
        if default_scheme:
            return [TextContent(type="text", text=f"Current default scheme: '{default_scheme}'")]
        else:
            return [TextContent(type="text", text="No default scheme configured. Builds will use the first available scheme.")]
    
    if name == "list_schemes":
        try:
            args = Folder(**arguments)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
        os.chdir(args.folder)
        xcode_project_path = find_xcode_project()
        if not xcode_project_path:
            return [TextContent(type="text", text="No Xcode project found in the specified folder")]
        
        project_name = os.path.basename(xcode_project_path)
        project_type = "-workspace" if xcode_project_path.endswith(".xcworkspace") else "-project"
        
        schemes = get_available_schemes(project_type, project_name)
        if schemes:
            return [TextContent(type="text", text="Available schemes:\n" + "\n".join(f"- {scheme}" for scheme in schemes))]
        else:
            return [TextContent(type="text", text="No schemes found")]
    
    try:
        args = BuildParams(**arguments)
    except ValueError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
    
    # Validate filter_string requirement for string_match filter
    if args.output_filter == OutputFilter.STRING_MATCH and not args.filter_string:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="filter_string is required when output_filter is 'string_match'"))
    
    os.chdir(args.folder)
    xcode_project_path = find_xcode_project()
    if not xcode_project_path:
        return [TextContent(type="text", text="No Xcode project found in the specified folder")]
    
    project_name = os.path.basename(xcode_project_path)
    project_type = "-workspace" if xcode_project_path.endswith(".xcworkspace") else "-project"

    try:
        scheme = find_scheme(project_type, project_name, args.scheme)
        destination = build_destination(args.simulator_name, args.ios_version)
    except ValueError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
    command = ["xcodebuild",
               project_type,
               project_name,
               "-scheme",
               scheme,
               "-destination",
               destination]
    if name == "test":
        command.append("test")

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    
    # Combine stdout and stderr for complete output
    stdout_lines = result.stdout.decode("utf-8").splitlines()
    stderr_lines = result.stderr.decode("utf-8").splitlines()
    all_lines = stdout_lines + stderr_lines
    
    filtered_output = filter_build_output(all_lines, args.output_filter, args.filter_string)
    
    # Include build status information
    status_text = f"Build {'succeeded' if result.returncode == 0 else 'failed'} (exit code: {result.returncode})"
    
    return [
        TextContent(type="text", text=f"Command: {' '.join(command)}"),
        TextContent(type="text", text=status_text),
        TextContent(type="text", text=filtered_output)
        ]


async def run():
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            options,
            raise_exceptions=True,
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
