# Relatório de Correções - Sistema de Artifacts do Professor Virtual

## Resumo dos Problemas Encontrados

Com base na pesquisa sobre o Google ADK, foram identificados os seguintes problemas críticos:

1. **APIs inexistentes/deprecated** sendo usadas (`session.get_artifact`, `session.create_artifact`)
2. **Falta de configuração do artifact_service** no Runner
3. **Métodos síncronos** onde deveriam ser assíncronos
4. **Falta de configuração do GCS** para produção

---

## 1. Arquivo: `professor_virtual/config.py`

### PROBLEMA: Falta configuração do artifact_service e GCS

**❌ REMOVER/ADICIONAR após a linha 38:**
```python
    API_KEY: str | None = Field(default="")
```

**✅ ADICIONAR:**
```python
    API_KEY: str | None = Field(default="")
    
    # Configurações do Artifact Service
    artifact_storage_type: str = Field(default="memory", description="memory ou gcs")
    gcs_bucket_name: str = Field(default="adk-professor-virtual-artifacts")
    
    # Configuração de ambiente
    is_production: bool = Field(default=False)
```

---

## 2. Arquivo: `professor_virtual/agent.py`

### PROBLEMA: Falta inicialização do artifact_service no Runner

**❌ CÓDIGO ATUAL (linhas 24-40):**
```python
root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction="",
    instruction=INSTRUCTION,
    name=configs.agent_settings.name,
    tools=[
        transcrever_audio,
        analisar_necessidade_visual,
        analisar_imagem_educacional,
        gerar_audio_tts,
    ],
    generate_content_config=configs.generate_content_config,
    before_tool_callback=before_tool,
    after_tool_callback=after_tool,
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)
```

**✅ SUBSTITUIR POR:**
```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService

# Configurar artifact service baseado no ambiente
if configs.is_production and configs.artifact_storage_type == "gcs":
    artifact_service = GcsArtifactService(bucket_name=configs.gcs_bucket_name)
else:
    artifact_service = InMemoryArtifactService()

# Configurar session service
session_service = InMemorySessionService()

# Criar o agente
root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction="",
    instruction=INSTRUCTION,
    name=configs.agent_settings.name,
    tools=[
        transcrever_audio,
        analisar_necessidade_visual,
        analisar_imagem_educacional,
        gerar_audio_tts,
    ],
    generate_content_config=configs.generate_content_config,
    before_tool_callback=before_tool,
    after_tool_callback=after_tool,
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)

# Criar o Runner com artifact service
runner = Runner(
    agent=root_agent,
    app_name=configs.app_name,
    session_service=session_service,
    artifact_service=artifact_service  # CRÍTICO: Deve ser configurado
)
```

---

## 3. Arquivo: `professor_virtual/tools/analisar_imagem_educacional/analisar_imagem_educacional.py`

### PROBLEMA 1: API inexistente `session.get_artifact`

**❌ REMOVER (linhas 48-51):**
```python
        # Obter artefato - mantém lógica original
        artifact = tool_context.session.get_artifact(nome_artefato_imagem)
        if not artifact:
```

**✅ SUBSTITUIR POR:**
```python
        # Obter artefato usando API correta
        artifact = await tool_context.load_artifact(nome_artefato_imagem)
        if not artifact:
```

### PROBLEMA 2: Função deve ser assíncrona

**❌ REMOVER (linha 42):**
```python
def analisar_imagem_educacional(nome_artefato_imagem: str, contexto_pergunta: str, tool_context: ToolContext) -> Dict[str, Any]:
```

**✅ SUBSTITUIR POR:**
```python
async def analisar_imagem_educacional(nome_artefato_imagem: str, contexto_pergunta: str, tool_context: ToolContext) -> Dict[str, Any]:
```

### PROBLEMA 3: Acesso incorreto aos dados do artifact

**❌ REMOVER (linha 57):**
```python
        imagem_bytes = artifact.content
```

**✅ SUBSTITUIR POR:**
```python
        # Extrair dados do artifact corretamente
        if hasattr(artifact, 'inline_data') and artifact.inline_data:
            imagem_bytes = artifact.inline_data.data
            mime_type = artifact.inline_data.mime_type
        else:
            return {
                "erro": "Formato de artifact inválido",
                "sucesso": False,
                "qualidade_adequada": False
            }
```

---

## 4. Arquivo: `professor_virtual/tools/gerar_audio_tts/gerar_audio_tts.py`

### PROBLEMA 1: API inexistente `session.create_artifact`

**❌ REMOVER (linhas 119-124):**
```python
        # Salvar usando a API existente do projeto
        tool_context.session.create_artifact(
            name=nome_artefato,
            content=audio_bytes,
            mime_type="audio/mpeg"
        )
```

**✅ SUBSTITUIR POR:**
```python
        # Salvar usando a API correta do ADK
        audio_part = types.Part.from_data(
            data=audio_bytes,
            mime_type="audio/mpeg"
        )
        version = await tool_context.save_artifact(nome_artefato, audio_part)
```

