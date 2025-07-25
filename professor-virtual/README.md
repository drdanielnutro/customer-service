# Professor Virtual - Assistente Educacional

Este projeto implementa um agente educacional baseado no Google Agent Development Kit (ADK). O Professor Virtual é um assistente de IA que auxilia estudantes com explicações, orientações e suporte educacional personalizado.

## Visão Geral

O Professor Virtual é um agente conversacional projetado para fornecer suporte educacional através de:
- Transcrição e análise de perguntas em áudio
- Análise de imagens de exercícios e materiais educacionais
- Geração de respostas em áudio para melhor acessibilidade
- Interações personalizadas baseadas nas necessidades do estudante

O agente utiliza a arquitetura ADK para garantir escalabilidade e integração com os serviços do Google Cloud.

## Ferramentas Disponíveis

O Professor Virtual possui as seguintes ferramentas especializadas:

### 1. Transcrever Áudio (`transcrever_audio`)
- **Função**: Converte perguntas em áudio para texto
- **Entrada**: Arquivo de áudio com a pergunta do estudante
- **Saída**: Transcrição em texto da pergunta

### 2. Analisar Imagem Educacional (`analisar_imagem_educacional`)
- **Função**: Analisa imagens de exercícios, diagramas ou materiais de estudo
- **Entrada**: Imagem contendo conteúdo educacional
- **Saída**: Descrição e análise do conteúdo visual

### 3. Analisar Necessidade Visual (`analisar_necessidade_visual`)
- **Função**: Identifica necessidades visuais específicas do estudante
- **Entrada**: Contexto da interação e preferências do estudante
- **Saída**: Recomendações de adaptação visual

### 4. Gerar Áudio TTS (`gerar_audio_tts`)
- **Função**: Converte respostas textuais em áudio
- **Entrada**: Texto da resposta educacional
- **Saída**: Arquivo de áudio com a resposta narrada

## Instalação

### Pré-requisitos

- Python 3.11+
- Poetry (gerenciador de dependências)
- Google ADK SDK
- Projeto no Google Cloud (para integração com Vertex AI)

### Passos de Instalação

1. **Clone o repositório**:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd professor-virtual
   ```

2. **Instale as dependências com Poetry**:
   ```bash
   poetry install
   ```

3. **Ative o ambiente virtual**:
   ```bash
   poetry shell
   ```

4. **Configure as credenciais do Google Cloud**:
   ```bash
   # Copie o arquivo de exemplo
   cp .env.example .env
   
   # Edite o arquivo .env com suas credenciais
   # GOOGLE_CLOUD_PROJECT=seu-projeto-id
   # GOOGLE_CLOUD_LOCATION=us-central1
   # GOOGLE_API_KEY=sua-api-key (se usar Gemini Developer API)
   ```

5. **Habilite as APIs necessárias**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

## Uso

### Executar o Agente em Modo CLI

```bash
adk run professor_virtual
```

### Executar com Interface Web do ADK

```bash
adk web
```

Depois selecione "professor_virtual" no dropdown da interface.

### Exemplo de Interação

**Estudante**: "Olá professor, pode me ajudar com matemática?"

**Professor Virtual**: "Olá! Claro que posso ajudar você com matemática. Você pode me enviar sua pergunta por áudio ou compartilhar uma imagem do exercício que está com dúvida. Como prefere começar?"

**Estudante**: *[Envia áudio com pergunta sobre equações]*

**Professor Virtual**: *[Transcreve o áudio, processa a pergunta e responde com explicação detalhada, podendo gerar áudio da resposta]*

## Avaliação

### Executar Testes de Avaliação

Os testes de avaliação verificam as capacidades do agente em cenários educacionais:

```bash
pytest eval
```

### Executar Testes Unitários

Para testar componentes individuais:

```bash
pytest tests/unit
```

### Estrutura de Testes

- `eval/`: Testes de avaliação end-to-end
  - `test_eval.py`: Cenários de interação educacional
  - `eval_data/`: Dados de teste e configurações
- `tests/unit/`: Testes unitários
  - `test_tools.py`: Testes das ferramentas educacionais
  - `test_config.py`: Testes de configuração

## Configuração

As configurações do agente estão em `professor_virtual/config.py`:

- **Nome do Agente**: Professor Virtual
- **Modelo LLM**: Configurável (Gemini por padrão)
- **Parâmetros de Resposta**: Tom educacional e paciente
- **Timeouts**: Configuráveis para cada ferramenta

### Variáveis de Ambiente

Configure no arquivo `.env`:

```bash
# Escolha o backend (0 para Developer API, 1 para Vertex AI)
GOOGLE_GENAI_USE_VERTEXAI=0

# Chave da API (necessária se GOOGLE_GENAI_USE_VERTEXAI=0)
GOOGLE_API_KEY=sua_chave_aqui

# Configurações do Vertex AI
GOOGLE_CLOUD_PROJECT=seu-projeto-id
GOOGLE_CLOUD_LOCATION=us-central1
```

## Deployment no Google Agent Engine

### 1. Construir o Pacote Wheel

```bash
poetry build --format=wheel --output=deployment
```

### 2. Deploy para Agent Engine

```bash
cd deployment
python deploy.py
```

### 3. Testar o Deployment

```python
import vertexai
from professor_virtual.config import Config
from vertexai.preview.reasoning_engines import AdkApp

configs = Config()

vertexai.init(
    project="SEU_PROJECT_ID",
    location="us-central1"
)

# Obter o agente pelo ID do recurso
agent_engine = vertexai.agent_engines.get('DEPLOYMENT_RESOURCE_NAME')

# Testar interação
for event in agent_engine.stream_query(
    user_id="test_user",
    session_id="test_session",
    message="Olá Professor!"
):
    print(event)
```

## Estrutura do Projeto

```
professor-virtual/
├── professor_virtual/
│   ├── __init__.py
│   ├── agent.py              # Lógica principal do agente
│   ├── config.py             # Configurações
│   ├── prompts.py            # Prompts educacionais
│   ├── entities/             # Modelos de dados
│   ├── tools/                # Ferramentas educacionais
│   └── shared_libraries/     # Bibliotecas compartilhadas
├── deployment/               # Scripts de deployment
├── eval/                     # Testes de avaliação
├── tests/                    # Testes unitários
├── pyproject.toml           # Configuração do projeto
└── README.md                # Este arquivo
```

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-ferramenta`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova ferramenta educacional'`)
4. Push para a branch (`git push origin feature/nova-ferramenta`)
5. Abra um Pull Request

## Suporte

Para dúvidas ou problemas:
- Abra uma issue no repositório
- Contate: contato@institutorecriare.com

## Licença

Este projeto está licenciado sob a Apache License 2.0 - veja o arquivo LICENSE para detalhes.