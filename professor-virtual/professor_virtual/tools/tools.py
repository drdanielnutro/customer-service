"""Custom tools for the Professor Virtual agent."""

import re
import uuid
from typing import Dict, Any, Optional
from google.adk.tools import ToolContext


class AnaliseVisualResult:
    def __init__(self, necessita_imagem: bool, confianca: float, referencias_encontradas: list[str]):
        self.necessita_imagem = necessita_imagem
        self.confianca = confianca
        self.referencias_encontradas = referencias_encontradas


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
            pontuacao_visual += len(matches) * 0.15
    if "exercício" in texto_lower or "questão" in texto_lower:
        pontuacao_visual += 0.3
    if any(word in texto_lower for word in ["esse aqui", "esta aqui", "isso aqui"]):
        pontuacao_visual += 0.4
    confianca = min(pontuacao_visual, 1.0)
    resultado = AnaliseVisualResult(confianca >= 0.5, confianca, list(set(referencias_encontradas)))
    return {
        "necessita_imagem": resultado.necessita_imagem,
        "confianca": resultado.confianca,
        "referencias_encontradas": resultado.referencias_encontradas,
        "justificativa": f"Detectadas {len(resultado.referencias_encontradas)} referências visuais",
    }


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


def gerar_audio_tts(texto: str, tool_context: ToolContext, velocidade: float = 1.0, voz: str = "pt-BR-Standard-A") -> Dict[str, Any]:
    """Gera um artefato de áudio TTS a partir de um texto."""
    try:
        if not texto or len(texto.strip()) == 0:
            return {"erro": "Texto vazio fornecido", "sucesso": False}
        audio_bytes = b"audio_data_simulado_tts_" + texto.encode("utf-8")
        nome_artefato = f"resposta_tts_{uuid.uuid4()}.mp3"
        tool_context.session.create_artifact(name=nome_artefato, content=audio_bytes, mime_type="audio/mpeg")
        return {"sucesso": True, "nome_artefato_gerado": nome_artefato, "tamanho_caracteres": len(texto)}
    except Exception as e:
        return {"erro": f"Erro ao gerar áudio TTS: {str(e)}", "sucesso": False}


PROFESSOR_TOOLS = {
    "transcrever_audio": transcrever_audio,
    "analisar_necessidade_visual": analisar_necessidade_visual,
    "analisar_imagem_educacional": analisar_imagem_educacional,
    "gerar_audio_tts": gerar_audio_tts,
}
