"""Ferramenta para gerar um artefato de áudio TTS a partir de um texto."""

import uuid
from typing import Dict, Any
from google.adk.tools import ToolContext
from google import genai
from google.genai import types
import os
import wave
import io
import logging

# Nota: Certifique-se de que as seguintes dependências estejam instaladas:
# pip install google-adk>=1.5.0 google-genai>=0.3.0 python-dotenv

from dotenv import load_dotenv

# Configurar logger
logger = logging.getLogger(__name__)


def _get_genai_client():
    """Obtém cliente genai configurado para ambiente local ou Vertex AI"""
    # Carregar variáveis de ambiente se ainda não carregadas
    load_dotenv()
    
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'True':
        return genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        )
    else:
        return genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))


def _create_wav_from_pcm(pcm_data: bytes, mime_type: str = "audio/pcm") -> bytes:
    """Converte dados PCM brutos em formato WAV
    
    Args:
        pcm_data: Dados PCM brutos
        mime_type: MIME type dos dados (para futuras otimizações)
    """
    # Parâmetros padrão do ADK: 24kHz, 16-bit, mono
    channels = 1
    rate = 24000
    sample_width = 2
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


async def gerar_audio_tts(texto: str, tool_context: ToolContext, velocidade: float = 1.0, voz: str = "pt-BR-Standard-A") -> Dict[str, Any]:
    """Gera um artefato de áudio TTS a partir de um texto usando a API Gemini.
    
    Args:
        texto: O texto a ser convertido em áudio
        tool_context: Contexto da ferramenta ADK
        voz: Nome da voz Gemini a ser usada (padrão: "pt-BR-Standard-A")
        velocidade: Fator de velocidade da fala
             Vozes disponíveis: Zephyr, Puck, Charon, Kore, Fenrir, Leda, Orus, Aoede,
             Callirrhoe, Autonoe, Enceladus, Iapetus, Umbriel, Algieba, Despina,
             Erinome, Algenib, Rasalgethi, Laomedeia, Achernar, Alnilam, Schedar,
             Gacrux, Pulcherrima, Achird, Zubenelgenubi, Vindemiatrix, Sadachbia,
             Sadaltager, Sulafat
    
    Returns:
        Dict com informações sobre o áudio gerado ou erro
    """
    try:
        # Validações existentes - mantidas integralmente
        if not texto or len(texto.strip()) == 0:
            return {"erro": "Texto vazio fornecido", "sucesso": False}
        
        # Nota: A API tem limite de contexto de 32k tokens, não caracteres
        # Removendo validação arbitrária de caracteres
        
        # Validar se a voz fornecida é uma voz Gemini válida
        vozes_validas = {
            "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede",
            "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba",
            "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
            "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi",
            "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"
        }
        
        if voz not in vozes_validas:
            return {
                "erro": f"Voz '{voz}' não é válida. Use uma das vozes Gemini oficiais.",
                "vozes_validas": sorted(list(vozes_validas)),
                "sucesso": False
            }

        gemini_voice = voz

        # Configurar cliente
        client = _get_genai_client()
        
        # Usar texto diretamente (SSML não é documentado para TTS API)
        texto_processado = texto
        
        # Configuração para TTS
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=gemini_voice
                    )
                )
            )
        )
        
        # Gerar áudio
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=texto_processado,
            config=config
        )
        
        # Extrair dados do áudio
        mime_type = 'audio/pcm'  # Valor padrão
        
        if (response.candidates and 
            len(response.candidates) > 0 and 
            response.candidates[0].content and 
            response.candidates[0].content.parts and 
            len(response.candidates[0].content.parts) > 0):
            
            audio_part = response.candidates[0].content.parts[0]
            
            # Verificar se tem dados inline
            if hasattr(audio_part, 'inline_data') and audio_part.inline_data:
                # Dados já vêm como bytes PCM diretos
                pcm_data = audio_part.inline_data.data
                
                # Verificar e capturar mime_type se disponível
                mime_type = getattr(audio_part.inline_data, 'mime_type', 'audio/pcm')
                
                # Log para debug
                logger.debug(f"Áudio recebido - MIME: {mime_type}, Tamanho: {len(pcm_data)} bytes")
                
                # Converter PCM para WAV (formato mais compatível)
                wav_data = _create_wav_from_pcm(pcm_data, mime_type)
                
                # Usar formato WAV conforme gerado
                audio_bytes = wav_data
            else:
                return {"erro": "Resposta do modelo não contém dados de áudio", "sucesso": False}
        else:
            return {"erro": "Resposta do modelo inválida ou vazia", "sucesso": False}
        
        # Gerar nome do artefato com extensão correta
        nome_artefato = f"resposta_tts_{uuid.uuid4()}.wav"
        
        # Criar Part do artifact usando API ADK
        audio_part = types.Part.from_data(
            data=audio_bytes,
            mime_type="audio/mpeg"
        )

        # Salvar usando método ADK
        try:
            version = await tool_context.save_artifact(nome_artefato, audio_part)
        except ValueError as e:
            return {
                "erro": f"Erro ao salvar artifact: {e}. Artifact service não configurado?",
                "sucesso": False
            }
        
        # Adicionar metadados ao estado da sessão se disponível
        if hasattr(tool_context, 'state'):
            try:
                tool_context.state["ultimo_audio_tts"] = {
                    "arquivo": nome_artefato,
                    "texto_original": texto[:100] + "..." if len(texto) > 100 else texto,
                    "voz_utilizada": gemini_voice,
                    "tamanho_bytes": len(audio_bytes)
                }
            except:
                # Se falhar ao salvar estado, continua sem erro
                pass
        
        # Retornar resposta no formato original esperado
        return {
            "sucesso": True,
            "nome_artefato_gerado": nome_artefato,
            "versao": version,  # Adicionar versão retornada
            "tamanho_caracteres": len(texto),
            "tamanho_bytes": len(audio_bytes),
            "voz_utilizada": gemini_voice,
            "velocidade": velocidade
        }
        
    except Exception as e:
        # Log detalhado para debug em desenvolvimento
        import traceback
        error_details = {
            "erro": f"Erro ao gerar áudio TTS: {str(e)}", 
            "sucesso": False,
            "tipo_erro": type(e).__name__
        }
        
        # Em desenvolvimento, adicionar stacktrace
        if os.getenv('DEBUG') == 'True':
            error_details["traceback"] = traceback.format_exc()
        
        return error_details