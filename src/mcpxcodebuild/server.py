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
import subprocess
import os
import json
from mcp.shared.exceptions import McpError

# Global default scheme configuration
default_scheme: Optional[str] = None

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

def find_available_simulator() -> str:
    devices_result = subprocess.run(["xcrun", "simctl", "list", "devices", "--json"], stdout=subprocess.PIPE, check=False)
    devices_json = json.loads(devices_result.stdout.decode("utf-8"))
    
    for runtime_id, devices in devices_json["devices"].items():
        if "iOS" in runtime_id:
            for device in devices:
                if device["isAvailable"]:
                    return f'platform=iOS Simulator,name={device["name"]},OS={runtime_id.split(".")[-1].replace("iOS-", "").replace("-", ".")}'
    return ""
class BuildParams(BaseModel):
    """Parameters"""
    folder: Annotated[str, Field(description="The full path of the current folder that the iOS Xcode workspace/project sits")]
    scheme: Annotated[Optional[str], Field(description="The specific scheme to build (optional - if not provided, first available scheme will be used)", default=None)]

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
            inputSchema={},
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
    os.chdir(args.folder)
    xcode_project_path = find_xcode_project()
    if not xcode_project_path:
        return [TextContent(type="text", text="No Xcode project found in the specified folder")]
    
    project_name = os.path.basename(xcode_project_path)
    project_type = "-workspace" if xcode_project_path.endswith(".xcworkspace") else "-project"

    try:
        scheme = find_scheme(project_type, project_name, args.scheme)
    except ValueError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
    destination = find_available_simulator()
    command = ["xcodebuild",
               project_type,
               project_name,
               "-scheme",
               scheme,
               "-destination",
               destination]
    if name == "test":
        command.append("test")

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False).stdout
    
    lines = result.decode("utf-8").splitlines()
    error_lines = [line for line in lines if "error:" or "warning:" in line.lower()]
    error_message = "\n".join(error_lines)
    if not error_message:
        error_message = "Successful"
    return [
        TextContent(type="text", text=f"Command: {' '.join(command)}"),
        TextContent(type="text", text=f"{error_message}")
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
