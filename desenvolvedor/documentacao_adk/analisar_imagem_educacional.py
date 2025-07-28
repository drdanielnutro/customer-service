"""Ferramenta para extrair informações educacionais relevantes de uma imagem."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from google.adk.tools import ToolContext
from google import genai
from google.genai import types
import json
import time
import base64
import os


@dataclass
class AnaliseImagemResult:
    """Resultado da análise de imagem educacional"""

    tipo_conteudo: str
    elementos_detectados: list[str]
    contexto_educacional: str
    qualidade_adequada: bool
    sugestao_acao: Optional[str]


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


def analisar_imagem_educacional(nome_artefato_imagem: str, contexto_pergunta: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Extrai informações educacionais relevantes de uma imagem."""
    try:
        # Obter artefato da imagem
        artifact = tool_context.session.get_artifact(nome_artefato_imagem)
        if not artifact:
            return {
                "erro": f"Artefato de imagem '{nome_artefato_imagem}' não encontrado.", 
                "sucesso": False, 
                "qualidade_adequada": False
            }
        
        imagem_bytes = artifact.content
        
        # Validar tamanho
        if len(imagem_bytes) > 5 * 1024 * 1024:
            return {
                "erro": "Imagem muito grande (máximo 5MB)", 
                "sucesso": False, 
                "qualidade_adequada": False
            }
        
        # Configurar cliente Gemini
        client = _get_genai_client()
        
        # Preparar imagem para análise
        image_part = types.Part.from_inline_data(
            data=base64.b64encode(imagem_bytes).decode('utf-8'),
            mime_type=artifact.mime_type or "image/jpeg"
        )
        
        # Prompt estruturado para análise educacional
        prompt = f"""Analise esta imagem do ponto de vista educacional considerando o contexto: {contexto_pergunta}
        
        Forneça uma análise estruturada em JSON com os seguintes campos:
        - "tipo_conteudo": categoria do conteúdo (exercicio_matematica, diagrama_ciencias, mapa_geografia, etc)
        - "elementos_detectados": lista de elementos principais identificados na imagem
        - "contexto_educacional": descrição do contexto pedagógico e aplicação
        - "conceitos_abordados": lista de conceitos educacionais presentes
        - "nivel_ensino_sugerido": nível mais apropriado (fundamental, medio, superior)
        - "qualidade_adequada": boolean indicando se a imagem tem qualidade para uso educacional
        - "sugestao_acao": sugestão de melhoria se a qualidade não for adequada
        - "perguntas_reflexao": lista de 3 perguntas para estimular reflexão sobre o conteúdo
        
        Responda APENAS com o JSON estruturado, sem texto adicional."""
        
        # Fazer chamada para o modelo
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2000,
                response_mime_type='application/json'
            )
        )
        
        # Processar resposta
        try:
            analise = json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback para resposta não estruturada
            analise = {
                "tipo_conteudo": "conteudo_educacional",
                "elementos_detectados": ["imagem analisada"],
                "contexto_educacional": response.text[:200],
                "qualidade_adequada": True,
                "sugestao_acao": None
            }
        
        # Adicionar metadados
        resultado = {
            "sucesso": True,
            "tamanho_bytes": len(imagem_bytes),
            "contexto_pergunta": contexto_pergunta,
            "tipo_conteudo": analise.get("tipo_conteudo", "desconhecido"),
            "elementos_detectados": analise.get("elementos_detectados", []),
            "contexto_educacional": analise.get("contexto_educacional", ""),
            "qualidade_adequada": analise.get("qualidade_adequada", True),
            "sugestao_acao": analise.get("sugestao_acao"),
            "conceitos_abordados": analise.get("conceitos_abordados", []),
            "nivel_ensino_sugerido": analise.get("nivel_ensino_sugerido", "medio"),
            "perguntas_reflexao": analise.get("perguntas_reflexao", [])
        }
        
        return resultado
        
    except Exception as e:
        return {
            "erro": f"Erro ao analisar imagem: {str(e)}", 
            "sucesso": False, 
            "qualidade_adequada": False
        }