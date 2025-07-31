"""Ferramenta para transcrever áudio para texto usando Google ADK e Gemini."""

from typing import Dict, Any, Optional
from google.adk.tools import ToolContext
from google import genai
from google.genai import types
from pydantic import BaseModel
import os
import json
import hashlib
from datetime import datetime
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Cache simples para transcrições
_transcription_cache = {}
_cache_max_size = 50


# Schema para resposta estruturada do Gemini
class TranscricaoGeminiResponse(BaseModel):
    """Schema para a resposta de transcrição do modelo Gemini.
    
    Define a estrutura esperada da resposta do modelo, garantindo
    consistência independente da versão ou comportamento do modelo.
    """
    transcricao: str
    idioma_detectado: str = "pt-BR"
    confianca: str = "media"
    observacoes: str = ""


def _get_genai_client():
    """Obtém cliente genai configurado para ambiente local ou Vertex AI."""
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'True':
        return genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        )
    else:
        return genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))


def _get_audio_hash(audio_bytes: bytes) -> str:
    """Gera hash único para o áudio (usado no cache)."""
    return hashlib.md5(audio_bytes).hexdigest()


def _limpar_cache_se_necessario():
    """Remove entradas antigas do cache se ultrapassar o limite."""
    global _transcription_cache
    if len(_transcription_cache) > _cache_max_size:
        # Remove 20% das entradas mais antigas
        items = sorted(_transcription_cache.items(), 
                      key=lambda x: x[1].get('timestamp', 0))
        remove_count = int(_cache_max_size * 0.2)
        for key, _ in items[:remove_count]:
            del _transcription_cache[key]


