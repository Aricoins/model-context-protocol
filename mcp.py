#!/usr/bin/env python3
"""
Servidor MCP (Model Context Protocol) completo
Implementación completa del protocolo MCP con todas las funcionalidades
"""

import asyncio
import json
import sys
import os
import logging
import traceback
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes del protocolo MCP
MCP_VERSION = "2024-11-05"

class LoggingLevel(Enum):
    DEBUG = "debug"
    INFO = "info" 
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class PromptMessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class TextContent:
    type: str = "text"
    text: str = ""

@dataclass
class PromptMessage:
    role: PromptMessageRole
    content: TextContent

@dataclass
class PromptArgument:
    name: str
    description: str
    required: bool = True

@dataclass
class Prompt:
    name: str
    description: str
    arguments: List[PromptArgument]

@dataclass
class Tool:
    name: str
    description: str
    inputSchema: Dict[str, Any]

@dataclass
class ServerCapabilities:
    prompts: Dict[str, Prompt]
    tools: Dict[str, Tool]

@dataclass 
class ClientCapabilities:
    experimental: Optional[Dict] = None

@dataclass
class Implementation:
    name: str
    version: str

@dataclass
class InitializeRequest:
    protocolVersion: str
    capabilities: ClientCapabilities
    clientInfo: Implementation

@dataclass
class InitializeResult:
    protocolVersion: str
    capabilities: ServerCapabilities
    serverInfo: Implementation
    instructions: str = "Servidor MCP listo"

@dataclass
class CallToolRequest:
    name: str
    arguments: Dict[str, Any]

@dataclass
class CallToolResult:
    content: List[TextContent]

@dataclass
class GetPromptRequest:
    name: str
    arguments: Dict[str, Any]

@dataclass
class GetPromptResult:
    description: str
    messages: List[PromptMessage]