### PROBLEMA 2: Função deve ser assíncrona

**❌ REMOVER (linha 41):**
```python
def gerar_audio_tts(texto: str, tool_context: ToolContext, velocidade: float = 1.0, voz: str = "pt-BR-Standard-A") -> Dict[str, Any]:
```

**✅ SUBSTITUIR POR:**
```python
async def gerar_audio_tts(texto: str, tool_context: ToolContext, velocidade: float = 1.0, voz: str = "pt-BR-Standard-A") -> Dict[str, Any]:
```

### PROBLEMA 3: Adicionar versão no retorno

**❌ REMOVER (linhas 142-148):**
```python
        return {
            "sucesso": True,
            "nome_artefato_gerado": nome_artefato,
            "tamanho_caracteres": len(texto),
            "tamanho_bytes": len(audio_bytes),
            "voz_utilizada": gemini_voice,
            "velocidade": velocidade
        }
```

**✅ SUBSTITUIR POR:**
```python
        return {
            "sucesso": True,
            "nome_artefato_gerado": nome_artefato,
            "versao": version,  # Adicionar versão retornada
            "tamanho_caracteres": len(texto),
            "tamanho_bytes": len(audio_bytes),
            "voz_utilizada": gemini_voice,
            "velocidade": velocidade
        }
```

---

## 5. Arquivo: `professor_virtual/tools/transcrever_audio/transcrever_audio.py`

### PROBLEMA 1: Método deve ser assíncrono

**❌ REMOVER (linha 46):**
```python
def transcrever_audio(
```

**✅ SUBSTITUIR POR:**
```python
async def transcrever_audio(
```

### PROBLEMA 2: load_artifact deve usar await

**❌ REMOVER (linha 61):**
```python
        audio_artifact = tool_context.load_artifact(nome_artefato_audio)
```

**✅ SUBSTITUIR POR:**
```python
        audio_artifact = await tool_context.load_artifact(nome_artefato_audio)
```

### PROBLEMA 3: save_artifact deve usar await

**❌ REMOVER (linha 151):**
```python
            versao_salva = tool_context.save_artifact(filename, transcript_artifact)
```

**✅ SUBSTITUIR POR:**
```python
            versao_salva = await tool_context.save_artifact(filename, transcript_artifact)
```

### PROBLEMA 4: Função auxiliar _buscar_audio_na_mensagem

**❌ REMOVER (linha 227):**
```python
def _buscar_audio_na_mensagem(tool_context: ToolContext) -> Optional[Any]:
```

**✅ SUBSTITUIR POR:**
```python
async def _buscar_audio_na_mensagem(tool_context: ToolContext) -> Optional[Any]:
```

**❌ REMOVER (linha 65):**
```python
            audio_artifact = _buscar_audio_na_mensagem(tool_context)
```

**✅ SUBSTITUIR POR:**
```python
            audio_artifact = await _buscar_audio_na_mensagem(tool_context)
```

---

## 6. Novo Arquivo Necessário: `professor_virtual/artifact_handler.py`

### Criar este arquivo para gerenciar uploads do frontend:

```python
"""Handler para processar uploads e criar artifacts do frontend."""

import base64
from typing import Dict, Any
from google.genai import types
from google.adk.agents.invocation_context import InvocationContext


async def handle_file_upload(
    file_data: Dict[str, Any],
    context: InvocationContext
) -> Dict[str, Any]:
    """
    Processa upload de arquivo do frontend e cria artifact.
    
    Args:
        file_data: Dict com 'content' (base64), 'mime_type' e 'filename'
        context: Contexto da invocação ADK
        
    Returns:
        Dict com informações do artifact criado
    """
    try:
        # Decodificar base64 se necessário
        if isinstance(file_data['content'], str):
            content_bytes = base64.b64decode(file_data['content'])
        else:
            content_bytes = file_data['content']
            
        # Criar Part do arquivo
        artifact = types.Part.from_data(
            data=content_bytes,
            mime_type=file_data['mime_type']
        )
        
        # Salvar artifact
        version = await context.save_artifact(
            filename=file_data['filename'],
            artifact=artifact
        )
        
        return {
            "success": True,
            "filename": file_data['filename'],
            "version": version,
            "size": len(content_bytes)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

## 7. Modificações no Frontend (Orientações)

### Frontend deve enviar dados no formato:

```json
{
  "action": "upload_file",
  "file_data": {
    "content": "base64_encoded_content",
    "mime_type": "audio/wav",
    "filename": "pergunta_aluno_123.wav"
  },
  "session_id": "session_abc",
  "user_id": "user_123"
}
```

### Frontend NÃO deve:
- Esperar que o Runner crie artifacts automaticamente
- Enviar arquivos binários diretamente no corpo da requisição
- Usar APIs do ADK diretamente (não há SDK Flutter oficial)

### Frontend DEVE:
- Converter arquivos para base64 antes de enviar
- Incluir sempre o MIME type correto
- Aguardar confirmação com filename e version do backend

---

## Resumo das Mudanças Críticas

1. **Todas as funções de tools devem ser `async`**
2. **Usar `await` com `load_artifact()` e `save_artifact()`**
3. **Nunca usar `session.get_artifact()` ou `session.create_artifact()`**
4. **Configurar `artifact_service` no Runner**
5. **Frontend envia base64, backend cria artifacts explicitamente**
6. **Acessar dados via `artifact.inline_data.data`**

## Ordem de Implementação Recomendada

1. Atualizar `config.py` com novas configurações
2. Modificar `agent.py` para incluir Runner e artifact_service
3. Tornar todas as funções de tools assíncronas
4. Substituir APIs deprecated nos tools
5. Criar `artifact_handler.py` para gerenciar uploads
6. Testar com `InMemoryArtifactService` primeiro
7. Migrar para `GcsArtifactService` em produção


## 8. Comutação Dev ↔ Produção por variáveis de ambiente

Para não esquecer nenhuma configuração e permitir alternar **InMemoryArtifactService** (desenvolvimento local) e **GcsArtifactService** (produção / Vertex AI) de modo automático, inclua:

### 8.1 Variáveis adicionadas ao `.env`

```dotenv
# já existentes
GOOGLE_GENAI_USE_VERTEXAI=0        # 0 = Gemini API local, 1 = Vertex AI

