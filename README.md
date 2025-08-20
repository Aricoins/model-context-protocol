# Model Context Protocol (MCP) Server

## Description

This project provides a complete implementation of the Model Context Protocol (MCP) server, along with a terminal client for interacting with it. The server offers a suite of tools for file manipulation, command execution, and more, all accessible through a simple terminal interface.

The server is built using Python and `asyncio` for asynchronous operations, making it efficient and responsive.

## Getting Started

### Prerequisites

*   Python 3.7+

### Installation

1.  Clone this repository to your local machine.
2.  No additional libraries are needed to run the server or the terminal client.

### Running the Server

To start the MCP server, run the following command in your terminal:

```bash
python mcp.py
```

The server will start and listen on `127.0.0.1:8888`.

### Running the Terminal Client

Once the server is running, open a new terminal window and run the following command:

```bash
python mcp_terminal.py
```

This will connect the terminal to the MCP server, and you'll see a prompt where you can enter commands.

## How to Use

The MCP terminal provides a simple interface for interacting with the server's tools. Here are some examples of how to use it:

*   **List files in the current directory:**
    ```
    > list_files
    ```

*   **Read the content of a file:**
    ```
    > read_file test_file.txt
    ```

*   **Write content to a file:**
    ```
    > write_file new_file.txt "Hello, MCP!"
    ```

*   **Create a new directory:**
    ```
    > create_directory new_folder
    ```

*   **Run a shell command:**
    ```
    > run_command echo "Hello from the terminal"
    ```

## Tools

The MCP server provides the following tools:

| Tool               | Description                                       |
| ------------------ | ------------------------------------------------- |
| `read_file`        | Reads the content of a file.                      |
| `write_file`       | Writes content to a file.                         |
| `list_files`       | Lists files and directories in a path.            |
| `create_directory` | Creates a new directory.                          |
| `delete_path`      | Deletes a file or directory.                      |
| `run_command`      | Executes a command in the terminal.               |
| `search_files`     | Searches for files by name or pattern.            |
| `file_info`        | Gets detailed information about a file.           |
| `calculator`       | A simple scientific calculator.                   |
| `datetime`         | Gets the current date and time.                   |
| `terminal_execute` | Executes a command in the terminal.               |

## Prompts

The MCP server also provides the following prompts:

| Prompt             | Description                               |
| ------------------ | ----------------------------------------- |
| `code_review`      | Reviews code for quality and errors.      |
| `code_explanation` | Explains how a piece of code works.       |
| `create_test`      | Generates tests for a given piece of code.|

## Development

For development and testing purposes, a test client is included in `mcp_client.py`. This client connects to the server and runs a series of predefined tests to ensure that all tools are working correctly.

To run the test client, make sure the server is running, and then execute the following command:

```bash
python mcp_client.py
```

The client will print the requests it sends to the server and the responses it receives, allowing you to see the communication between the client and the server in detail.