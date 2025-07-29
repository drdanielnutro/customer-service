# Relatório de Validação: Sistema de Artifacts do Google ADK

## Resumo Executivo

Esta pesquisa aprofundada sobre o sistema de artifacts do Google ADK revela importantes descobertas sobre a implementação oficial. **Nota importante**: Há uma discrepância temporal significativa - a documentação oficial indica que o ADK não foi lançado em 1º de abril de 2025 como mencionado, mas sim teve releases principais em maio e junho de 2025.

## 1. Classes e Métodos Oficiais do ADK

### CORRETO - Classes Principais

As três classes principais do sistema de artifacts são:

- **BaseArtifactService**: Classe abstrata base definindo a interface
- **GcsArtifactService**: Implementação com Google Cloud Storage 
- **InMemoryArtifactService**: Implementação em memória para desenvolvimento

### CORRETO - Assinaturas de Métodos

```python
class BaseArtifactService:
    async def save_artifact(
        self, app_name: str, user_id: str, session_id: str, 
        filename: str, artifact: types.Part
    ) -> int
    
    async def load_artifact(
        self, app_name: str, user_id: str, session_id: str,
        filename: str, version: Optional[int] = None
    ) -> Optional[types.Part]
    
    async def list_artifact_keys(
        self, app_name: str, user_id: str, session_id: str
    ) -> list[str]
```

### INCORRETO - APIs Deprecated

**Descoberta crítica**: Não há evidências de que `session.get_artifact` tenha existido na API oficial. A documentação mostra apenas:
- `tool_context.load_artifact()` - Método atual e recomendado
- `callback_context.load_artifact()` - Para uso em callbacks

Todos os métodos são **assíncronos** desde a v0.5.0 (maio 2025), requerendo `await`.

## 2. Responsabilidades do Frontend

### CORRETO - Envio de Dados Binários

O frontend deve enviar dados para o backend em um dos formatos:
- **Base64**: Para APIs JSON
- **Multipart/form-data**: Para upload direto de arquivos
- **Sempre incluir MIME type**: `application/pdf`, `image/png`, etc.

### INCORRETO - Criação Automática de Artifacts

**O Runner NÃO cria artifacts automaticamente**. A documentação e exemplos oficiais mostram que:

1. Frontend envia dados para o backend
2. Backend deve explicitamente chamar `context.save_artifact()`
3. Não há criação automática baseada em uploads

Exemplo correto:
```python
# Backend deve criar artifact explicitamente
artifact = types.Part.from_data(
    data=uploaded_bytes,
    mime_type="application/pdf"
)
version = await context.save_artifact("document.pdf", artifact)
```

### NÃO DOCUMENTADO - Integração Flutter

Não existem pacotes oficiais Flutter para ADK. A integração deve ser feita via HTTP API com o backend.

## 3. Fluxo de Processamento

### CORRETO - Acesso via ToolContext

Tools acessam artifacts através do ToolContext:
```python
async def my_tool(filename: str, tool_context: ToolContext):
    artifact = await tool_context.load_artifact(filename)
    if artifact:
        data = artifact.inline_data.data
        mime_type = artifact.inline_data.mime_type
```

### CORRETO - Versionamento Automático

- Cada `save_artifact()` cria nova versão
- Versões começam em 0 e incrementam sequencialmente
- `load_artifact(filename)` retorna versão mais recente
- `load_artifact(filename, version=N)` retorna versão específica

### PARCIALMENTE CORRETO - Referências em Prompts

Para incluir artifacts em prompts, deve-se usar `types.Part` objects:
```python
content = types.Content(
    role="user",
    parts=[
        types.Part(text="Analyze this document"),
        artifact  # types.Part object
    ]
)
```

## 4. Storage e Persistência

### CORRETO - Estrutura de Paths no GCS

```
# Session-scoped
{app_name}/{user_id}/{session_id}/{filename}/{version}

# User-scoped  
{app_name}/{user_id}/user/{filename}/{version}
```

### CORRETO - Diferença entre Escopos

- **Session-scoped**: `"report.pdf"` - apenas na sessão atual
- **User-scoped**: `"user:profile.png"` - acessível entre sessões

### CORRETO - artifact_delta nos Eventos

```python
event.actions.artifact_delta = {
    "report.pdf": 2,  # filename: new_version
    "user:profile.png": 0
}
```

### NÃO DOCUMENTADO - URLs Assinadas

O ADK não expõe diretamente geração de URLs assinadas do GCS. Acesso é via endpoints da API:
```
GET /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}
```

## 5. Configuração e Inicialização

### CORRETO - Setup do Runner

```python
from google.adk.artifacts import GcsArtifactService
from google.adk.runners import Runner

# Configuração correta
artifact_service = GcsArtifactService(bucket_name="my-bucket")

runner = Runner(
    agent=agent,
    app_name="my_app",
    session_service=session_service,
    artifact_service=artifact_service  # Obrigatório
)
```

## Correções Recomendadas

### Arquivo: `backend/adk_config.py`
```python
# INCORRETO
artifact = session.get_artifact(filename)

# CORRETO  
artifact = await tool_context.load_artifact(filename)
```

### Arquivo: `backend/artifact_handler.py`
```python
# INCORRETO - Esperando criação automática
# runner.process_upload(file_data)

# CORRETO - Criação explícita
async def handle_upload(file_data, context):
    artifact = types.Part.from_data(
        data=file_data.content,
        mime_type=file_data.mime_type
    )
    version = await context.save_artifact(
        filename=file_data.filename,
        artifact=artifact
    )
    return {"version": version}
```

### Arquivo: `frontend/lib/adk_service.dart`
```dart
// CORRETO - Sem SDK oficial Flutter
class ADKService {
  Future<Response> uploadFile(File file) async {
    final base64Data = base64Encode(file.readAsBytesSync());
    final mimeType = lookupMimeType(file.path);
    
    return await http.post(
      Uri.parse('$backendUrl/upload'),
      body: jsonEncode({
        'file_data': base64Data,
        'mime_type': mimeType,
        'session_id': sessionId,
      }),
    );
  }
}
```

## Padrões de Implementação Validados

### 1. Criação de Artifacts
✅ Usar `types.Part.from_data()` ou construtor `types.Part()`  
✅ Sempre especificar MIME type  
❌ NÃO esperar criação automática pelo Runner

### 2. Acesso a Artifacts  
✅ Usar `await context.load_artifact()`  
✅ Verificar se artifact não é `None`  
❌ NÃO usar `session.get_artifact()`

### 3. Gerenciamento de Versões
✅ Confiar no versionamento automático  
✅ Usar parâmetro `version` para acessar versões específicas  
✅ Implementar limpeza manual quando necessário

### 4. Integração Frontend-Backend
✅ Frontend envia via HTTP API  
✅ Backend cria artifacts explicitamente  
❌ NÃO há pacotes Flutter oficiais

## Conclusão

O sistema de artifacts do Google ADK fornece uma abstração robusta para gerenciamento de dados binários, mas requer implementação explícita em vários pontos. As principais correções necessárias na implementação incluem:

1. Migrar todas as operações para async/await
2. Remover expectativas de criação automática de artifacts
3. Usar os métodos corretos do context em vez de session
4. Implementar criação explícita de artifacts no backend

A documentação oficial em https://google.github.io/adk-docs/artifacts/ deve ser a referência principal para implementações futuras.