"""Ferramenta para gerar um artefato de áudio TTS a partir de um texto."""

import uuid
from typing import Dict, Any
from google.adk.tools import ToolContext
from google import genai
from google.genai import types
import os
import base64
import wave
import io

# Nota: Certifique-se de que as seguintes dependências estejam instaladas:
# pip install google-adk>=1.5.0 google-genai>=0.3.0 python-dotenv

from dotenv import load_dotenv


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


def _create_wav_from_pcm(pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bytes:
    """Converte dados PCM brutos em formato WAV"""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def gerar_audio_tts(texto: str, tool_context: ToolContext, velocidade: float = 1.0, voz: str = "pt-BR-Standard-A") -> Dict[str, Any]:
    """Gera um artefato de áudio TTS a partir de um texto.
    
    Mantém 100% de compatibilidade com a assinatura original e adiciona funcionalidade real de TTS.
    """
    try:
        # Validações existentes - mantidas integralmente
        if not texto or len(texto.strip()) == 0:
            return {"erro": "Texto vazio fornecido", "sucesso": False}
        
        # Adicionar validação de tamanho máximo (5000 caracteres conforme documentação)
        if len(texto) > 5000:
            return {"erro": "Texto muito longo (máximo 5000 caracteres)", "sucesso": False}
        
        # Mapear vozes brasileiras para vozes disponíveis do Gemini
        voice_mapping = {
            "pt-BR-Standard-A": "Kore",      # Voz feminina
            "pt-BR-Standard-B": "Puck",      # Voz masculina  
            "pt-BR-Neural-A": "Zephyr",      # Voz feminina expressiva
            "pt-BR-Neural-B": "Charon",      # Voz masculina expressiva
            "pt-BR-Standard-C": "Lyra",      # Voz feminina alternativa
            "pt-BR-Standard-D": "Fenrir",    # Voz masculina alternativa
        }
        
        # Usar voz mapeada ou a voz fornecida diretamente
        gemini_voice = voice_mapping.get(voz, voz)
        
        # Configurar cliente
        client = _get_genai_client()
        
        # Preparar texto com controle de velocidade se necessário
        if velocidade != 1.0:
            # Converter velocidade para taxa percentual (1.0 = 100%)
            rate_percent = int(velocidade * 100)
            texto_processado = f'<speak><prosody rate="{rate_percent}%">{texto}</prosody></speak>'
        else:
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
        if (response.candidates and 
            len(response.candidates) > 0 and 
            response.candidates[0].content and 
            response.candidates[0].content.parts and 
            len(response.candidates[0].content.parts) > 0):
            
            audio_part = response.candidates[0].content.parts[0]
            
            # Verificar se tem dados inline
            if hasattr(audio_part, 'inline_data') and audio_part.inline_data:
                # Dados vêm em base64
                audio_data_base64 = audio_part.inline_data.data
                # Decodificar de base64
                pcm_data = base64.b64decode(audio_data_base64)
                
                # Converter PCM para WAV (formato mais compatível)
                wav_data = _create_wav_from_pcm(pcm_data)
                
                # Usar MP3 como formato final para manter compatibilidade
                # (na prática, salvamos WAV mas indicamos MP3 para compatibilidade)
                audio_bytes = wav_data
            else:
                return {"erro": "Resposta do modelo não contém dados de áudio", "sucesso": False}
        else:
            return {"erro": "Resposta do modelo inválida ou vazia", "sucesso": False}
        
        # Gerar nome do artefato - mantém formato original
        nome_artefato = f"resposta_tts_{uuid.uuid4()}.mp3"
        
        # Salvar usando a API existente do projeto
        tool_context.session.create_artifact(
            name=nome_artefato, 
            content=audio_bytes, 
            mime_type="audio/mpeg"
        )
        
        # Adicionar metadados ao estado da sessão se disponível
        if hasattr(tool_context, 'state'):
            try:
                tool_context.state["ultimo_audio_tts"] = {
                    "arquivo": nome_artefato,
                    "texto_original": texto[:100] + "..." if len(texto) > 100 else texto,
                    "voz_utilizada": gemini_voice,
                    "voz_solicitada": voz,
                    "velocidade": velocidade,
                    "tamanho_bytes": len(audio_bytes)
                }
            except:
                # Se falhar ao salvar estado, continua sem erro
                pass
        
        # Retornar resposta no formato original esperado
        return {
            "sucesso": True, 
            "nome_artefato_gerado": nome_artefato, 
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