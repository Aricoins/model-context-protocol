#!/usr/bin/env python3
"""
Cliente MCP de prueba para VS Code
Prueba todas las funcionalidades de manipulación de archivos y terminal
"""

import asyncio
import json
import os

async def mcp_client():
    reader, writer = await asyncio.open_connection('localhost', 8888)

    # 1. Send initialize request
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "VS Code MCP Client",
                "version": "0.1.0"
            },
            "capabilities": {},
            "workspaceFolders": [
                {
                    "uri": f"file://{os.getcwd()}",
                    "name": "TestWorkspace"
                }
            ]
        }
    }
    print("--> initialize")
    writer.write(json.dumps(initialize_request).encode() + b'\n')
    await writer.drain()
    await asyncio.sleep(0.1)

    # 2. Receive initialize response
    response = await reader.readline()
    print("<--", json.loads(response.decode()))
    await asyncio.sleep(0.1)

    # 3. Send initialized notification
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {}
    }
    print("--> initialized")
    writer.write(json.dumps(initialized_notification).encode() + b'\n')
    await writer.drain()
    await asyncio.sleep(0.1)

    # 4. Test tools/call with datetime
    tool_call_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "datetime",
            "arguments": {}
        }
    }
    print("--> tools/call (datetime)")
    writer.write(json.dumps(tool_call_request).encode() + b'\n')
    await writer.drain()
    await asyncio.sleep(0.1)

    # 5. Receive tools/call response for datetime
    response = await reader.readline()
    print("<--", json.loads(response.decode()))
    await asyncio.sleep(0.1)

    # 6. Test write_file
    write_file_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "write_file",
            "arguments": {
                "path": "test_file.txt",
                "content": "Este es un archivo de prueba\nCreado por el servidor MCP\n"
            }
        }
    }
    print("--> tools/call (write_file)")
    writer.write(json.dumps(write_file_request).encode() + b'\n')
    await writer.drain()
    await asyncio.sleep(0.1)

    # 7. Receive write_file response
    response = await reader.readline()
    print("<--", json.loads(response.decode()))
    await asyncio.sleep(0.1)

    # 8. Test read_file
    read_file_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "read_file",
            "arguments": {
                "path": "test_file.txt"
            }
        }
    }
    print("--> tools/call (read_file)")
    writer.write(json.dumps(read_file_request).encode() + b'\n')
    await writer.drain()
    await asyncio.sleep(0.1)

    # 9. Receive read_file response
    response = await reader.readline()
    print("<--", json.loads(response.decode()))
    await asyncio.sleep(0.1)

    # 10. Test list_files
    list_files_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "list_files",
            "arguments": {}
        }
    }
    print("--> tools/call (list_files)")
    writer.write(json.dumps(list_files_request).encode() + b'\n')
    await writer.drain()
    await asyncio.sleep(0.1)

    # 11. Receive list_files response
    response = await reader.readline()
    print("<--", json.loads(response.decode()))
    await asyncio.sleep(0.1)

    # 12. Test run_command
    run_command_request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "run_command",
            "arguments": {
                "command": "echo 'Hola desde MCP'"
            }
        }
    }
    print("--> tools/call (run_command)")
    writer.write(json.dumps(run_command_request).encode() + b'\n')
    await writer.drain()
    await asyncio.sleep(0.1)

    # 13. Receive run_command response
    response = await reader.readline()
    print("<--", json.loads(response.decode()))
    await asyncio.sleep(0.1)

    # 14. Close connection
    writer.close()
    await writer.wait_closed()

asyncio.run(mcp_client())