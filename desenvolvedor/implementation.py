"""
Implementação das ferramentas customizadas para o Professor Virtual ADK
Todas as ferramentas seguem o padrão FunctionTool do Google ADK e utilizam
o padrão de Artefatos para manipulação de dados binários.
"""

import re
import base64
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import uuid # Usado para gerar nomes de artefatos únicos

# Imports do ADK (conforme documentação)
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents import LlmAgent


@dataclass
class AnaliseVisualResult:
    """Resultado da análise de necessidade visual"""
    necessita_imagem: bool
    confianca: float
    referencias_encontradas: list[str]


@dataclass
class AnaliseImagemResult:
    """Resultado da análise de imagem educacional"""
    tipo_conteudo: str  # exercicio, texto, diagrama, etc
    elementos_detectados: list[str]
    contexto_educacional: str
    qualidade_adequada: bool
    sugestao_acao: Optional[str]


def transcrever_audio(
    nome_artefato_audio: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Transcreve um artefato de áudio para texto usando serviços de speech-to-text.
    
    Esta ferramenta processa o áudio gravado pela criança, que foi previamente
    salvo como um artefato na sessão, e o converte em texto para que o agente
    possa entender a pergunta.
    
    Args:
        nome_artefato_audio: O nome do artefato de áudio a ser processado.
                             Ex: "pergunta_aluno_123.wav"
        tool_context: Contexto da ferramenta ADK, usado para acessar o artefato.
        
    Returns:
        Dict contendo o texto transcrito e metadados com a estrutura:
        - sucesso: bool indicando se a transcrição foi bem-sucedida
        - texto: str com o texto transcrito (se sucesso=True)
        - erro: str com mensagem de erro (se sucesso=False)
        - duracao_segundos: float com duração do áudio
        - formato: str com formato do arquivo (extraído do artefato)
        - tamanho_bytes: int com tamanho do arquivo
        - idioma_detectado: str com idioma detectado (padrão pt-BR)
    """
    try:
        # 1. Acessar o artefato usando o tool_context
        artifact = tool_context.session.get_artifact(nome_artefato_audio)
        if not artifact:
            return {
                "erro": f"Artefato de áudio '{nome_artefato_audio}' não encontrado na sessão.",
                "sucesso": False
            }
        
        audio_bytes = artifact.content
        formato = artifact.name.split('.')[-1] if '.' in artifact.name else "desconhecido"

        # 2. Validações (agora sobre os dados reais do artefato)
        formatos_suportados = ["wav", "mp3", "m4a"]
        if formato not in formatos_suportados:
            return {"erro": f"Formato {formato} não suportado", "sucesso": False}
        
        max_size = 10 * 1024 * 1024  # 10MB
        if len(audio_bytes) > max_size:
            return {"erro": "Arquivo de áudio muito grande (máximo 10MB)", "sucesso": False}
        
        # 3. Lógica de negócio (simulada)
        # NOTA: Em produção, aqui você integraria com um serviço real de STT
        texto_transcrito = "Este é um texto simulado da transcrição do áudio do artefato."
        duracao_segundos = len(audio_bytes) / (16000 * 2)  # Estimativa básica
        
        return {
            "sucesso": True,
            "texto": texto_transcrito,
            "duracao_segundos": duracao_segundos,
            "formato": formato,
            "tamanho_bytes": len(audio_bytes),
            "idioma_detectado": "pt-BR"
        }
        
    except Exception as e:
        return {"erro": f"Erro ao transcrever áudio: {str(e)}", "sucesso": False}


def analisar_necessidade_visual(
    texto: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Detecta se há referências visuais no texto que requerem captura de imagem.
    
    Esta ferramenta analisa o texto transcrito procurando por palavras e padrões
    que indicam que a criança está se referindo a algo visual.
    
    Args:
        texto: Texto transcrito da pergunta da criança.
        tool_context: Contexto da ferramenta ADK.
        
    Returns:
        Dict com análise de necessidade visual.
    """
    # Nenhuma mudança necessária nesta função, pois ela não lida com dados binários.
    padroes_visuais = [
        r'\b(esse|esta|esses|estas|aqui|aí|isso|isto)\b', r'\b(mostr\w+|ve[jr]|olh\w+|observ\w+)\b',
        r'\b(figura|imagem|foto|desenho|gráfico|diagrama|exercício|questão|problema)\b',
        r'\b(tá|está)\s+(escrito|mostrando|aparecendo)', r'o que (é|significa|quer dizer) (isso|isto)',
        r'não (entendi|compreendi) (esse|este|essa|esta)', r'(ajuda|me ajude|help) com (isso|este|esse)',
    ]
    texto_lower = texto.lower()
    referencias_encontradas = []
    pontuacao_visual = 0.0
    for padrao in padroes_visuais:
        matches = re.findall(padrao, texto_lower)
        if matches:
            referencias_encontradas.extend(matches)
            pontuacao_visual += len(matches) * 0.15
    if "exercício" in texto_lower or "questão" in texto_lower: pontuacao_visual += 0.3
    if any(word in texto_lower for word in ["esse aqui", "esta aqui", "isso aqui"]): pontuacao_visual += 0.4
    
    confianca = min(pontuacao_visual, 1.0)
    resultado = AnaliseVisualResult(
        necessita_imagem=confianca >= 0.5,
        confianca=confianca,
        referencias_encontradas=list(set(referencias_encontradas))
    )
    return {
        "necessita_imagem": resultado.necessita_imagem, "confianca": resultado.confianca,
        "referencias_encontradas": resultado.referencias_encontradas,
        "justificativa": f"Detectadas {len(resultado.referencias_encontradas)} referências visuais"
    }


def analisar_imagem_educacional(
    nome_artefato_imagem: str,
    contexto_pergunta: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Extrai informações educacionais relevantes de um artefato de imagem.
    
    Esta ferramenta processa a imagem capturada (foto do exercício, página do livro),
    que foi previamente salva como um artefato, e extrai informações relevantes.
    
    Args:
        nome_artefato_imagem: O nome do artefato de imagem a ser processado.
                              Ex: "exercicio_matematica_001.png"
        contexto_pergunta: Contexto da pergunta original da criança.
        tool_context: Contexto da ferramenta ADK, usado para acessar o artefato.
        
    Returns:
        Dict com análise educacional da imagem.
    """
    try:
        # 1. Acessar o artefato
        artifact = tool_context.session.get_artifact(nome_artefato_imagem)
        if not artifact:
            return {
                "erro": f"Artefato de imagem '{nome_artefato_imagem}' não encontrado.",
                "sucesso": False, "qualidade_adequada": False
            }
        
        imagem_bytes = artifact.content

        # 2. Validações
        max_size = 5 * 1024 * 1024  # 5MB
        if len(imagem_bytes) > max_size:
            return {
                "erro": "Imagem muito grande (máximo 5MB)",
                "sucesso": False, "qualidade_adequada": False
            }
        
        # 3. Lógica de negócio (simulada)
        # NOTA: Em produção, aqui você integraria com um serviço real de visão
        resultado = AnaliseImagemResult(
            tipo_conteudo="exercicio_matematica",
            elementos_detectados=["equação quadrática", "gráfico de parábola"],
            contexto_educacional="Exercício de matemática sobre funções quadráticas",
            qualidade_adequada=True, sugestao_acao=None
        )
        if len(imagem_bytes) < 10000:
            resultado.qualidade_adequada = False
            resultado.sugestao_acao = "Imagem pode estar com baixa resolução"
        
        return {
            "sucesso": True, "tipo_conteudo": resultado.tipo_conteudo,
            "elementos_detectados": resultado.elementos_detectados,
            "contexto_educacional": resultado.contexto_educacional,
            "qualidade_adequada": resultado.qualidade_adequada,
            "sugestao_acao": resultado.sugestao_acao,
            "tamanho_bytes": len(imagem_bytes), "contexto_pergunta": contexto_pergunta
        }
        
    except Exception as e:
        return {
            "erro": f"Erro ao analisar imagem: {str(e)}",
            "sucesso": False, "qualidade_adequada": False
        }


def gerar_audio_tts(
    texto: str,
    tool_context: ToolContext,
    velocidade: float = 1.0,
    voz: str = "pt-BR-Standard-A"
) -> Dict[str, Any]:
    """Gera um artefato de áudio TTS a partir de um texto.
    
    Converte o texto da resposta educacional em áudio e o salva como um novo
    artefato na sessão. O nome do artefato gerado é retornado para que o
    aplicativo cliente possa recuperá-lo e reproduzi-lo.
    
    Args:
        texto: Texto para converter em áudio.
        tool_context: Contexto da ferramenta ADK.
        velocidade: Velocidade da fala (0.5 a 2.0).
        voz: Identificador da voz a usar.
        
    Returns:
        Dict indicando o sucesso e o nome do artefato de áudio criado.
        - sucesso: bool
        - nome_artefato_gerado: str com o nome do artefato (se sucesso=True)
        - erro: str com mensagem de erro (se sucesso=False)
    """
    try:
        if not texto or len(texto.strip()) == 0:
            return {"erro": "Texto vazio fornecido", "sucesso": False}
        
        # NOTA: Em produção, aqui você integraria com um serviço real de TTS
        # e obteria os bytes reais do áudio.
        audio_bytes_simulados = b"audio_data_simulado_tts_" + texto.encode('utf-8')
        
        # 1. Criar um nome único para o novo artefato
        nome_artefato = f"resposta_tts_{uuid.uuid4()}.mp3"
        
        # 2. Criar o artefato na sessão atual
        tool_context.session.create_artifact(
            name=nome_artefato,
            content=audio_bytes_simulados,
            mime_type="audio/mpeg"
        )
        
        # 3. Retornar apenas a referência (o nome do artefato)
        return {
            "sucesso": True,
            "nome_artefato_gerado": nome_artefato,
            "tamanho_caracteres": len(texto)
        }
        
    except Exception as e:
        return {"erro": f"Erro ao gerar áudio TTS: {str(e)}", "sucesso": False}


# Funções auxiliares (a função de validação de metadados foi removida pois
# a validação agora ocorre dentro da própria ferramenta, de forma mais robusta)

def extrair_contexto_educacional(texto: str) -> Dict[str, Any]:
    """Extrai contexto educacional do texto para melhor processamento"""
    materias = {
        "matematica": ["conta", "número", "equação", "calcul", "soma", "multiplicação"],
        "portugues": ["palavra", "frase", "texto", "verbo", "substantivo", "letra"],
        "ciencias": ["animal", "planta", "corpo", "natureza", "experimento"],
        "historia": ["ano", "época", "aconteceu", "passado", "história"],
        "geografia": ["país", "cidade", "mapa", "continente", "oceano"]
    }
    texto_lower = texto.lower()
    materia_detectada = "geral"
    for materia, palavras_chave in materias.items():
        if any(palavra in texto_lower for palavra in palavras_chave):
            materia_detectada = materia
            break
    return {
        "materia_provavel": materia_detectada,
        "nivel_complexidade": "basico",
        "tipo_ajuda": "explicacao"
    }


# Registro das ferramentas para uso com o ADK
PROFESSOR_TOOLS = {
    "transcrever_audio": transcrever_audio,
    "analisar_necessidade_visual": analisar_necessidade_visual,
    "analisar_imagem_educacional": analisar_imagem_educacional,
    "gerar_audio_tts": gerar_audio_tts
}