"""Ferramenta para extrair informações educacionais relevantes de uma imagem."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from google.adk.tools import ToolContext
from google import genai
from google.genai import types
import os
import json
import base64

# Nota: Certifique-se de que as seguintes dependências estejam instaladas:
# pip install google-adk>=1.5.0 google-genai>=0.3.0 python-dotenv

from dotenv import load_dotenv


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
    # Carregar variáveis de ambiente se ainda não carregadas
    load_dotenv()
    
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') in ['1', 'True']:
        return genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        )
    else:
        return genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))


def analisar_imagem_educacional(nome_artefato_imagem: str, contexto_pergunta: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Extrai informações educacionais relevantes de uma imagem.
    
    Mantém 100% de compatibilidade com a assinatura original e adiciona análise real com Gemini Vision.
    """
    try:
        # Obter artefato - mantém lógica original
        artifact = tool_context.session.get_artifact(nome_artefato_imagem)
        if not artifact:
            return {
                "erro": f"Artefato de imagem '{nome_artefato_imagem}' não encontrado.", 
                "sucesso": False, 
                "qualidade_adequada": False
            }
        
        imagem_bytes = artifact.content
        
        # Validação de tamanho - mantém limite original
        if len(imagem_bytes) > 5 * 1024 * 1024:
            return {
                "erro": "Imagem muito grande (máximo 5MB)", 
                "sucesso": False, 
                "qualidade_adequada": False
            }
        
        # Configurar cliente
        client = _get_genai_client()
        
        # Preparar imagem para análise
        # Determinar MIME type do artifact
        mime_type = "image/jpeg"  # padrão
        if hasattr(artifact, 'mime_type') and artifact.mime_type:
            mime_type = artifact.mime_type
        elif nome_artefato_imagem.lower().endswith('.png'):
            mime_type = "image/png"
        elif nome_artefato_imagem.lower().endswith('.gif'):
            mime_type = "image/gif"
        elif nome_artefato_imagem.lower().endswith('.webp'):
            mime_type = "image/webp"
        
        # Criar parte da imagem
        image_part = types.Part.from_bytes(
            data=imagem_bytes,
            mime_type=mime_type
        )
        
        # Prompt estruturado para análise educacional
        prompt = f"""Analise esta imagem do ponto de vista educacional considerando o contexto: {contexto_pergunta}

        IMPORTANTE: Responda APENAS com um JSON válido, sem markdown ou texto adicional.
        
        O JSON deve conter EXATAMENTE estes campos:
        {{
            "tipo_conteudo": "categoria do conteúdo educacional (exercicio_matematica, diagrama_ciencias, mapa_geografia, ilustracao_historia, material_lingua, recurso_artes, etc)",
            "elementos_detectados": ["lista", "de", "elementos", "visuais", "identificados"],
            "contexto_educacional": "descrição detalhada do contexto pedagógico e possíveis aplicações em sala de aula",
            "conceitos_abordados": ["lista", "de", "conceitos", "educacionais", "presentes"],
            "nivel_ensino_sugerido": "nivel mais apropriado (educacao_infantil, fundamental_1, fundamental_2, medio, superior)",
            "qualidade_adequada": true ou false (baseado em legibilidade, resolução e clareza),
            "sugestao_acao": null ou "sugestão específica se a qualidade não for adequada",
            "perguntas_reflexao": ["pergunta 1 para discussão", "pergunta 2", "pergunta 3"],
            "aplicacoes_pedagogicas": ["aplicação 1", "aplicação 2", "aplicação 3"],
            "interdisciplinaridade": ["conexão com disciplina 1", "conexão com disciplina 2"],
            "acessibilidade": {{
                "descricao_alternativa": "descrição detalhada da imagem para deficientes visuais",
                "elementos_textuais": ["texto visível 1", "texto visível 2"],
                "cores_predominantes": ["cor1", "cor2", "cor3"]
            }}
        }}
        
        Analise cuidadosamente TODOS os elementos visuais, textos, diagramas, símbolos e contexto geral."""
        
        # Fazer chamada para o modelo
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                temperature=0.2,  # Baixa temperatura para análise mais precisa
                max_output_tokens=2000,
                response_mime_type='application/json'
            )
        )
        
        # Processar resposta
        try:
            # Limpar resposta se vier com markdown
            json_text = response.text.strip()
            if json_text.startswith('```'):
                # Remove markdown code blocks
                json_text = json_text.split('```')[1]
                if json_text.startswith('json'):
                    json_text = json_text[4:]
                json_text = json_text.strip()
            
            analise = json.loads(json_text)
        except json.JSONDecodeError as je:
            # Fallback para análise básica se JSON falhar
            # Ainda tentamos extrair informações úteis da resposta
            analise = {
                "tipo_conteudo": "conteudo_educacional",
                "elementos_detectados": ["imagem analisada"],
                "contexto_educacional": response.text[:200] if response.text else "Análise realizada",
                "conceitos_abordados": [],
                "nivel_ensino_sugerido": "medio",
                "qualidade_adequada": True,
                "sugestao_acao": None,
                "perguntas_reflexao": [],
                "aplicacoes_pedagogicas": [],
                "interdisciplinaridade": [],
                "acessibilidade": {
                    "descricao_alternativa": "Imagem educacional analisada",
                    "elementos_textuais": [],
                    "cores_predominantes": []
                }
            }
        
        # Verificar qualidade com base no tamanho (lógica original preservada)
        if len(imagem_bytes) < 10000:
            analise["qualidade_adequada"] = False
            analise["sugestao_acao"] = analise.get("sugestao_acao") or "Imagem pode estar com baixa resolução"
        
        # Construir resultado mantendo estrutura original + enriquecimentos
        resultado = {
            # Campos obrigatórios originais
            "tipo_conteudo": analise.get("tipo_conteudo", "conteudo_educacional"),
            "elementos_detectados": analise.get("elementos_detectados", []),
            "contexto_educacional": analise.get("contexto_educacional", ""),
            "qualidade_adequada": analise.get("qualidade_adequada", True),
            "sugestao_acao": analise.get("sugestao_acao"),
            
            # Metadados originais
            "sucesso": True,
            "tamanho_bytes": len(imagem_bytes),
            "contexto_pergunta": contexto_pergunta,
            
            # Enriquecimentos pedagógicos (campos adicionais que não quebram compatibilidade)
            "conceitos_abordados": analise.get("conceitos_abordados", []),
            "nivel_ensino_sugerido": analise.get("nivel_ensino_sugerido", "medio"),
            "perguntas_reflexao": analise.get("perguntas_reflexao", []),
            "aplicacoes_pedagogicas": analise.get("aplicacoes_pedagogicas", []),
            "interdisciplinaridade": analise.get("interdisciplinaridade", []),
            "acessibilidade": analise.get("acessibilidade", {})
        }
        
        # Salvar análise completa no estado da sessão se disponível
        if hasattr(tool_context, 'state'):
            try:
                tool_context.state["ultima_analise_imagem"] = {
                    "arquivo": nome_artefato_imagem,
                    "timestamp": os.environ.get('REQUEST_TIME', ''),
                    "analise_completa": resultado
                }
            except:
                # Se falhar ao salvar estado, continua sem erro
                pass
        
        return resultado
        
    except Exception as e:
        # Mantém estrutura de erro original
        import traceback
        error_result = {
            "erro": f"Erro ao analisar imagem: {str(e)}", 
            "sucesso": False, 
            "qualidade_adequada": False
        }
        
        # Em desenvolvimento, adicionar mais detalhes
        if os.getenv('DEBUG') == 'True':
            error_result["tipo_erro"] = type(e).__name__
            error_result["traceback"] = traceback.format_exc()
        
        return error_result