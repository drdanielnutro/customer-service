"""Handler para processar uploads e criar artifacts do frontend."""

import base64
from typing import Any, Dict

from google.genai import types
from google.adk.agents.invocation_context import InvocationContext


async def handle_file_upload(
    file_data: Dict[str, Any],
    context: InvocationContext,
) -> Dict[str, Any]:
    """Processa upload de arquivo do frontend e cria artifact."""
    try:
        # Decodificar base64 se necessário
        if isinstance(file_data["content"], str):
            content_bytes = base64.b64decode(file_data["content"])
        else:
            content_bytes = file_data["content"]

        # Criar Part do arquivo
        artifact = types.Part.from_data(
            data=content_bytes,
            mime_type=file_data["mime_type"],
        )

        # Salvar artifact
        version = await context.save_artifact(
            filename=file_data["filename"],
            artifact=artifact,
        )

        return {
            "success": True,
            "filename": file_data["filename"],
            "version": version,
            "size": len(content_bytes),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
