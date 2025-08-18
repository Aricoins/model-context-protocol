import asyncio
import json

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
                "name": "MCP Test Client",
                "version": "0.1.0"
            },
            "capabilities": {}
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

    # 4. Send tools/call request
    tool_call_request = {
        "jsonrpc": "2.0",
        "id": 2, # New ID
        "method": "tools/call",
        "params": {
            "name": "datetime",
            "arguments": {}
        }
    }
    print("--> tools/call")
    writer.write(json.dumps(tool_call_request).encode() + b'\n')
    await writer.drain()
    await asyncio.sleep(0.1)

    # 5. Receive tools/call response
    response = await reader.readline()
    print("Respuesta:", json.loads(response.decode()))

    # 6. Close connection
    writer.close()
    await writer.wait_closed()

asyncio.run(mcp_client())
