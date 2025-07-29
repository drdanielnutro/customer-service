
# Análise da Base de Código do Professor Virtual

Este relatório descreve a estrutura e a funcionalidade do projeto "Professor Virtual", com foco na interconexão de seus componentes e na sua relação com o arquivo central **agent.py**.

## Visão Geral do Projeto

```mermaid
graph TB
  professorVirtual["Professor Virtual<br>AI Agent<br>professor_virtual/agent.py"]
  googleAdkAgent["google.adk.Agent<br>Framework<br>N/A"]
  googleGemini["Google Gemini Models<br>AI Services<br>2.0 Flash / 2.5 Flash"]
  userInteraction["User Interaction<br>Process<br>N/A"]
  educationalFunctionality["Educational Functionality<br>Purpose<br>N/A"]
  specializedTools["Specialized Tools<br>Components<br>professor_virtual/tools/"]
  callbacks["Callbacks<br>Components<br>professor_virtual/shared_libraries/callbacks/"]
  artifacts["ADK Artifacts<br>Data Storage<br>Audio/Image/Text"]
  
  professorVirtual --> |"built with"| googleAdkAgent
  professorVirtual --> |"interacts with"| userInteraction
  professorVirtual --> |"provides"| educationalFunctionality
  professorVirtual --> |"uses"| specializedTools
  professorVirtual --> |"manages behavior via"| callbacks
  specializedTools --> |"powered by"| googleGemini
  specializedTools --> |"stores/retrieves"| artifacts
  googleGemini --> |"processes"| artifacts
```


O projeto **Professor Virtual** é um agente de IA construído com o framework `google.adk.Agent`. Seu propósito principal é interagir com usuários e fornecer funcionalidades educacionais. Ele opera utilizando um conjunto de ferramentas especializadas para executar ações e callbacks para gerenciar seu comportamento e fluxo de interação. As ferramentas foram recentemente atualizadas de implementações mock para versões reais integradas com os modelos Google Gemini, proporcionando capacidades avançadas de processamento de áudio, imagem e síntese de voz.

## Componentes Principais

```mermaid
graph TB
  agentPy["agent.py<br>Main Agent File<br>professor_virtual/agent.py"]
  configPy["config.py<br>Configuration<br>professor_virtual/config.py"]
  rootInitPy["__init__.py<br>Package Marker<br>professor_virtual/__init__.py"]
  promptsDir["prompts/<br>Prompts Module<br>professor_virtual/prompts/"]
  entitiesDir["entities/<br>Entities Module<br>professor_virtual/entities/"]
  sharedLibrariesDir["shared_libraries/<br>Callbacks Module<br>professor_virtual/shared_libraries/"]
  toolsDir["tools/<br>Tools Module<br>professor_virtual/tools/"]
  promptsPromptsPy["prompts.py<br>Instructions<br>professor_virtual/prompts/prompts.py"]
  callbacksPy["callbacks.py<br>Callback Aggregator<br>professor_virtual/shared_libraries/callbacks.py"]
  afterToolCb["after_tool_callback.py<br>Callback<br>professor_virtual/shared_libraries/callbacks/after_tool/after_tool_callback.py"]
  beforeAgentCb["before_agent_callback.py<br>Callback<br>professor_virtual/shared_libraries/callbacks/before_agent/before_agent_callback.py"]
  beforeToolCb["before_tool_callback.py<br>Callback<br>professor_virtual/shared_libraries/callbacks/before_tool/before_tool_callback.py"]
  rateLimitCb["rate_limit_callback.py<br>Callback<br>professor_virtual/shared_libraries/callbacks/rate_limit_callback/rate_limit_callback.py"]
  analisarImagemTool["analisar_imagem_educacional.py<br>Tool<br>professor_virtual/tools/analisar_imagem_educacional/analisar_imagem_educacional.py"]
  analisarNecessidadeTool["analisar_necessidade_visual.py<br>Tool<br>professor_virtual/tools/analisar_necessidade_visual/analisar_necessidade_visual.py"]
  gerarAudioTool["gerar_audio_tts.py<br>Tool<br>professor_virtual/tools/gerar_audio_tts/gerar_audio_tts.py"]
  transcreverAudioTool["transcrever_audio.py<br>Tool<br>professor_virtual/tools/transcrever_audio/transcrever_audio.py"]

  agentPy --> |"imports Config from"| configPy
  agentPy --> |"imports INSTRUCTION from"| promptsPromptsPy
  agentPy --> |"imports callbacks from"| callbacksPy
  agentPy --> |"imports tools from"| toolsDir

  subgraph Configuration and Initialization
    configPy
    rootInitPy
  end

  subgraph Prompts
    promptsDir
    promptsPromptsPy
  end

  subgraph Entities
    entitiesDir
  end

  subgraph Shared Libraries (Callbacks)
    sharedLibrariesDir
    callbacksPy --> |"aggregates"| afterToolCb
    callbacksPy --> |"aggregates"| beforeAgentCb
    callbacksPy --> |"aggregates"| beforeToolCb
    callbacksPy --> |"aggregates"| rateLimitCb
  end

  subgraph Tools
    toolsDir
    toolsDir --> |"contains"| analisarImagemTool
    toolsDir --> |"contains"| analisarNecessidadeTool
    toolsDir --> |"contains"| gerarAudioTool
    toolsDir --> |"contains"| transcreverAudioTool
  end
```


