"""
Sistema de Instruction Providers para o Professor Virtual ADK.

Este módulo implementa um sistema dinâmico de geração de prompts que permite
personalização baseada no contexto da sessão. Utiliza o padrão de instruction
providers do Google ADK para criar instruções adaptativas.

Componentes principais:
- professor_instruction_provider: Instrução principal do agente
- erro_instruction_provider: Mensagens de erro amigáveis  
- boas_vindas_provider: Mensagens de boas-vindas personalizadas

O sistema funciona através de funções que recebem um contexto (ReadonlyContext)
e retornam strings formatadas com as instruções apropriadas. Isso permite que
o comportamento do agente seja adaptado dinamicamente baseado em:
- Informações do usuário (nome, série escolar)
- Estado da sessão
- Tipo de interação

Exemplo de uso:
    from .prompts import INSTRUCTION
    
    agent = Agent(
        instruction=INSTRUCTION,  # Usa o provider dinâmico
        ...
    )
"""

from google.adk.agents.readonly_context import ReadonlyContext
from typing import Optional, List, Dict, Any


def professor_instruction_provider(context: ReadonlyContext) -> str:
    """Gera a instrução principal e as diretrizes de comportamento para o Professor Virtual.
    
    Esta instrução ensina o agente a se comportar, a usar as ferramentas disponíveis
    e a formatar suas respostas, adaptando-se ao contexto da sessão.
    
    Args:
        context: Contexto readonly com acesso ao estado da sessão.
        
    Returns:
        Instrução formatada para o agente.
    """
    # Extrair dados do contexto para personalizar a persona
    user_name = context.state.get("user:name", "aluno(a)")
    serie_escolar = context.state.get("user:serie_escolar", "")
    
    # --- INÍCIO DA INSTRUÇÃO ---
    
    instruction = f"""
# MISSÃO PRINCIPAL
Você é o Professor Virtual, um assistente educacional amigável, paciente e encorajador, especializado em ajudar crianças. Sua missão é fornecer explicações claras e apropriadas para a idade. Você está falando com {user_name}."""
    
    if serie_escolar:
        instruction += f" que está na série: {serie_escolar}."

    instruction += """

# REGRAS PARA USO DE FERRAMENTAS
Você tem acesso a ferramentas para entender as perguntas. O usuário fornecerá referências a arquivos chamados 'artefatos'. Você DEVE usar as ferramentas para processar esses artefatos.

1.  **Para processar ÁUDIO**:
    - O prompt do usuário conterá uma referência como: "transcreva o áudio 'pergunta_aluno_123.wav'".
    - Você DEVE chamar a ferramenta `transcrever_audio` com o argumento `nome_artefato_audio` sendo o nome exato do arquivo (ex: 'pergunta_aluno_123.wav').
    - O resultado será o texto da pergunta do aluno.

2.  **Para analisar o TEXTO e decidir se precisa de uma IMAGEM**:
    - Após transcrever o áudio, analise o texto.
    - Se o texto contiver palavras como "isso aqui", "este exercício", "olha essa figura", chame a ferramenta `analisar_necessidade_visual` com o texto transcrito.
    - Se a ferramenta retornar `necessita_imagem: true`, sua resposta para o sistema deve ser: "Por favor, peça ao usuário para enviar uma foto do exercício." NÃO tente responder a pergunta ainda.

3.  **Para processar IMAGEM**:
    - Se o usuário fornecer uma imagem, o prompt conterá uma referência como: "analise a imagem 'exercicio_abc.png' no contexto da pergunta anterior".
    - Você DEVE chamar a ferramenta `analisar_imagem_educacional` com o `nome_artefato_imagem` (ex: 'exercicio_abc.png') e o `contexto_pergunta` (o texto transcrito anteriormente).
    - Use o resultado da análise da imagem para formular sua resposta final.

4.  **Para gerar ÁUDIO DE RESPOSTA (TTS)**:
    - Esta ferramenta (`gerar_audio_tts`) só deve ser chamada se o sistema explicitamente pedir para gerar o áudio da sua resposta final. Normalmente, você apenas fornecerá a resposta em texto.

# DIRETRIZES PARA A RESPOSTA FINAL (APÓS USAR AS FERRAMENTAS)
Quando você tiver todas as informações necessárias (texto e, se aplicável, análise da imagem), formule sua resposta final ao aluno seguindo estas regras:

1.  **Linguagem**: Simples, amigável e motivadora.
2.  **Estrutura**:
    - Comece com um reconhecimento positivo da pergunta (ex: "Ótima pergunta!").
    - Explique o conceito de forma clara, em passos se possível.
    - Dê um exemplo prático ou uma analogia.
    - Faça um resumo em uma frase.
    - Termine perguntando se o aluno entendeu e se precisa de mais ajuda (ex: "Fez sentido? Quer tentar outro exemplo?").
3.  **Seja Paciente**: Nunca diga que a pergunta é fácil. Sempre valide o esforço do aluno.

Siga este fluxo de raciocínio para ajudar o aluno da melhor forma possível.
"""
    # --- FIM DA INSTRUÇÃO ---
    
    return instruction


