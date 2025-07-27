"""Ferramenta para detectar se há referências visuais no texto."""

import re
from typing import Dict, Any
from dataclasses import dataclass
from google.adk.tools import ToolContext


@dataclass
class AnaliseVisualResult:
    """Resultado da análise de necessidade visual"""

    necessita_imagem: bool
    confianca: float
    referencias_encontradas: list[str]


def analisar_necessidade_visual(texto: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Detecta se há referências visuais no texto."""
    padroes_visuais = [
        r"\b(esse|esta|esses|estas|aqui|aí|isso|isto)\b",
        r"\b(mostr\w+|ve[jr]|olh\w+|observ\w+)\b",
        r"\b(figura|imagem|foto|desenho|gráfico|diagrama|exercício|questão|problema)\b",
        r"\b(tá|está)\s+(escrito|mostrando|aparecendo)",
        r"o que (é|significa|quer dizer) (isso|isto)",
        r"não (entendi|compreendi) (esse|este|essa|esta)",
        r"(ajuda|me ajude|help) com (isso|este|esse)",
    ]
    texto_lower = texto.lower()
    referencias_encontradas: list[str] = []
    pontuacao_visual = 0.0
    for padrao in padroes_visuais:
        matches = re.findall(padrao, texto_lower)
        if matches:
            referencias_encontradas.extend(matches)
            # Adjusted weight to ensure common phrases pass the detection
            # threshold more reliably.
            pontuacao_visual += len(matches) * 0.15
    if "exercício" in texto_lower or "questão" in texto_lower:
        pontuacao_visual += 0.3
    if any(
        word in texto_lower
        for word in ["esse aqui", "esta aqui", "isso aqui", "essa figura aqui"]
    ):
        pontuacao_visual += 0.4
    confianca = min(pontuacao_visual, 1.0)
    resultado = AnaliseVisualResult(confianca >= 0.5, confianca, list(set(referencias_encontradas)))
    return {
        "necessita_imagem": resultado.necessita_imagem,
        "confianca": resultado.confianca,
        "referencias_encontradas": resultado.referencias_encontradas,
        "justificativa": f"Detectadas {len(resultado.referencias_encontradas)} referências visuais",
    }