### Agente Principal

*   **agent.py**: Este é o arquivo central do projeto, responsável por instanciar e configurar o agente de IA. Ele integra as configurações, prompts, ferramentas e callbacks para definir o comportamento do **Professor Virtual**.

### Configuração e Inicialização

Este módulo gerencia as configurações essenciais para o funcionamento do agente.

*   **config.py**: Define e carrega as configurações do agente, como o modelo de IA a ser utilizado e outras configurações de conteúdo. O **agent.py** importa e utiliza a classe `Config` deste arquivo para inicializar suas configurações.
*   **__init__.py** (no diretório raiz): Marca o diretório `professor_virtual` como um pacote Python, permitindo que seus módulos (incluindo **agent.py**) sejam importados.

### Integração com Google Gemini

O projeto foi recentemente atualizado para usar implementações reais das ferramentas através da integração com os modelos Google Gemini, substituindo as versões mock anteriores.

#### Modelos Utilizados

*   **Gemini 2.0 Flash**: Usado para transcrição de áudio com suporte a múltiplos idiomas
*   **Gemini 2.5 Flash**: Usado para análise de imagens educacionais com capacidades de visão computacional
*   **Gemini 2.5 Flash Preview TTS**: Usado para síntese de voz (Text-to-Speech) com vozes naturais

#### Configuração de Ambiente

As ferramentas suportam dois modos de operação:

1. **Google Developer API** (padrão):
   - Requer `GOOGLE_API_KEY` configurada
   - `GOOGLE_GENAI_USE_VERTEXAI=0` ou não definida

2. **Vertex AI**:
   - Requer `GOOGLE_CLOUD_PROJECT` e `GOOGLE_CLOUD_LOCATION`
   - `GOOGLE_GENAI_USE_VERTEXAI=1` ou `True`

#### Funcionalidades Avançadas

*   **Sistema de Cache**: Transcrições de áudio são cacheadas para otimizar requisições repetidas
*   **Artifacts ADK**: Todas as ferramentas integram com o sistema de artifacts do ADK para salvar e recuperar dados
*   **Tratamento de Erros**: Implementação robusta com fallbacks e mensagens de erro detalhadas
*   **Metadados Ricos**: As ferramentas retornam informações adicionais como estatísticas, qualidade e sugestões

### Prompts

Este módulo contém as instruções textuais que guiam o comportamento do agente de IA.

*   **prompts/__init__.py**: Marca o diretório `prompts` como um pacote Python. Ele pode reexportar variáveis de outros módulos dentro do pacote `prompts`.
*   **prompts/prompts.py**: Armazena as instruções (prompts) que definem o comportamento do agente. O **agent.py** importa a variável `INSTRUCTION` deste módulo para configurar o `Agent`.
*   **prompts/README.md**: Fornece documentação e informações adicionais sobre o diretório `prompts`. Não é utilizado diretamente pelo código.

### Entidades

Este módulo define as estruturas de dados para as entidades do sistema.

