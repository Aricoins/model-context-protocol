# Model Context Protocol (MCP) Server

## Description

This is a complete implementation of the Model Context Protocol (MCP) server. It provides functionalities such as:

*   Handling client connections
*   Serving prompts
*   Executing tools

The server is built using Python and asyncio for asynchronous operations.

## Features

*   **MCP Version**: 2024-11-05
*   **Prompts**: Code review, text summary
*   **Tools**: Calculator, datetime

## Requirements

*   Python 3.7+
*   asyncio
*   json
*   logging
*   typing
*   dataclasses
*   enum

## Usage

1.  Clone the repository.
2.  Run the `mcp.py` script.
3.  The server listens on host `127.0.0.1` and port `8888`.

## Implementation Details

*   The server uses JSON for request and response serialization.
*   Custom JSON serializer for dataclasses and enums.
*   Error handling with specific MCP error codes.

## Classes

*   `MCPServer`: Main class implementing the MCP server.
*   `MCPError`: Custom exception for MCP errors.

## Data Classes

*   `TextContent`
*   `PromptMessage`
*   `PromptArgument`
*   `Prompt`
*   `Tool`
*   `ServerCapabilities`
*   `ClientCapabilities`
*   `Implementation`
*   `InitializeRequest`
*   `InitializeResult`
*   `CallToolRequest`
*   `CallToolResult`
*   `GetPromptRequest`
*   `GetPromptResult`

## Enums

*   `LoggingLevel`
*   `PromptMessageRole`

## Logging

The server uses the logging module to provide detailed information about its operations.

## Error Codes

*   `PARSE_ERROR`
*   `INVALID_REQUEST`
*   `METHOD_NOT_FOUND`
*   `INVALID_PARAMS`
*   `INTERNAL_ERROR`

## Protocol

The server implements the Model Context Protocol with `initialize`, `initialized`, `tools/list`, `tools/call`, `prompts/list`, and `prompts/get` methods.

## Example Usage

To run the server:

```bash
python mcp.py
```