class MCPError(Exception):
    """Errores específicos del protocolo MCP"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"MCP Error {code}: {message}")

# Códigos de error estándar
class ErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

class MCPServer:
    """Implementación completa de un servidor MCP"""
    
    def __init__(self):
        self.initialized = False
        self.client_capabilities = None
        
        # Configurar capacidades del servidor
        self.prompts = self._setup_prompts()
        self.tools = self._setup_tools()
        
        self.server_capabilities = ServerCapabilities(
            prompts={p.name: p for p in self.prompts},
            tools={t.name: t for t in self.tools}
        )
    
    def _setup_prompts(self) -> List[Prompt]:
        """Configura los prompts disponibles"""
        return [
            Prompt(
                name="code_review",
                description="Revisión de código con enfoque en calidad",
                arguments=[
                    PromptArgument(
                        name="language",
                        description="Lenguaje de programación",
                        required=True
                    ),
                    PromptArgument(
                        name="code", 
                        description="Código a revisar",
                        required=True
                    )
                ]
            ),
            Prompt(
                name="text_summary",
                description="Resumen de textos largos",
                arguments=[
                    PromptArgument(
                        name="text",
                        description="Texto a resumir",
                        required=True
                    ),
                    PromptArgument(
                        name="length",
                        description="Longitud del resumen (palabras)",
                        required=False
                    )
                ]
            )
        ]
    
    def _setup_tools(self) -> List[Tool]:
        """Configura las herramientas disponibles"""
        return [
            Tool(
                name="calculator",
                description="Calculadora científica",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    },
                    "required": ["expression"]
                }
            ),
            Tool(
                name="datetime",
                description="Obtiene la fecha y hora actual",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    async def handle_request(self, request_data: str) -> str:
        """Maneja una solicitud MCP entrante"""
        logger.debug(f"Type of request_data in handle_request: {type(request_data)}, content: {request_data!r}")
        request = json.loads(request_data)
        logger.debug(f"Solicitud recibida: {request}")
        logger.debug(f"Parsed request type: {type(request)}, content: {request}")
        
        # Validar estructura básica
        if "id" not in request or "method" not in request:
            raise MCPError(ErrorCodes.INVALID_REQUEST, "Faltan campos requeridos")
        
        method = request["method"]
        params = request.get("params", {})
        request_id = request["id"]
        
        # Procesar según el método
        result = await self._dispatch_method(method, params)
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
        return json.dumps(response, default=self._json_serializer)
    
    def _json_serializer(self, obj):
        """Serializador JSON personalizado para dataclasses y enums"""
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
    
    def _create_error_response(self, request_id, code: int, message: str) -> str:
        """Crea una respuesta de error"""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        })
    
    async def _dispatch_method(self, method: str, params: Dict[str, Any]) -> Any:
        """Despacha métodos según el protocolo MCP"""
        if method == "initialize":
            return await self._handle_initialize(params)
        elif method == "initialized":
            return await self._handle_initialized(params)
        
        if not self.initialized:
            raise MCPError(ErrorCodes.INVALID_REQUEST, "Servidor no inicializado")
        
        if method == "tools/list":
            return await self._handle_tools_list()
        elif method == "tools/call":
            return await self._handle_tools_call(params)
        elif method == "prompts/list":
            return await self._handle_prompts_list()
        elif method == "prompts/get":
            return await self._handle_prompts_get(params)
        else:
            raise MCPError(ErrorCodes.METHOD_NOT_FOUND, f"Método no encontrado: {method}")
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la inicialización del servidor"""
        # Validar versión del protocolo
        if params.get("protocolVersion") != MCP_VERSION:
            raise MCPError(ErrorCodes.INVALID_PARAMS, f"Versión de protocolo no soportada")
        
        # Guardar capacidades del cliente
        self.client_capabilities = params.get("capabilities", {})
        
        # Resultado de inicialización
        return asdict(InitializeResult(
            protocolVersion=MCP_VERSION,
            capabilities=self.server_capabilities,
            serverInfo=Implementation(
                name="Python MCP Server",
                version="1.0.0"
            )
        ))
    
    async def _handle_initialized(self, params: Dict[str, Any]) -> None:
        """Marca el servidor como inicializado"""
        self.initialized = True
        logger.info("Servidor MCP inicializado correctamente")
        return None
    
    async def _handle_tools_list(self) -> Dict[str, Any]:
        """Lista todas las herramientas disponibles"""
        return {"tools": [asdict(tool) for tool in self.tools]}
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una herramienta específica"""
        if "name" not in params:
            raise MCPError(ErrorCodes.INVALID_PARAMS, "Falta el nombre de la herramienta")
        
        tool_name = params["name"]
        arguments = params.get("arguments", {})
        
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            raise MCPError(ErrorCodes.INVALID_PARAMS, f"Herramienta no encontrada: {tool_name}")
        
        try:
            content = await self._execute_tool(tool_name, arguments)
            result = CallToolResult(content=content)
            return asdict(result)
        except Exception as e:
            logger.error(f"Error ejecutando herramienta {tool_name}: {e}")
            error_content = [TextContent(text=f"Error: {str(e)}")]
            result = CallToolResult(content=error_content)
            return asdict(result)
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Ejecuta una herramienta específica"""
        if tool_name == "calculator":
            import math
            try:
                result = eval(arguments["expression"], {"__builtins__": None}, math.__dict__)
                return [TextContent(text=f"Resultado: {result}")]
            except Exception as e:
                raise ValueError(f"Error de cálculo: {str(e)}")
        
        elif tool_name == "datetime":
            from datetime import datetime
            return [TextContent(text=f"Fecha y hora actual: {datetime.now().isoformat()}")]
        
        raise ValueError(f"Herramienta no implementada: {tool_name}")
    
    async def _handle_prompts_list(self) -> Dict[str, Any]:
        """Lista todos los prompts disponibles"""
        return {"prompts": [asdict(prompt) for prompt in self.prompts]}
    
    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene un prompt específico"""
        if "name" not in params:
            raise MCPError(ErrorCodes.INVALID_PARAMS, "Falta el nombre del prompt")
        
        prompt_name = params["name"]
        arguments = params.get("arguments", {})
        
        prompt = next((p for p in self.prompts if p.name == prompt_name), None)
        if not prompt:
            raise MCPError(ErrorCodes.INVALID_PARAMS, f"Prompt no encontrado: {prompt_name}")
        
        try:
            messages = await self._generate_prompt(prompt, arguments)
            result = GetPromptResult(
                description=prompt.description,
                messages=messages
            )
            return asdict(result)
        except Exception as e:
            logger.error(f"Error generando prompt {prompt_name}: {e}")
            raise MCPError(ErrorCodes.INTERNAL_ERROR, f"Error generando prompt: {str(e)}")
    
    async def _generate_prompt(self, prompt: Prompt, arguments: Dict[str, Any]) -> List[PromptMessage]:
        """Genera mensajes para un prompt específico"""
        # Validar argumentos requeridos
        for arg in prompt.arguments:
            if arg.required and arg.name not in arguments:
                raise ValueError(f"Argumento requerido faltante: {arg.name}")
        
        if prompt.name == "code_review":
            return [
                PromptMessage(
                    role=PromptMessageRole.USER,
                    content=TextContent(
                        text=f"""Revisa este código {arguments['language']}:

{arguments['code']}

Proporciona comentarios sobre:
- Estilo de código
- Posibles errores
- Optimizaciones
"""
                    )
                )
            ]
        
        elif prompt.name == "text_summary":
            length = arguments.get("length", 100)
            return [
                PromptMessage(
                    role=PromptMessageRole.USER,
                    content=TextContent(
                        text=f"Resume el siguiente texto en aproximadamente {length} palabras:\n\n"
                        f"{arguments['text']}"
                    )
                )
            ]
        
        raise ValueError(f"Prompt no implementado: {prompt.name}")
async def handle_client(reader, writer):
    """Maneja una conexión de cliente TCP"""
    mcp_server = MCPServer()
    addr = writer.get_extra_info('peername')
    logger.info(f"Conexión recibida de {addr}")

    while True:
        try:
            data = await reader.readline()
            if not data:
                logger.info(f"Conexión cerrada por {addr}")
                break

            request_str = data.decode().strip()
            logger.debug(f"Raw request string received: {request_str!r}")
            if not request_str:
                continue
            request = json.loads(request_str)

            logger.debug(f"Mensaje recibido de {addr}: {request}")
            response = await mcp_server.handle_request(request_str)
            writer.write(response.encode() + b'\r\n')
            await writer.drain()

        except asyncio.CancelledError:
            break
        except Exception:
            logger.error(f"Error procesando mensaje de {addr}:", exc_info=True)
            break # Close connection on error

    logger.info(f"Cerrando conexión de {addr}")
    writer.close()
    await writer.wait_closed()


async def main():
    """Función principal del servidor MCP"""
    host = '127.0.0.1'
    port = 8888

    server = await asyncio.start_server(
        handle_client, host, port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.info(f'Servidor MCP escuchando en {addrs}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario.")