"""Ferramenta para gerar um artefato de áudio TTS a partir de um texto."""

import uuid
from typing import Dict, Any
from google.adk.tools import ToolContext
from google import genai
from google.genai import types
import os
import base64


def _get_genai_client():
    """Obtém cliente genai configurado para ambiente local ou Vertex AI"""
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'True':
        return genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        )
    else:
        return genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))


def gerar_audio_tts(texto: str, tool_context: ToolContext, velocidade: float = 1.0, voz: str = "pt-BR-Standard-A") -> Dict[str, Any]:
    """Gera um artefato de áudio TTS a partir de um texto.
    
    Args:
        texto: Texto para converter em áudio
        tool_context: Contexto da ferramenta ADK
        velocidade: Velocidade da fala (0.5 a 2.0)
        voz: Nome da voz a ser usada (vozes disponíveis: Kore, Puck, Charon, Zephyr, etc)
    
    Returns:
        Dict com status da operação e nome do artefato gerado
    """
    try:
        # Validar entrada
        if not texto or len(texto.strip()) == 0:
            return {"erro": "Texto vazio fornecido", "sucesso": False}
        
        # Limitar tamanho do texto
        if len(texto) > 5000:
            return {"erro": "Texto muito longo (máximo 5000 caracteres)", "sucesso": False}
        
        # Configurar cliente Gemini
        client = _get_genai_client()
        
        # Mapear vozes disponíveis no Gemini TTS
        vozes_disponiveis = {
            "pt-BR-Standard-A": "Kore",  # Voz feminina padrão
            "pt-BR-Standard-B": "Puck",  # Voz masculina padrão
            "pt-BR-Neural-A": "Zephyr",  # Voz neural feminina
            "pt-BR-Neural-B": "Charon",  # Voz neural masculina
        }
        
        # Usar voz mapeada ou a fornecida diretamente
        voz_gemini = vozes_disponiveis.get(voz, voz)
        
        # Configuração específica para TTS
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voz_gemini
                    )
                )
            )
        )
        
        # Adicionar marcações SSML para velocidade se diferente de 1.0
        if velocidade != 1.0:
            texto_ssml = f'<speak><prosody rate="{velocidade}">{texto}</prosody></speak>'
        else:
            texto_ssml = texto
        
        # Gerar áudio
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-tts',
            contents=texto_ssml,
            config=config
        )
        
        # Extrair dados do áudio
        if response.candidates and response.candidates[0].content.parts:
            audio_part = response.candidates[0].content.parts[0]
            if hasattr(audio_part, 'inline_data') and audio_part.inline_data:
                audio_bytes = base64.b64decode(audio_part.inline_data.data)
            else:
                # Fallback para formato diferente de resposta
                audio_bytes = audio_part.data if hasattr(audio_part, 'data') else b''
        else:
            return {"erro": "Resposta do modelo não contém áudio", "sucesso": False}
        
        if not audio_bytes:
            return {"erro": "Falha ao gerar áudio", "sucesso": False}
        
        # Criar nome único para o artefato
        nome_artefato = f"resposta_tts_{uuid.uuid4()}.mp3"
        
        # Salvar como artefato
        tool_context.session.create_artifact(
            name=nome_artefato, 
            content=audio_bytes, 
            mime_type="audio/mpeg"
        )
        
        # Calcular estatísticas
        duracao_estimada = len(texto.split()) * 0.4 / velocidade  # Estimativa básica
        
        return {
            "sucesso": True, 
            "nome_artefato_gerado": nome_artefato, 
            "tamanho_caracteres": len(texto),
            "tamanho_bytes": len(audio_bytes),
            "voz_utilizada": voz_gemini,
            "velocidade": velocidade,
            "duracao_estimada_segundos": round(duracao_estimada, 1)
        }
        
    except Exception as e:
        return {
            "erro": f"Erro ao gerar áudio TTS: {str(e)}", 
            "sucesso": False,
            "detalhes_erro": {
                "tipo": type(e).__name__,
                "mensagem": str(e)
            }
        }