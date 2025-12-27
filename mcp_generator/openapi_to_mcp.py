import json
import sys
from pathlib import Path


def generate_mcp_from_openapi(openapi_path: str, output_path: str):
    """
    Convert OpenAPI specification into MCP tool definitions
    """

    with open(openapi_path, "r") as f:
        openapi = json.load(f)

    mcp_tools = []

    paths = openapi.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            tool_name = f"{method}_{path}".replace("/", "_").replace("{", "").replace("}", "")

            tool = {
                "name": tool_name,
                "description": details.get("summary", ""),
                "method": method.upper(),
                "path": path,
                "input_schema": {},
                "output_schema": {}
            }

            # Request body (input schema)
            if "requestBody" in details:
                tool["input_schema"] = details["requestBody"]

            # Path parameters
            if "parameters" in details:
                tool["input_schema"]["parameters"] = details["parameters"]

            # Response schema (output schema)
            responses = details.get("responses", {})
            if "200" in responses:
                tool["output_schema"] = responses["200"]

            mcp_tools.append(tool)

    mcp_definition = {
        "protocol": "mcp",
        "version": "1.0",
        "tools": mcp_tools
    }

    with open(output_path, "w") as f:
        json.dump(mcp_definition, f, indent=2)

    print(f"✅ MCP tools generated at: {output_path}")


if __name__ == "__main__":
    """
    Usage:
    python openapi_to_mcp.py openapi.json mcp.json
    """

    if len(sys.argv) != 3:
        print("Usage: python openapi_to_mcp.py <openapi.json> <output_mcp.json>")
        sys.exit(1)

    openapi_path = sys.argv[1]
    output_path = sys.argv[2]

    generate_mcp_from_openapi(openapi_path, output_path)

