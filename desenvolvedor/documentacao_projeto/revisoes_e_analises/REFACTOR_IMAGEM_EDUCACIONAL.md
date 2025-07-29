# Guia de Refatoração: Ferramenta `analisar_imagem_educacional`

Este documento detalha todas as **modificações recomendadas** para a ferramenta
`analisar_imagem_educacional` (em `tools/analisar_imagem_educacional/analisar_imagem_educacional.py`),
além das alterações correlatas em `config.py`, `prompts.py` e outros pontos do projeto.
Ele deve servir de guia completo para qualquer desenvolvedor ou assistente de IA que venha a implementá-las.

---

## 1. Contexto

O projeto **Professor Virtual** usa Google ADK e Google GenAI para processar artefatos
de áudio, texto e imagem no fluxo de interação com o aluno. A ferramenta
`analisar_imagem_educacional` faz a ponte entre artefatos de imagem e o Gemini Vision,
mas contém atualmente **desalinhamentos** com a configuração central e duplicações de lógica.

Este guia contempla seis frentes de refatoração:

1. Ajuste da checagem da variável de ambiente `GOOGLE_GENAI_USE_VERTEXAI`.
2. Remoção de `load_dotenv()` redundante.
3. Unificação da criação do cliente GenAI com a configuração central em `Config`.
4. Extração do template de prompt para `prompts.py`.
5. Reuso de `generate_content_config` de `Config` para chamadas de modelo.
6. Aprimoramento da lógica de detecção de MIME type.

---

## 2. Problemas Identificados

- **Flag booleana incompatível**: confere `'True'` em vez de aceitar padrão "1".
- **.env carregado duplicado**: chama `load_dotenv()` internamente, embora já seja gerenciado por `Config`.
- **Cliente GenAI manual**: duplica lógica que poderia vir de `Config` central.
- **Prompt embutido**: bloco multilinha inserido diretamente no código, tornando-o difícil de versar.
- **Parâmetros de geração hardcoded**: temperatura e tokens da imagem não usam `generate_content_config`.
- **MIME type simplista**: ramifica apenas JPEG/PNG/GIF/WebP sem usar heurística padrão.

---

## 3. Instruções de Refatoração

### 3.1 Ajuste da checagem `GOOGLE_GENAI_USE_VERTEXAI`

**Arquivo:**
`tools/analisar_imagem_educacional/analisar_imagem_educacional.py`

**Antes:**
```python
if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'True':
    # Vertex AI
else:
    # API Key
```

**Depois:**
```python
if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') in ('1', 'True'):
    # Vertex AI
else:
    # API Key
```

Isso garante que tanto "1" quanto "True" acionem o caminho Vertex AI.

### 3.2 Remover `load_dotenv()` redundante

**Arquivo:** mesmo trecho de `_get_genai_client()` acima.

**O que remover:**
```python
# Carregar variáveis de ambiente se ainda não carregadas
load_dotenv()
```

> **Importante:** remova somente depois de integrar a leitura de `.env` via `Config`
> (seção 3.3), para não quebrar execuções isoladas.

### 3.3 Unificar cliente GenAI com `Config`

**Arquivo:**
`tools/analisar_imagem_educacional/analisar_imagem_educacional.py`

**Implementação sugerida:**
```python
from .config import Config

def _get_genai_client():
    # Usa configuração centralizada via Pydantic
    cfg = Config()
    if cfg.GENAI_USE_VERTEXAI in ('1', 'True'):
        return genai.Client(
            vertexai=True,
            project=cfg.CLOUD_PROJECT,
            location=cfg.CLOUD_LOCATION
        )
    return genai.Client(api_key=cfg.API_KEY)
```

**Cuidados:** importe `Config` sem criar dependência circular.

### 3.4 Extrair prompt para `prompts.py`

**Local original:** bloco multilinha de `prompt = f"""Analise esta imagem..."""` (~L60–94).

**Passos:**
1. Copiar o texto do prompt para uma função em `prompts/prompts.py`, p.ex.:
   ```python
   def prompt_analisar_imagem(contexto: str) -> str:
       return f"""
       Analise esta imagem do ponto de vista educacional considerando o contexto: {contexto}
       IMPORTANTE: responda somente JSON válido...
       """
   ```
2. Na ferramenta, substituir por:
   ```python
   from .prompts import prompt_analisar_imagem

   prompt = prompt_analisar_imagem(contexto_pergunta)
   ```

### 3.5 Reuso de `generate_content_config` do `Config`

**Contexto em `agent.py`:**
```python
root_agent = Agent(
    …
    generate_content_config=configs.generate_content_config,
)
```

**Na ferramenta, substituir parâmetros fixos por:**
```python
cfg = Config()
response = client.models.generate_content(
    model=cfg.agent_settings.model,
    config=types.GenerateContentConfig(**cfg.generate_content_image_config),
    contents=[image_part, prompt]
)
```

> **Nota:** adicionar `generate_content_image_config` em `config.py` para sustentar
> temperature, max_output_tokens e response_mime_type específicos para imagens.

### 3.6 Aprimoramento de detecção de MIME type

**Antes (ramificações manuais):**
```python
mime_type = 'image/jpeg'
if nome_artefato_imagem.endswith('.png'):
    mime_type = 'image/png'
# etc.
```

**Sugestão (opcional):**
```python
import mimetypes

mime_type, _ = mimetypes.guess_type(nome_artefato_imagem)
if not mime_type:
    mime_type = 'application/octet-stream'
```

---

## 4. Cuidados e Validação Final

1. Executar `pre-commit run --files ...` nos arquivos alterados.
2. Testar cenários Vertex AI e API Key no ADK para garantir seleção correta.
3. Verificar logs de startup para evitar múltiplos carregamentos de `.env`.
4. Validar lint (flake8/pylint) nos trechos modificados.

---

*Este documento é um guia de implementação e não altera diretamente o código.*
