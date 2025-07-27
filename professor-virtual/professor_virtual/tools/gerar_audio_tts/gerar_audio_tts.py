"""Ferramenta para gerar um artefato de áudio TTS a partir de um texto."""

import uuid
from typing import Dict, Any
from google.adk.tools import ToolContext


def gerar_audio_tts(texto: str, tool_context: ToolContext, velocidade: float = 1.0, voz: str = "pt-BR-Standard-A") -> Dict[str, Any]:
    """Gera um artefato de áudio TTS a partir de um texto."""
    try:
        if not texto or len(texto.strip()) == 0:
            return {"erro": "Texto vazio fornecido", "sucesso": False}
        audio_bytes = b"audio_data_simulado_tts_" + texto.encode("utf-8")
        nome_artefato = f"resposta_tts_{uuid.uuid4()}.mp3"
        tool_context.session.create_artifact(name=nome_artefato, content=audio_bytes, mime_type="audio/mpeg")
        return {"sucesso": True, "nome_artefato_gerado": nome_artefato, "tamanho_caracteres": len(texto)}
    except Exception as e:
        return {"erro": f"Erro ao gerar áudio TTS: {str(e)}", "sucesso": False}