*   **entities/__init__.py**: Marca o diretório `entities` como um pacote Python.
*   **entities/student.py**: Define a estrutura de dados ou classe para representar uma entidade de estudante. Atualmente, não é diretamente chamado por **agent.py**, mas pode ser utilizado por callbacks ou ferramentas que interagem com dados de estudantes.

### Bibliotecas Compartilhadas (Callbacks)

Este módulo contém funções de callback que são executadas em pontos específicos do ciclo de vida do agente, permitindo a interceptação e modificação do comportamento padrão.

*   **shared_libraries/__init__.py**: Marca o diretório `shared_libraries` como um pacote Python.
*   **shared_libraries/callbacks.py**: Atua como um ponto de agregação para as funções de callback. O **agent.py** importa funções como `rate_limit_callback`, `before_agent`, `before_tool` e `after_tool` deste módulo para configurar o `Agent`.
*   **shared_libraries/callbacks/__init__.py**: Marca o diretório `callbacks` como um pacote Python.
*   **shared_libraries/callbacks/after_tool/__init__.py**: Marca o diretório `after_tool` como um pacote Python.
*   **shared_libraries/callbacks/after_tool/after_tool_callback.py**: Implementa a função de callback executada **após** a execução de uma ferramenta. É configurada no **agent.py** e chamada pelo framework `google.adk`.
*   **shared_libraries/callbacks/before_agent/__init__.py**: Marca o diretório `before_agent` como um pacote Python.
*   **shared_libraries/callbacks/before_agent/before_agent_callback.py**: Implementa a função de callback executada **antes** do agente iniciar seu processo de raciocínio. É configurada no **agent.py** e chamada pelo framework `google.adk`.
*   **shared_libraries/callbacks/before_tool/__init__.py**: Marca o diretório `before_tool` como um pacote Python.
*   **shared_libraries/callbacks/before_tool/before_tool_callback.py**: Implementa a função de callback executada **antes** da execução de uma ferramenta. É configurada no **agent.py** e chamada pelo framework `google.adk`.
*   **shared_libraries/callbacks/lowercase_value/__init__.py**: Marca o diretório `lowercase_value` como um pacote Python.
*   **shared_libraries/callbacks/lowercase_value/lowercase_value.py**: Provavelmente contém uma função utilitária para converter valores para minúsculas. Não é diretamente chamado por **agent.py**.
*   **shared_libraries/callbacks/rate_limit_callback/__init__.py**: Marca o diretório `rate_limit_callback` como um pacote Python.
*   **shared_libraries/callbacks/rate_limit_callback/rate_limit_callback.py**: Implementa a função de callback para aplicar limites de taxa às chamadas do modelo. É configurada no **agent.py** como `before_model_callback` e chamada pelo framework `google.adk` antes de cada chamada ao modelo de IA.
*   **shared_libraries/callbacks/validate_student_id/__init__.py**: Marca o diretório `validate_student_id` como um pacote Python.
*   **shared_libraries/callbacks/validate_student_id/validate_student_id_callback.py**: Provavelmente contém uma função para validar IDs de estudantes. Não é diretamente chamado por **agent.py**.

### Ferramentas (Tools)

Este módulo contém as ferramentas especializadas que o agente pode utilizar para realizar tarefas específicas. Todas as ferramentas foram atualizadas para implementações reais usando Google Gemini, substituindo as versões mock anteriores.

*   **tools/__init__.py**: Marca o diretório `tools` como um pacote Python e reexporta as ferramentas individuais. O **agent.py** importa as ferramentas deste módulo e as passa como uma lista para o parâmetro `tools` do `Agent` durante a inicialização.

#### Ferramentas de Processamento de Áudio

*   **tools/transcrever_audio/__init__.py**: Marca o diretório `transcrever_audio` como um pacote Python.
*   **tools/transcrever_audio/transcrever_audio.py**: Implementa transcrição de áudio real usando **Gemini 2.0 Flash**. Características principais:
    - Transcrição em português brasileiro com detecção automática de idioma
    - Suporte para múltiplos falantes com identificação
    - Cache inteligente de transcrições para otimização
    - Formatos suportados: WAV, MP3, M4A, OGG, FLAC, AAC
    - Limite de 20MB por arquivo
    - Calcula estatísticas (palavras por minuto, duração estimada)
    - Salva transcrições como artifacts ADK