async def transcrever_audio(
    nome_artefato_audio: str, 
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Transcreve um artefato de áudio para texto usando Gemini.
    
    Mantém assinatura 100% compatível com implementação atual.
    
    Args:
        nome_artefato_audio: Nome do artefato de áudio a ser transcrito
        tool_context: Contexto da ferramenta ADK (fornecido automaticamente)
    
    Returns:
        Dict com campos obrigatórios 'sucesso' e 'texto', mais metadados
    """
    try:
        # Carregar artifact usando método correto da documentação
        audio_artifact = await tool_context.load_artifact(nome_artefato_audio)
        
        if not audio_artifact:
            # Tentar buscar na mensagem do usuário como fallback
            audio_artifact = await _buscar_audio_na_mensagem(tool_context)
            if not audio_artifact:
                return {
                    "sucesso": False,
                    "erro": f"Artefato de áudio '{nome_artefato_audio}' não encontrado."
                }
        
        # Extrair dados do artifact
        audio_bytes, mime_type = _extrair_dados_do_artifact(audio_artifact)
        
        if not audio_bytes:
            return {
                "sucesso": False,
                "erro": "Não foi possível extrair dados de áudio do artefato."
            }
        
        # Validar formato
        formato = mime_type.split('/')[-1] if '/' in mime_type else "desconhecido"
        formatos_suportados = ["wav", "mp3", "m4a", "ogg", "flac", "aac", "mpeg", "aiff"]
        
        if formato not in formatos_suportados:
            return {
                "sucesso": False,
                "erro": f"Formato '{formato}' não suportado. Use: {', '.join(formatos_suportados)}"
            }
        
        # Validar tamanho (20MB limite para inline data)
        tamanho_mb = len(audio_bytes) / (1024 * 1024)
        if tamanho_mb > 20:
            return {
                "sucesso": False,
                "erro": f"Arquivo muito grande ({tamanho_mb:.1f}MB). Máximo: 20MB.",
                "sugestao": "Use a Files API para arquivos grandes."
            }
        
        # Verificar cache
        audio_hash = _get_audio_hash(audio_bytes)
        if audio_hash in _transcription_cache:
            cached = _transcription_cache[audio_hash].copy()
            cached["fonte_cache"] = True
            return cached
        
        # Configurar cliente Gemini
        client = _get_genai_client()
        
        # Criar Part do áudio (método correto da documentação)
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type
        )
        
        # Prompt em português para transcrição
        prompt = """Transcreva o áudio a seguir para português brasileiro.

Forneça a resposta APENAS em formato JSON com:
{
  "transcricao": "texto completo transcrito",
  "idioma_detectado": "código do idioma (pt-BR, en-US, etc)",
  "confianca": "alta, media ou baixa",
  "observacoes": "qualquer observação relevante"
}

Se houver múltiplos falantes, indique com "Falante 1:", "Falante 2:", etc."""
        
        # Fazer transcrição usando método correto
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # Modelo compatível com transcrição de áudio.
            contents=[prompt, audio_part],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8000,
                response_mime_type='application/json',
                response_schema=TranscricaoGeminiResponse
            )
        )
        
        # Processar resposta
        try:
            # Usar response.parsed para obter objeto Pydantic validado
            if hasattr(response, 'parsed') and response.parsed:
                gemini_response = response.parsed
                texto_transcrito = gemini_response.transcricao
                idioma_detectado = gemini_response.idioma_detectado
                confianca = gemini_response.confianca
                observacoes = gemini_response.observacoes
            else:
                # Fallback para parsing manual se parsed não estiver disponível
                resultado_json = json.loads(response.text)
                texto_transcrito = resultado_json.get("transcricao", "")
                idioma_detectado = resultado_json.get("idioma_detectado", "pt-BR")
                confianca = resultado_json.get("confianca", "media")
                observacoes = resultado_json.get("observacoes", "")
        except (json.JSONDecodeError, AttributeError) as e:
            # Fallback se resposta não for estruturada
            logger.warning(f"Resposta não estruturada do modelo: {e}")
            texto_transcrito = response.text
            idioma_detectado = "desconhecido"
            confianca = "baixa"
            observacoes = "Resposta não estruturada do modelo"
        
        # Calcular estatísticas
        palavras = len(texto_transcrito.split())
        caracteres = len(texto_transcrito)
        
        # Estimar duração baseada no tamanho e formato
        duracao_segundos = _estimar_duracao(audio_bytes, formato)
        
        # Salvar transcrição como artifact (opcional)
        arquivo_salvo = None
        versao_salva = None
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            transcript_artifact = types.Part.from_text(text=texto_transcrito)
            filename = f"transcricao_{timestamp}.txt"
            versao_salva = await tool_context.save_artifact(filename, transcript_artifact)
            arquivo_salvo = filename
        except Exception as e:
            logger.warning(f"Não foi possível salvar transcrição: {e}")
        
        # Preparar resultado compatível
        resultado = {
            # Campos obrigatórios para compatibilidade
            "sucesso": True,
            "texto": texto_transcrito,
            
            # Metadados compatíveis com implementação anterior
            "duracao_segundos": round(duracao_segundos, 1),
            "formato": formato,
            "tamanho_bytes": len(audio_bytes),
            "idioma_detectado": idioma_detectado,
            
            # Estatísticas adicionais
            "estatisticas": {
                "total_palavras": palavras,
                "total_caracteres": caracteres,
                "palavras_por_minuto": round((palavras / duracao_segundos) * 60) if duracao_segundos > 0 else 0
            },
            
            # Qualidade da transcrição
            "qualidade": {
                "confianca": confianca,
                "observacoes": observacoes
            }
        }
        
        # Adicionar campos opcionais se disponíveis
        if arquivo_salvo and versao_salva:
            resultado["arquivo_salvo"] = arquivo_salvo
            resultado["versao"] = versao_salva
        
        # Adicionar ao cache
        _limpar_cache_se_necessario()
        _transcription_cache[audio_hash] = resultado.copy()
        _transcription_cache[audio_hash]["timestamp"] = datetime.now().timestamp()
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro na transcrição: {str(e)}", exc_info=True)
        
        return {
            "sucesso": False,
            "erro": f"Erro ao transcrever áudio: {str(e)}",
            "detalhes_erro": {
                "tipo": type(e).__name__,
                "mensagem": str(e)
            }
        }


def _extrair_dados_do_artifact(artifact) -> tuple[bytes, str]:
    """Extrai bytes e mime_type de um artifact ADK.
    
    Baseado na documentação oficial do ADK.
    """
    try:
        # Se for um Part com inline_data
        if hasattr(artifact, 'inline_data') and artifact.inline_data:
            inline_data = artifact.inline_data
            if hasattr(inline_data, 'data') and hasattr(inline_data, 'mime_type'):
                return inline_data.data, inline_data.mime_type
        
        # Se for um objeto com atributos diretos
        if hasattr(artifact, 'data') and hasattr(artifact, 'mime_type'):
            return artifact.data, artifact.mime_type
        
        # Se for bytes direto (alguns artifacts retornam apenas os dados)
        if isinstance(artifact, bytes):
            # Tentar detectar formato pelos magic bytes
            if artifact[:4] == b'RIFF':
                return artifact, 'audio/wav'
            elif artifact[:3] == b'ID3' or artifact[:2] == b'\xff\xfb':
                return artifact, 'audio/mpeg'
            else:
                return artifact, 'audio/mpeg'  # Assumir MP3 como padrão
                
    except Exception as e:
        logger.error(f"Erro ao extrair dados do artifact: {e}")
    
    return None, None


async def _buscar_audio_na_mensagem(tool_context: ToolContext) -> Optional[Any]:
    """Busca áudio na mensagem do usuário como fallback.
    
    Baseado na documentação do ADK sobre acesso a user_content.
    """
    try:
        # Acessar conteúdo do usuário via ToolContext
        if hasattr(tool_context, 'user_content'):
            user_content = tool_context.user_content()
            if user_content and hasattr(user_content, 'parts'):
                for part in user_content.parts:
                    if hasattr(part, 'mime_type') and part.mime_type.startswith('audio/'):
                        return part
    except Exception as e:
        logger.debug(f"Não foi possível buscar áudio na mensagem: {e}")
    
    return None


def _estimar_duracao(audio_bytes: bytes, formato: str) -> float:
    """Estima duração do áudio baseada no tamanho e formato."""
    # Estimativas baseadas em bitrates típicos
    estimativas = {
        "mp3": (len(audio_bytes) * 8) / (128 * 1000),      # 128kbps
        "mpeg": (len(audio_bytes) * 8) / (128 * 1000),     # 128kbps
        "wav": len(audio_bytes) / (44100 * 2 * 2),         # 44.1kHz, 16-bit, stereo
        "m4a": (len(audio_bytes) * 8) / (96 * 1000),       # 96kbps
        "aac": (len(audio_bytes) * 8) / (128 * 1000),      # 128kbps
        "ogg": (len(audio_bytes) * 8) / (160 * 1000),      # 160kbps
        "flac": len(audio_bytes) / (44100 * 2 * 2 * 0.6),  # ~60% compressão
        "aiff": len(audio_bytes) / (44100 * 2 * 2),        # 44.1kHz, 16-bit, stereo (similar ao WAV)
    }
    
    return estimativas.get(formato, len(audio_bytes) / (16000 * 2))  # Padrão: 16kHz mono


# Versão avançada com parâmetros opcionais (para futuro)
async def transcrever_audio_avancado(
    nome_artefato_audio: str,
    tool_context: ToolContext,
    incluir_timestamps: bool = False,
    identificar_speakers: bool = False,
    idioma_preferencial: str = "pt-BR"
) -> Dict[str, Any]:
    """Versão avançada com funcionalidades extras.
    
    Mantém compatibilidade total - pode ser usada no lugar da função básica.
    """
    # Por enquanto, redireciona para função básica
    # Funcionalidades avançadas serão implementadas posteriormente
    resultado = await transcrever_audio(nome_artefato_audio, tool_context)
    
    # Adicionar informação sobre configurações usadas
    if resultado.get("sucesso"):
        resultado["configuracoes_avancadas"] = {
            "timestamps_solicitados": incluir_timestamps,
            "identificacao_falantes_solicitada": identificar_speakers,
            "idioma_preferencial": idioma_preferencial,
            "nota": "Funcionalidades avançadas em desenvolvimento"
        }
    
    return resultado
