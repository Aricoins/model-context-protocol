#!/usr/bin/env python3
"""
Servidor MCP para VS Code - Manipulación de archivos y terminal
"""

import asyncio
import json
import logging
import math
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MCP_VERSION = "2024-11-05"

class MCPServer:
    """Servidor MCP para manipulación de archivos y terminal en VS Code"""
    
    def __init__(self):
        self.initialized = False
        self.workspace_root = os.getcwd()  # Directorio de trabajo actual
        self.capabilities = {
            "tools": self._setup_tools(),
            "prompts": self._setup_prompts(),
            "resources": self._setup_resources()
        }
    
    def _setup_tools(self) -> Dict[str, Any]:
        """Configura todas las herramientas disponibles"""
        return {
            "read_file": {
                "name": "read_file",
                "description": "Lee el contenido de un archivo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del archivo"}
                    },
                    "required": ["path"]
                }
            },
            "write_file": {
                "name": "write_file",
                "description": "Escribe contenido en un archivo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del archivo"},
                        "content": {"type": "string", "description": "Contenido a escribir"},
                        "append": {"type": "boolean", "description": "Añadir al final en lugar de sobrescribir"}
                    },
                    "required": ["path", "content"]
                }
            },
            "list_files": {
                "name": "list_files",
                "description": "Lista archivos y directorios en una ruta",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta a listar (por defecto: directorio actual)"}
                    },
                    "required": []
                }
            },
            "create_directory": {
                "name": "create_directory",
                "description": "Crea un directorio",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del directorio a crear"}
                    },
                    "required": ["path"]
                }
            },
            "delete_path": {
                "name": "delete_path",
                "description": "Elimina un archivo o directorio",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta a eliminar"}
                    },
                    "required": ["path"]
                }
            },
            "run_command": {
                "name": "run_command",
                "description": "Ejecuta un comando en la terminal",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Comando a ejecutar"},
                        "cwd": {"type": "string", "description": "Directorio de trabajo"}
                    },
                    "required": ["command"]
                }
            },
            "search_files": {
                "name": "search_files",
                "description": "Busca archivos por nombre o patrón",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Patrón de búsqueda (ej: *.py)"},
                        "path": {"type": "string", "description": "Ruta donde buscar (por defecto: directorio actual)"}
                    },
                    "required": ["pattern"]
                }
            },
            "file_info": {
                "name": "file_info",
                "description": "Obtiene información detallada de un archivo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del archivo"}
                    },
                    "required": ["path"]
                }
            },
            "calculator": {
                "name": "calculator",
                "description": "Calculadora científica",
                "inputSchema": {
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"]
                }
            },
            "terminal_execute": {
                "name": "terminal_execute",
                "description": "Ejecuta un comando en la terminal",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Comando a ejecutar"}
                    },
                    "required": ["command"]
                }
            },
            "datetime": {
                "name": "datetime", 
                "description": "Obtiene la fecha y hora actual",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    
    def _setup_prompts(self) -> Dict[str, Any]:
        """Configura todos los prompts disponibles"""
        return {
            "code_review": {
                "name": "code_review",
                "description": "Revisión de código con enfoque en calidad",
                "arguments": [
                    {"name": "language", "description": "Lenguaje de programación", "required": True},
                    {"name": "code", "description": "Código a revisar", "required": True}
                ]
            },
            "code_explanation": {
                "name": "code_explanation",
                "description": "Explica el funcionamiento de un código",
                "arguments": [
                    {"name": "language", "description": "Lenguaje de programación", "required": True},
                    {"name": "code", "description": "Código a explicar", "required": True}
                ]
            },
            "create_test": {
                "name": "create_test",
                "description": "Genera tests para un código dado",
                "arguments": [
                    {"name": "language", "description": "Lenguaje de programación", "required": True},
                    {"name": "code", "description": "Código para el cual crear tests", "required": True},
                    {"name": "framework", "description": "Framework de testing a usar", "required": False}
                ]
            }
        }
    
    def _setup_resources(self) -> Dict[str, Any]:
        """Configura recursos disponibles (para futuras extensiones)"""
        return {}
    
    def _resolve_path(self, path: str) -> str:
        """Resuelve una ruta relativa a absoluta dentro del workspace"""
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.workspace_root, path))
    
    async def handle_request(self, request_data: str) -> str:
        """Maneja una solicitud MCP entrante"""
        try:
            request = json.loads(request_data)
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")
            
            logger.info(f"Procesando método: {method}, ID: {request_id}")
            
            if method == "initialize":
                result = await self.handle_initialize(params)
                return self._create_response(request_id, result)
            
            if not self.initialized and method != "initialized":
                return self._create_error_response(request_id, -32002, "Servidor no inicializado")
            
            if method == "initialized":
                result = await self.handle_initialized(params)
                return "" if request_id is None else self._create_response(request_id, result)
            
            elif method == "tools/list":
                result = await self.handle_tools_list()
                return self._create_response(request_id, result)
            
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
                return self._create_response(request_id, result)
            
            elif method == "prompts/list":
                result = await self.handle_prompts_list()
                return self._create_response(request_id, result)
            
            elif method == "prompts/get":
                result = await self.handle_prompts_get(params)
                return self._create_response(request_id, result)
            elif method == "terminal/execute":
                result = await self.handle_terminal_execute(params)
                return self._create_response(request_id, result)
            
            else:
                return self._create_error_response(request_id, -32601, f"Método no encontrado: {method}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
            return self._create_error_response(None, -32700, "Error de análisis JSON")
        except Exception as e:
            logger.error(f"Error procesando solicitud: {e}")
            return self._create_error_response(request_id, -32603, f"Error interno: {str(e)}")

    async def handle_terminal_execute(self, params):
        """Ejecuta un comando en la terminal."""
        command = params.get("command")
        if not command:
            return {"content": [{"type": "text", "text": "Comando no proporcionado"}]}

        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=self.workspace_root)
            stdout = process.stdout
            stderr = process.stderr
            return_code = process.returncode

            return {
                "content": [{"type": "text",
                             "text": f"Comando ejecutado:\n{command}\n\nSalida:\n{stdout}\nErrores:\n{stderr}\nCódigo de retorno: {return_code}"}]
            }
        except Exception as e:
            logger.error(f"Error al ejecutar el comando: {e}")
            return {
                "content": [{"type": "text", "text": f"Error al ejecutar el comando: {e}"}]
            }

    
    def _create_response(self, request_id, result):
        """Crea una respuesta JSON-RPC válida"""
        if request_id is None:
            return ""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        })
    
    def _create_error_response(self, request_id, code, message):
        """Crea una respuesta de error JSON-RPC"""
        if request_id is None:
            return ""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        })
    
    async def handle_initialize(self, params):
        """Maneja la inicialización del servidor"""
        if params.get("protocolVersion") != MCP_VERSION:
            raise Exception(f"Versión de protocolo no soportada: {params.get('protocolVersion')}")
        
        # Establecer el directorio de trabajo si se proporciona
        workspace_dirs = params.get("workspaceFolders", [])
        if workspace_dirs:
            self.workspace_root = workspace_dirs[0].get("uri", "").replace("file://", "")
            if os.name == 'nt':  # Windows
                self.workspace_root = self.workspace_root.lstrip('/')
        
        return {
            "protocolVersion": MCP_VERSION,
            "capabilities": self.capabilities,
            "serverInfo": {"name": "VS Code MCP Server", "version": "1.0.0"},
            "instructions": "Servidor MCP para manipulación de archivos y terminal en VS Code"
        }
    
    async def handle_initialized(self, params):
        """Marca el servidor como inicializado"""
        self.initialized = True
        logger.info(f"Servidor MCP inicializado. Workspace: {self.workspace_root}")
        return None
    
    async def handle_tools_list(self):
        """Lista todas las herramientas disponibles"""
        return {"tools": list(self.capabilities["tools"].values())}
    
    async def handle_tools_call(self, params):
        """Ejecuta una herramienta específica"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "read_file":
            return await self._tool_read_file(arguments)
        elif tool_name == "write_file":
            return await self._tool_write_file(arguments)
        elif tool_name == "list_files":
            return await self._tool_list_files(arguments)
        elif tool_name == "create_directory":
            return await self._tool_create_directory(arguments)
        elif tool_name == "delete_path":
            return await self._tool_delete_path(arguments)
        elif tool_name == "run_command":
            return await self._tool_run_command(arguments)
        elif tool_name == "search_files":
            return await self._tool_search_files(arguments)
        elif tool_name == "file_info":
            return await self._tool_file_info(arguments)
        elif tool_name == "calculator":
            return await self._tool_calculator(arguments)
        elif tool_name == "datetime":
            return await self._tool_datetime(arguments)
        
        return {"content": [{"type": "text", "text": f"Herramienta no encontrada: {tool_name}"}]}
    
    async def _tool_read_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Lee el contenido de un archivo"""
        path = self._resolve_path(arguments.get("path", ""))
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Contenido de {path}:\n\n{content}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error leyendo archivo {path}: {str(e)}"
                }]
            }
    
    async def _tool_write_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Escribe contenido en un archivo"""
        path = self._resolve_path(arguments.get("path", ""))
        content = arguments.get("content", "")
        append = arguments.get("append", False)
        
        try:
            # Crear directorios padres si no existen
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            
            action = "Añadido a" if append else "Escrito en"
            return {
                "content": [{
                    "type": "text", 
                    "text": f"{action} archivo: {path}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error escribiendo archivo {path}: {str(e)}"
                }]
            }
    
    async def _tool_list_files(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Lista archivos y directorios en una ruta"""
        path = arguments.get("path", "")
        target_path = self._resolve_path(path) if path else self.workspace_root
        
        try:
            if not os.path.exists(target_path):
                return {
                    "content": [{
                        "type": "text", 
                        "text": f"La ruta no existe: {target_path}"
                    }]
                }
            
            items = []
            for item in os.listdir(target_path):
                item_path = os.path.join(target_path, item)
                is_dir = os.path.isdir(item_path)
                items.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "size": os.path.getsize(item_path) if not is_dir else 0
                })
            
            # Ordenar: directorios primero, luego archivos
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            items_text = "\n".join([
                f"[DIR]  {item['name']}" if item["type"] == "directory" 
                else f"[FILE] {item['name']} ({item['size']} bytes)"
                for item in items
            ])
            
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Contenido de {target_path}:\n\n{items_text}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error listando directorio {target_path}: {str(e)}"
                }]
            }
    
    async def _tool_create_directory(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un directorio"""
        path = self._resolve_path(arguments.get("path", ""))
        
        try:
            os.makedirs(path, exist_ok=True)
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Directorio creado: {path}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error creando directorio {path}: {str(e)}"
                }]
            }
    
    async def _tool_delete_path(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina un archivo o directorio"""
        path = self._resolve_path(arguments.get("path", ""))
        
        try:
            if not os.path.exists(path):
                return {
                    "content": [{
                        "type": "text", 
                        "text": f"La ruta no existe: {path}"
                    }]
                }
            
            if os.path.isdir(path):
                shutil.rmtree(path)
                action = "Directorio eliminado"
            else:
                os.remove(path)
                action = "Archivo eliminado"
            
            return {
                "content": [{
                    "type": "text", 
                    "text": f"{action}: {path}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error eliminando {path}: {str(e)}"
                }]
            }
    
    async def _tool_run_command(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta un comando en la terminal"""
        command = arguments.get("command", "")
        cwd = arguments.get("cwd", "")
        working_dir = self._resolve_path(cwd) if cwd else self.workspace_root
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Comando ejecutado en {working_dir}:\n{command}\n\nResultado:\n{json.dumps(output, indent=2)}"
                }]
            }
        except subprocess.TimeoutExpired:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"El comando tardó demasiado en ejecutarse: {command}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error ejecutando comando: {str(e)}"
                }]
            }
    
    async def _tool_search_files(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Busca archivos por nombre o patrón"""
        pattern = arguments.get("pattern", "")
        path = arguments.get("path", "")
        search_path = self._resolve_path(path) if path else self.workspace_root
        
        try:
            found_files = []
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if pattern in file or pattern == "*" or pattern == "*.*":
                        found_files.append(os.path.join(root, file))
            
            if not found_files:
                return {
                    "content": [{
                        "type": "text", 
                        "text": f"No se encontraron archivos con el patrón '{pattern}' en {search_path}"
                    }]
                }
            
            files_text = "\n".join(found_files)
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Archivos encontrados con patrón '{pattern}' en {search_path}:\n\n{files_text}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error buscando archivos: {str(e)}"
                }]
            }
    
    async def _tool_file_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene información detallada de un archivo"""
        path = self._resolve_path(arguments.get("path", ""))
        
        try:
            if not os.path.exists(path):
                return {
                    "content": [{
                        "type": "text", 
                        "text": f"La ruta no existe: {path}"
                    }]
                }
            
            stats = os.stat(path)
            file_info = {
                "path": path,
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "is_file": os.path.isfile(path),
                "is_dir": os.path.isdir(path),
                "extension": os.path.splitext(path)[1] if os.path.isfile(path) else ""
            }
            
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Información del archivo:\n{json.dumps(file_info, indent=2)}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error obteniendo información del archivo: {str(e)}"
                }]
            }
    
    async def _tool_calculator(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculadora científica"""
        try:
            result = eval(arguments["expression"], {"__builtins__": None}, math.__dict__)
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Resultado: {result}"
                }]
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text", 
                    "text": f"Error de cálculo: {str(e)}"
                }]
            }
    
    async def _tool_datetime(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene la fecha y hora actual"""
        return {
            "content": [{
                "type": "text", 
                "text": f"Fecha y hora actual: {datetime.now().isoformat()}"
            }]
        }


    




    
    async def handle_prompts_list(self):
        """Lista todos los prompts disponibles"""
        return {"prompts": list(self.capabilities["prompts"].values())}
    
    async def handle_prompts_get(self, params):
        """Obtiene un prompt específico"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if prompt_name == "code_review":
            return {
                "description": "Revisión de código con enfoque en calidad",
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Revisa este código {arguments.get('language', '')}:\n\n{arguments.get('code', '')}\n\nProporciona comentarios sobre calidad, posibles errores y optimizaciones."
                    }
                }]
            }
        
        elif prompt_name == "code_explanation":
            return {
                "description": "Explica el funcionamiento de un código",
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Explica cómo funciona este código {arguments.get('language', '')}:\n\n{arguments.get('code', '')}\n\nDescribe el propósito, las funciones principales y cualquier detalle importante."
                    }
                }]
            }
        
        elif prompt_name == "create_test":
            framework = arguments.get("framework", "estándar")
            return {
                "description": "Genera tests para un código dado",
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Genera tests usando {framework} para este código {arguments.get('language', '')}:\n\n{arguments.get('code', '')}\n\nIncluye casos de prueba para diferentes escenarios."
                    }
                }]
            }
        
        return {
            "description": "Prompt no encontrado",
            "messages": [{
                "role": "user",
                "content": {
                    "type": "text", 
                    "text": f"El prompt '{prompt_name}' no existe."
                }
            }]
        }

async def handle_client(reader, writer):
    """Maneja una conexión de cliente TCP"""
    mcp_server = MCPServer()
    addr = writer.get_extra_info('peername')
    logger.info(f"Conexión recibida de {addr}")

    try:
        while True:
            data = await reader.readline()
            if not data:
                break

            request = data.decode().strip()
            if not request:
                continue

            logger.debug(f"Request recibido: {request}")
            response = await mcp_server.handle_request(request)
            
            if response:
                writer.write(response.encode() + b'\n')
                await writer.drain()
                logger.debug(f"Response enviado: {response}")
            
    except Exception as e:
        logger.error(f"Error con {addr}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        logger.info(f"Conexión cerrada: {addr}")

async def main():
    """Función principal del servidor MCP"""
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    
    async with server:
        logger.info("Servidor MCP para VS Code ejecutándose en 127.0.0.1:8888")
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")