*   **tools/gerar_audio_tts/__init__.py**: Marca o diretório `gerar_audio_tts` como um pacote Python.
*   **tools/gerar_audio_tts/gerar_audio_tts.py**: Implementa síntese de voz real usando **Gemini 2.5 Flash Preview TTS**. Características principais:
    - Conversão de texto para áudio com vozes naturais
    - Suporte a múltiplas vozes brasileiras mapeadas (Kore, Puck, Zephyr, Charon, Lyra, Fenrir)
    - Controle de velocidade de fala (0.5x a 2.0x)
    - Converte PCM bruto para formato WAV
    - Limite de 5000 caracteres por requisição
    - Salva áudios como artifacts ADK com MIME type audio/mpeg

#### Ferramentas de Análise Visual

*   **tools/analisar_imagem_educacional/__init__.py**: Marca o diretório `analisar_imagem_educacional` como um pacote Python.
*   **tools/analisar_imagem_educacional/analisar_imagem_educacional.py**: Implementa análise de imagens educacionais usando **Gemini 2.5 Flash Vision**. Características principais:
    - Análise pedagógica profunda de conteúdo visual
    - Identifica tipo de conteúdo (exercícios, diagramas, mapas, ilustrações)
    - Detecta conceitos educacionais e nível de ensino apropriado
    - Gera perguntas para reflexão e aplicações pedagógicas
    - Analisa interdisciplinaridade e conexões com outras matérias
    - Fornece descrição alternativa para acessibilidade
    - Suporte para JPEG, PNG, GIF, WebP até 5MB
    - Retorna análise estruturada em JSON

*   **tools/analisar_necessidade_visual/__init__.py**: Marca o diretório `analisar_necessidade_visual` como um pacote Python.
*   **tools/analisar_necessidade_visual/analisar_necessidade_visual.py**: Implementa detecção de referências visuais no texto usando análise por regex. Características principais:
    - Identifica quando o usuário está se referindo a imagens ou elementos visuais
    - Detecta padrões como "esse aqui", "esta figura", "olhe isso"
    - Calcula score de confiança baseado em palavras-chave
    - Não usa IA, implementação baseada em padrões
    - Útil para decidir quando solicitar imagens ao usuário

### Outros Arquivos

*   **README.md**: Fornece uma visão geral do projeto, instruções de configuração e uso. Não é chamado por nenhum código Python.
*   **__pycache__/** e arquivos `.pyc`: Diretórios e arquivos gerados automaticamente pelo Python para armazenar versões compiladas em bytecode dos módulos. Contribuem para o desempenho do carregamento dos módulos que **agent.py** importa.

## Dependências Externas

O projeto agora possui dependências adicionais para suportar as implementações reais das ferramentas:

### Dependências Python

*   **google-genai**: SDK oficial do Google para integração com modelos Gemini (versão 0.3.0+)
*   **google-adk**: Framework ADK para desenvolvimento de agentes (versão 1.5.0+)
*   **python-dotenv**: Carregamento de variáveis de ambiente do arquivo .env
*   **wave**: Biblioteca padrão Python para manipulação de arquivos WAV
*   **base64, json, io**: Bibliotecas padrão para processamento de dados

### APIs e Serviços

*   **Google Gemini API**: Requer chave de API ou configuração Vertex AI
*   **Modelos Gemini**: Acesso aos modelos 2.0 Flash, 2.5 Flash e 2.5 Flash Preview TTS
*   **Limites de API**: 
    - Transcrição: 20MB por arquivo de áudio
    - TTS: 5000 caracteres por requisição
    - Análise de imagem: 5MB por imagem

### Configuração Mínima

1. Instalar dependências: `poetry install`
2. Configurar credenciais em `.env`:
   - Para Developer API: `GOOGLE_API_KEY=sua_chave`
   - Para Vertex AI: `GOOGLE_CLOUD_PROJECT` e autenticação gcloud

---
*Generated by [CodeViz.ai](https://codeviz.ai) on 27/07/2025, 13:34:48*
*Updated on 28/07/2025 to reflect real tool implementations with Google Gemini*
