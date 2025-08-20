#!/usr/bin/env python3

import asyncio
import json
import os #revisar doc
import subprocess
import sys

# Global variables for the MCP connection
mcp_reader = None
mcp_writer = None
mcp_initialized = False

async def initialize_mcp_server(config):
    """
    Initializes the connection to the MCP server.
    """
    global mcp_reader, mcp_writer, mcp_initialized
    try:
        mcp_reader, mcp_writer = await asyncio.open_connection(config['mcp_server']['host'], config['mcp_server']['port'])

        # 1. Send initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "MCP Terminal",
                    "version": "0.1.0"
                },
                "capabilities": {},
                "workspaceFolders": [
                    {
                        "uri": f"file://{os.getcwd()}",
                        "name": "MCPWorkspace"
                    }
                ]
            }
        }
        print("--> MCP Initialize")
        mcp_writer.write(json.dumps(initialize_request).encode() + b'\n')
        await mcp_writer.drain()

        # 2. Receive initialize response
        response = await mcp_reader.readline()
        print(f"<-- MCP Response: {json.loads(response.decode())}")

        # 3. Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        print("--> MCP Initialized")
        mcp_writer.write(json.dumps(initialized_notification).encode() + b'\n')
        await mcp_writer.drain()
        mcp_initialized = True
        print("MCP Server Initialized Successfully.")

    except Exception as e:
        print(f"Error initializing MCP server: {e}")
        mcp_initialized = False


async def run_mcp_client(config, message):
    """
    Connects to the MCP server and sends a message.
    """
    global mcp_reader, mcp_writer, mcp_initialized
    if not mcp_initialized:
        print("MCP Server not initialized. Please restart the terminal.")
        return

    try:
        # Craft a simplified request (adjust as needed for your MCP server)
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "terminal/execute",
            "params": {
                "command": message
            }
        }

        mcp_writer.write(json.dumps(request).encode() + b'\n')
        await mcp_writer.drain()

        response = await mcp_reader.readline()
        print(f"<-- MCP Response: {json.loads(response.decode())}")

    except Exception as e:
        print(f"Error communicating with MCP server: {e}")


async def main():
    """
    Main function to run the terminal application.
    """
    try:
        with open('terminal_interface_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: terminal_interface_config.json not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in terminal_interface_config.json.")
        sys.exit(1)

    # Initialize MCP Server
    await initialize_mcp_server(config)

    current_model = "cloud"  # Default model
    local_process = None # To store the local model subprocess
    print(f"Loaded configuration.  Using {current_model} model initially.")

    while True:
        prompt = config['prompt']
        user_input = input(prompt)

        if user_input.lower() == 'exit':
            print("Exiting...")
            if mcp_writer:
                mcp_writer.close()
                await mcp_writer.wait_closed()
            break
        elif user_input.lower() == 'switch':
            if current_model == "cloud":
                current_model = "local"
                print("Switched to local model.")
            else:
                current_model = "cloud"
                print("Switched to cloud model.")
            continue # Skip to the next input


        # Process the user input based on the selected model
        if current_model == "cloud":
            print(f"Sending to cloud model ({config['cloud_model']['name']}): {user_input}")
            # In a real application, you would send the user_input
            # to the cloud model API and print the response.
        else:
            # Local Model interaction using subprocess
            local_model_command = config['local_model']['command']
            try:
                local_process = subprocess.Popen(
                    local_model_command,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Send input to the local model
                local_process.stdin.write(user_input + '\n')
                local_process.stdin.flush()

                # Capture the output
                local_output = local_process.stdout.read()
                print(f"Local Model Output: {local_output}")

                local_process.stdin.close()
                local_process.wait()

            except Exception as e:
                print(f"Error interacting with local model: {e}")

        # Send the user input to the MCP server
        await run_mcp_client(config, user_input)

if __name__ == "__main__":
    asyncio.run(main())