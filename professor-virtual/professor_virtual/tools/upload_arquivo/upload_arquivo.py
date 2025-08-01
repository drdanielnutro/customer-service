"""Tool para processar uploads de arquivos do frontend e criar artifacts ADK.

Esta tool substitui a função handle_file_upload do artifact_handler.py,
corrigindo o problema de uso do InvocationContext incorreto.
Agora usa ToolContext que possui os métodos necessários para artifacts.
"""

import base64
from typing import Dict, Any
from google.genai import types
from google.adk.tools import tool
from google.adk.tools.tool_context import ToolContext


@tool(
    name="upload_arquivo",
    description="Processa upload de arquivo do frontend e cria artifact no ADK"
)
async def upload_arquivo(
    file_data: Dict[str, Any],
    context: ToolContext
) -> Dict[str, Any]:
    """
    Processa upload de arquivo do frontend e cria artifact.
    
    Esta tool é a forma correta de lidar com uploads no ADK, pois:
    1. Recebe ToolContext que possui o método save_artifact
    2. É invocada pelo agent quando necessário
    3. Segue o padrão ADK de usar Tools para ações
    
    Args:
        file_data: Dict containing:
            - content: Base64 encoded file content (string)
            - mime_type: MIME type of the file (e.g., "audio/wav", "image/jpeg")
            - filename: Unique filename for the artifact
        context: ADK ToolContext (injetado automaticamente)
        
    Returns:
        Dict containing:
            - success: Boolean indicating if upload was successful
            - filename: The filename used for the artifact (on success)
            - version: The version assigned by ADK as integer (on success)
            - size: Size of the file in bytes (on success)
            - error: Error message (on failure)
            
    Example:
        >>> file_data = {
        ...     "content": "UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB...",
        ...     "mime_type": "audio/wav",
        ...     "filename": "student_question_001.wav"
        ... }
        >>> # O agent invocará esta tool automaticamente
        >>> # result = await upload_arquivo(file_data, context)
        >>> # result será algo como:
        >>> {
        ...     "success": True,
        ...     "filename": "student_question_001.wav",
        ...     "version": 0,  # Integer, não string!
        ...     "size": 46382
        ... }
    """
    try:
        # Validar entrada
        if not all(k in file_data for k in ['content', 'mime_type', 'filename']):
            return {
                "success": False,
                "error": "Missing required fields: content, mime_type, or filename"
            }
        
        # Decodificar base64
        if isinstance(file_data['content'], str):
            content_bytes = base64.b64decode(file_data['content'])
        else:
            content_bytes = file_data['content']
            
        # Criar Part do arquivo
        artifact = types.Part.from_data(
            data=content_bytes,
            mime_type=file_data['mime_type']
        )
        
        # Salvar artifact usando ToolContext (agora funciona!)
        version = await context.save_artifact(
            filename=file_data['filename'],
            artifact=artifact
        )
        
        return {
            "success": True,
            "filename": file_data['filename'],
            "version": version,  # ADK retorna integer
            "size": len(content_bytes)
        }
        
    except ValueError as e:
        # Erro específico quando artifact_service é None
        return {
            "success": False,
            "error": f"Artifact service not configured: {str(e)}"
        }
    except base64.binascii.Error as e:
        # Erro ao decodificar base64
        return {
            "success": False,
            "error": f"Invalid base64 encoding: {str(e)}"
        }
    except Exception as e:
        # Outros erros
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }