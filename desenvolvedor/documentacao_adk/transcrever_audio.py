"""Ferramenta para transcrever áudio para texto."""

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


def transcrever_audio(nome_artefato_audio: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Transcreve um artefato de áudio para texto.
    
    Args:
        nome_artefato_audio: Nome do artefato de áudio a ser transcrito
        tool_context: Contexto da ferramenta ADK
    
    Returns:
        Dict com a transcrição e metadados
    """
    try:
        # Obter artefato
        artifact = tool_context.session.get_artifact(nome_artefato_audio)
        if not artifact:
            return {
                "erro": f"Artefato de áudio '{nome_artefato_audio}' não encontrado na sessão.", 
                "sucesso": False
            }

        audio_bytes = artifact.content
        
        # Validar formato
        formato = artifact.name.split('.')[-1] if '.' in artifact.name else "desconhecido"
        formatos_suportados = ["wav", "mp3", "m4a", "ogg", "flac", "aac"]
        
        if formato not in formatos_suportados:
            return {
                "erro": f"Formato {formato} não suportado. Formatos aceitos: {', '.join(formatos_suportados)}", 
                "sucesso": False
            }
        
        # Validar tamanho
        if len(audio_bytes) > 10 * 1024 * 1024:
            return {
                "erro": "Arquivo de áudio muito grande (máximo 10MB)", 
                "sucesso": False
            }
        
        # Configurar cliente Gemini
        client = _get_genai_client()
        
        # Preparar áudio para análise
        audio_part = types.Part.from_inline_data(
            data=base64.b64encode(audio_bytes).decode('utf-8'),
            mime_type=f"audio/{formato}"
        )
        
        # Prompt para transcrição com metadados
        prompt = """Transcreva o áudio a seguir para português brasileiro.
        
        Forneça a resposta em formato JSON com os seguintes campos:
        - "transcricao": texto completo transcrito
        - "idioma_detectado": idioma principal detectado no áudio
        - "confianca": nível de confiança da transcrição (alta, media, baixa)
        - "observacoes": quaisquer observações sobre qualidade do áudio, ruídos, múltiplos falantes, etc
        
        Se houver múltiplos falantes, indique na transcrição com "Falante 1:", "Falante 2:", etc.
        
        Responda APENAS com o JSON estruturado."""
        
        # Fazer transcrição
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[audio_part, prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,  # Baixa temperatura para transcrição precisa
                max_output_tokens=4000,
                response_mime_type='application/json'
            )
        )
        
        # Processar resposta
        try:
            import json
            resultado_json = json.loads(response.text)
            texto_transcrito = resultado_json.get("transcricao", "")
            idioma = resultado_json.get("idioma_detectado", "pt-BR")
            confianca = resultado_json.get("confianca", "media")
            observacoes = resultado_json.get("observacoes", "")
        except:
            # Fallback se não vier em JSON
            texto_transcrito = response.text
            idioma = "pt-BR"
            confianca = "media"
            observacoes = "Transcrição direta sem metadados estruturados"
        
        # Calcular estatísticas
        palavras = len(texto_transcrito.split())
        caracteres = len(texto_transcrito)
        
        # Estimar duração baseada no tamanho do arquivo e taxa de bits típica
        # Assumindo ~128kbps para MP3
        if formato == "mp3":
            duracao_segundos = (len(audio_bytes) * 8) / (128 * 1000)
        else:
            # Estimativa genérica
            duracao_segundos = len(audio_bytes) / (16000 * 2)  # 16kHz, 16-bit mono
        
        return {
            "sucesso": True,
            "texto": texto_transcrito,
            "duracao_segundos": round(duracao_segundos, 1),
            "formato": formato,
            "tamanho_bytes": len(audio_bytes),
            "idioma_detectado": idioma,
            "estatisticas": {
                "total_palavras": palavras,
                "total_caracteres": caracteres,
                "palavras_por_minuto": round((palavras / duracao_segundos) * 60) if duracao_segundos > 0 else 0
            },
            "qualidade": {
                "confianca": confianca,
                "observacoes": observacoes
            }
        }
        
    except Exception as e:
        return {
            "erro": f"Erro ao transcrever áudio: {str(e)}", 
            "sucesso": False,
            "detalhes_erro": {
                "tipo": type(e).__name__,
                "mensagem": str(e)
            }
        }