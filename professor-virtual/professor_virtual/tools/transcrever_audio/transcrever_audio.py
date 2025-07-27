"""Ferramenta para transcrever áudio para texto."""

from typing import Dict, Any
from google.adk.tools import ToolContext


def transcrever_audio(nome_artefato_audio: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Transcreve um artefato de áudio para texto."""
    try:
        artifact = tool_context.session.get_artifact(nome_artefato_audio)
        if not artifact:
            return {"erro": f"Artefato de áudio '{nome_artefato_audio}' não encontrado na sessão.", "sucesso": False}

        audio_bytes = artifact.content
        formato = artifact.name.split('.')[-1] if '.' in artifact.name else "desconhecido"
        formatos_suportados = ["wav", "mp3", "m4a"]
        if formato not in formatos_suportados:
            return {"erro": f"Formato {formato} não suportado", "sucesso": False}
        if len(audio_bytes) > 10 * 1024 * 1024:
            return {"erro": "Arquivo de áudio muito grande (máximo 10MB)", "sucesso": False}

        texto_transcrito = "Este é um texto simulado da transcrição do áudio do artefato."
        duracao_segundos = len(audio_bytes) / (16000 * 2)
        return {
            "sucesso": True,
            "texto": texto_transcrito,
            "duracao_segundos": duracao_segundos,
            "formato": formato,
            "tamanho_bytes": len(audio_bytes),
            "idioma_detectado": "pt-BR",
        }
    except Exception as e:
        return {"erro": f"Erro ao transcrever áudio: {str(e)}", "sucesso": False}