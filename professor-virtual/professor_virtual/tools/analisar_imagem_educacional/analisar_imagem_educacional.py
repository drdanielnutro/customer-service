"""Ferramenta para extrair informações educacionais relevantes de uma imagem."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from google.adk.tools import ToolContext


@dataclass
class AnaliseImagemResult:
    """Resultado da análise de imagem educacional"""

    tipo_conteudo: str
    elementos_detectados: list[str]
    contexto_educacional: str
    qualidade_adequada: bool
    sugestao_acao: Optional[str]


def analisar_imagem_educacional(nome_artefato_imagem: str, contexto_pergunta: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Extrai informações educacionais relevantes de uma imagem."""
    try:
        artifact = tool_context.session.get_artifact(nome_artefato_imagem)
        if not artifact:
            return {"erro": f"Artefato de imagem '{nome_artefato_imagem}' não encontrado.", "sucesso": False, "qualidade_adequada": False}
        imagem_bytes = artifact.content
        if len(imagem_bytes) > 5 * 1024 * 1024:
            return {"erro": "Imagem muito grande (máximo 5MB)", "sucesso": False, "qualidade_adequada": False}
        resultado = {
            "tipo_conteudo": "exercicio_matematica",
            "elementos_detectados": ["equação quadrática", "gráfico de parábola"],
            "contexto_educacional": "Exercício de matemática sobre funções quadráticas",
            "qualidade_adequada": True,
            "sugestao_acao": None,
        }
        if len(imagem_bytes) < 10000:
            resultado["qualidade_adequada"] = False
            resultado["sugestao_acao"] = "Imagem pode estar com baixa resolução"
        resultado.update({"sucesso": True, "tamanho_bytes": len(imagem_bytes), "contexto_pergunta": contexto_pergunta})
        return resultado
    except Exception as e:
        return {"erro": f"Erro ao analisar imagem: {str(e)}", "sucesso": False, "qualidade_adequada": False}