# novas
ARTIFACT_STORAGE_TYPE=             # vazio → será derivado de GOOGLE_GENAI_USE_VERTEXAI
GCS_BUCKET_NAME=adk-professor-virtual-artifacts
GOOGLE_CLOUD_PROJECT=seu-projeto-id
GOOGLE_CLOUD_LOCATION=us-central1
```

*Se `ARTIFACT_STORAGE_TYPE` ficar vazio, o código escolherá `memory` quando `GOOGLE_GENAI_USE_VERTEXAI=0` e `gcs` quando for `1`.*

---

### 8.2 Ajuste em `config.py` — derivação automática

```python
class Settings(BaseSettings):
    GOOGLE_GENAI_USE_VERTEXAI: int = Field(0, env="GOOGLE_GENAI_USE_VERTEXAI")

    ARTIFACT_STORAGE_TYPE: str | None = Field(default=None, env="ARTIFACT_STORAGE_TYPE")
    GCS_BUCKET_NAME: str = Field(default="adk-professor-virtual-artifacts", env="GCS_BUCKET_NAME")
    GOOGLE_CLOUD_PROJECT: str | None = Field(default=None, env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION: str | None = Field(default=None, env="GOOGLE_CLOUD_LOCATION")

    @property
    def use_vertex(self) -> bool:
        return self.GOOGLE_GENAI_USE_VERTEXAI == 1

    @property
    def artifact_storage(self) -> str:
        # se explícito, usa; senão, deriva do modo VertexAI
        return self.ARTIFACT_STORAGE_TYPE or ("gcs" if self.use_vertex else "memory")
```

---

### 8.3 Verificação **await** em helpers

Além dos arquivos listados, revise **todos** os *helpers* internos e callbacks para garantir:

* funções que chamam `load_artifact` / `save_artifact` → `async def …`
* chamadas precedidas de `await`

> **Checklist rápido**
>
> * \[\_buscar\_audio\_na\_mensagem] ✅ já alterado
> * \[\_get\_audio\_hash] — permanece síncrono (não faz I/O)
> * qualquer callback em `before_tool` / `after_tool` que use artifacts → tornar async

---

### 8.4 Permissões GCS em produção

1. Crie ou escolha um **Service Account** com:

   * `Vertex AI User`
   * `Storage Object Admin` (ou no mínimo `Storage Object Creator` + `Viewer`) no bucket definido em `GCS_BUCKET_NAME`.

2. Defina `GOOGLE_APPLICATION_CREDENTIALS=/caminho/sa-key.json` no ambiente de execução (Cloud Run, Cloud Functions ou máquina local).

3. Verifique que o bucket está na mesma região de `GOOGLE_CLOUD_LOCATION` para reduzir latência.

---

### 8.5 Fluxo de testes recomendado

| Etapa                          | Variáveis                                                     | Resultado esperado                                                                                  |
| ------------------------------ | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Dev local**                  | `GOOGLE_GENAI_USE_VERTEXAI=0`                                 | Artifacts em memória, descartados ao reiniciar                                                      |
| **Smoke-test GCS** (validação) | `GOOGLE_GENAI_USE_VERTEXAI=1` + chave JSON + bucket existente | Arquivos **.wav / .png / .mp3** surgem em `gs://$GCS_BUCKET_NAME/app_name/user_id/session_id/.../0` |
| **Produção**                   | Igual ao teste GCS + deploy Vertex AI                         | Mesmo comportamento, agora com modelo Vertex AI                                                     |

---

> 🔖 **Depois de incorporar este complemento, o relatório passa a cobrir 100 %** das dependências de ambiente, alternância dev/produção e verificação de await em funções auxiliares.