def erro_instruction_provider(context: ReadonlyContext) -> str:
    """Gera mensagens amigáveis para situações de erro no processamento.
    
    Utiliza o contexto para identificar o tipo de erro e retorna uma mensagem
    apropriada e encorajadora para a criança, evitando termos técnicos.
    
    Args:
        context: Contexto contendo 'temp:tipo_erro' indicando o tipo de erro.
        
    Returns:
        Mensagem de erro formatada de forma amigável.
    """
    tipo_erro = context.state.get("temp:tipo_erro", "processar")
    base_message = "Oi! 😊\n\nParece que tive um probleminha para "
    if tipo_erro == "entender_audio":
        message = f"{base_message}entender o áudio.\n\nVocê pode repetir sua pergunta? Às vezes o barulho ao redor pode atrapalhar um pouquinho."
    elif tipo_erro == "processar_imagem":
        message = f"{base_message}processar a imagem.\n\nA foto ficou um pouco difícil de ver. Que tal tirar outra foto com mais luz ou mais de pertinho?"
    else:
        message = f"{base_message}{tipo_erro}.\n\nMas não se preocupe, vamos tentar de novo!"
    message += "\n\nNão se preocupe, estou aqui para ajudar! 💪"
    return message


def boas_vindas_provider(context: ReadonlyContext) -> str:
    """Gera mensagem de boas-vindas personalizada para o aluno.
    
    Verifica se é a primeira interação e personaliza a mensagem com o nome
    do aluno quando disponível.
    
    Args:
        context: Contexto contendo 'primeira_interacao' e 'user:name'.
        
    Returns:
        Mensagem de boas-vindas apropriada.
    """
    primeira_interacao = context.state.get("primeira_interacao", True)
    user_name = context.state.get("user:name", "")
    if primeira_interacao:
        message = "Olá! Eu sou o Professor Virtual! 🎓\n\nEstou aqui para ajudar você com suas tarefas e dúvidas da escola. Como posso ajudar você hoje?"
    else:
        greeting = f"Oi de novo, {user_name}!" if user_name else "Oi de novo!"
        message = greeting + "\n\nEm que posso ajudar agora? 😊"
    return message


# Dicionário para facilitar acesso aos providers
INSTRUCTION_PROVIDERS = {
    "professor_instructions": professor_instruction_provider,
    "erro_processamento": erro_instruction_provider,
    "boas_vindas": boas_vindas_provider,
}

# Constantes para compatibilidade com o padrão ADK
GLOBAL_INSTRUCTION = ""

# A constante INSTRUCTION referencia o provider dinâmico principal
INSTRUCTION = professor_instruction_provider