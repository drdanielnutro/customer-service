# Google Agent Development Kit (ADK) Runner e Controle de Respostas HTTP - Relatório Técnico Detalhado

## Contexto e arquitetura fundamental do ADK Runner

O Google Agent Development Kit (ADK) versão 1.0.0+ utiliza **FastAPI com Uvicorn** como framework web interno, expondo endpoints HTTP automaticamente quando executado com `adk run` ou `adk web`. Entretanto, o ADK não fornece controle direto sobre o formato JSON das respostas através de configuração simples, exigindo abordagens específicas para implementar um contrato de API consistente.

### Mudança crítica no formato de resposta (v1.0.0+)

A versão 1.0.0+ introduziu uma mudança fundamental: todas as respostas JSON mudaram de `snake_case` para `camelCase`. Aplicações existentes precisam ser atualizadas para refletir esta mudança:

```json
// Antes (v0.x)
{"session_id": "123", "user_id": "abc"}

// Agora (v1.0.0+)
{"sessionId": "123", "userId": "abc"}
```

## 1. Endpoints HTTP expostos pelo ADK Runner

### Endpoints principais disponíveis por padrão

```python
# Endpoints de execução
POST /run              # Execução síncrona (retorna todos os eventos)
POST /run_sse          # Execução com Server-Sent Events (streaming)

# Endpoints de sessão
GET    /apps/{app_name}/users/{user_id}/sessions
POST   /apps/{app_name}/users/{user_id}/sessions/{session_id}
DELETE /apps/{app_name}/users/{user_id}/sessions/{session_id}

# Endpoints de artefatos (não há /upload nativo)
GET /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts
GET /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}
PUT /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}

# Endpoint A2A Protocol
GET /.well-known/agent.json  # Agent Card para descoberta

# Endpoints de UI/Debug (quando web=True)
GET /dev-ui ou /          # Interface web de desenvolvimento
GET /docs                 # Swagger UI automática
GET /openapi.json        # Especificação OpenAPI
```

### Formato de request/response padrão

```json
// Request para /run
{
  "appName": "nome_do_agente",
  "userId": "id_usuario",
  "sessionId": "id_sessao",
  "newMessage": {
    "role": "user",
    "parts": [{"text": "mensagem do usuário"}]
  }
}

// Response structure (Event Object)
{
  "content": {
    "parts": [...],
    "role": "model|user"
  },
  "invocationId": "uuid",
  "author": "agent_name",
  "actions": {
    "stateDelta": {},
    "artifactDelta": {}
  },
  "timestamp": 1743712220.385936
}
```

## 2. Estratégias para controlar formato de respostas HTTP

### 2.1 Usando callbacks para interceptar e modificar respostas

O ADK oferece callbacks poderosos que permitem interceptar e modificar respostas em diferentes pontos do pipeline:

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
import json
import time

def unify_response_format_callback(
    callback_context: CallbackContext, 
    content: types.Content
) -> types.Content:
    """Callback que padroniza todas as respostas para formato unificado"""
    if content and content.parts:
        original_response = content.parts[0].text
        
        # Criar resposta no formato unificado desejado
        unified_response = {
            "type": "agent_response",
            "data": {
                "message": original_response,
                "agentId": callback_context.agent_name,
                "sessionId": callback_context.session_id
            },
            "metadata": {
                "timestamp": time.time(),
                "version": "1.0.0"
            },
            "error": None
        }
        
        # Retornar como JSON formatado
        return types.Content(
            role="model",
            parts=[types.Part(text=json.dumps(unified_response))]
        )
    return content

# Aplicar callback ao agente
agent = LlmAgent(
    name="educational_agent",
    model="gemini-2.0-flash",
    instruction="Você é um assistente educacional.",
    after_agent_callback=unify_response_format_callback
)
```

### 2.2 Criando aplicação FastAPI customizada com get_fast_api_app()

A função `get_fast_api_app()` permite criar uma aplicação FastAPI customizada onde você pode adicionar middleware e endpoints próprios:

```python
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app
import json

# Criar app ADK customizada
app: FastAPI = get_fast_api_app(
    agent_dir="./agents",
    session_db_url="sqlite:///sessions.db",
    allow_origins=["*"],
    web=False  # Desabilitar UI web para evitar conflitos
)

# Middleware para padronizar todas as respostas
@app.middleware("http")
async def standardize_responses(request: Request, call_next):
    response = await call_next(request)
    
    # Interceptar respostas JSON do ADK
    if response.headers.get("content-type") == "application/json":
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        try:
            original_data = json.loads(body)
            
            # Transformar para formato unificado
            unified_response = {
                "type": determine_response_type(request.url.path),
                "data": original_data,
                "metadata": {
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "timestamp": time.time()
                },
                "error": None
            }
            
            return JSONResponse(
                content=unified_response,
                status_code=response.status_code
            )
        except:
            pass
    
    return response

def determine_response_type(path: str) -> str:
    if "/run" in path:
        return "agent_execution"
    elif "/artifacts" in path:
        return "artifact_operation"
    elif "/sessions" in path:
        return "session_operation"
    return "general"
```

## 3. Implementando upload de arquivos com formato JSON unificado

O ADK não possui um endpoint `/upload` nativo nem `artifact_handler.py` tradicional. Em vez disso, usa um sistema de serviços de artefatos. Aqui está como implementar upload com validação Pydantic:

### 3.1 Schema unificado para todas as operações

```python
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from enum import Enum

class OperationType(str, Enum):
    UPLOAD = "upload"
    MESSAGE = "message"
    ERROR = "error"
    SESSION = "session"

class UnifiedAPIResponse(BaseModel):
    """Schema unificado para TODAS as respostas da API"""
    type: OperationType
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "upload",
                "success": True,
                "data": {
                    "fileId": "abc123",
                    "filename": "document.pdf",
                    "size": 1024
                },
                "error": None,
                "metadata": {
                    "timestamp": "2025-07-30T10:30:00Z",
                    "requestId": "req_12345"
                }
            }
        }
```

### 3.2 Endpoint customizado de upload

```python
from fastapi import UploadFile, File, HTTPException
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
import google.genai.types as types
import base64
import hashlib

@app.post("/api/v1/upload", response_model=UnifiedAPIResponse)
async def upload_endpoint(
    file: UploadFile = File(...),
    user_id: str = "default_user",
    session_id: str = "default_session"
):
    """Endpoint de upload com resposta unificada"""
    try:
        # Ler arquivo
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()[:12]
        
        # Criar Part object para o ADK
        file_part = types.Part.from_data(
            data=file_content,
            mime_type=file.content_type
        )
        
        # Salvar usando artifact service
        artifact_name = f"{file_hash}_{file.filename}"
        
        # Se tiver acesso ao artifact_service
        # version = artifact_service.save_artifact(
        #     app_name="educational_agent",
        #     user_id=user_id,
        #     session_id=session_id,
        #     filename=artifact_name,
        #     artifact=file_part
        # )
        
        return UnifiedAPIResponse(
            type=OperationType.UPLOAD,
            success=True,
            data={
                "fileId": file_hash,
                "filename": file.filename,
                "artifactName": artifact_name,
                "mimeType": file.content_type,
                "size": len(file_content)
            },
            metadata={
                "timestamp": time.time(),
                "userId": user_id,
                "sessionId": session_id
            }
        )
        
    except Exception as e:
        return UnifiedAPIResponse(
            type=OperationType.ERROR,
            success=False,
            error={
                "code": "UPLOAD_FAILED",
                "message": str(e)
            },
            metadata={
                "timestamp": time.time()
            }
        )
```

### 3.3 Tool para processar uploads dentro do agente

```python
def create_file_upload_tool():
    """Cria ferramenta para processar uploads com formato unificado"""
    
    def handle_file_upload(
        file_data: str,  # Base64 encoded
        filename: str,
        metadata: dict,
        tool_context: ToolContext
    ) -> str:
        """Processa upload mantendo formato unificado"""
        try:
            # Decodificar e processar
            decoded_data = base64.b64decode(file_data)
            file_hash = hashlib.sha256(decoded_data).hexdigest()[:12]
            
            # Criar artefato
            file_part = types.Part.from_data(
                data=decoded_data,
                mime_type=metadata.get('mime_type', 'application/octet-stream')
            )
            
            # Salvar artefato
            artifact_name = f"{file_hash}_{filename}"
            version = tool_context.save_artifact(
                filename=artifact_name,
                artifact=file_part
            )
            
            # Retornar resposta unificada como JSON
            response = UnifiedAPIResponse(
                type=OperationType.UPLOAD,
                success=True,
                data={
                    "fileId": file_hash,
                    "filename": filename,
                    "artifactName": artifact_name,
                    "version": version
                },
                metadata={
                    "processedBy": "file_upload_tool",
                    "timestamp": time.time()
                }
            )
            
            return json.dumps(response.dict())
            
        except Exception as e:
            error_response = UnifiedAPIResponse(
                type=OperationType.ERROR,
                success=False,
                error={
                    "code": "TOOL_ERROR",
                    "message": str(e)
                }
            )
            return json.dumps(error_response.dict())
    
    return FunctionTool(func=handle_file_upload)
```

## 4. Integração com frontend (Flutter/React)

### 4.1 Cliente TypeScript/React com tipagem forte

```typescript
// types.ts
interface UnifiedAPIResponse {
  type: 'upload' | 'message' | 'error' | 'session';
  success: boolean;
  data?: any;
  error?: {
    code: string;
    message: string;
  };
  metadata: {
    timestamp: number;
    [key: string]: any;
  };
}

// ADKClient.ts
class ADKClient {
  private baseUrl: string;
  
  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }
  
  async sendMessage(
    message: string,
    sessionId: string,
    userId: string
  ): Promise<UnifiedAPIResponse> {
    const response = await fetch(`${this.baseUrl}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        appName: 'educational_agent',
        userId,
        sessionId,
        newMessage: {
          role: 'user',
          parts: [{ text: message }]
        }
      })
    });
    
    return await response.json();
  }
  
  async uploadFile(
    file: File,
    sessionId: string,
    userId: string
  ): Promise<UnifiedAPIResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    formData.append('session_id', sessionId);
    
    const response = await fetch(`${this.baseUrl}/api/v1/upload`, {
      method: 'POST',
      body: formData
    });
    
    return await response.json();
  }
  
  // Handler unificado para processar respostas
  handleResponse(response: UnifiedAPIResponse) {
    switch (response.type) {
      case 'message':
        this.handleMessage(response.data);
        break;
      case 'upload':
        this.handleUpload(response.data);
        break;
      case 'error':
        this.handleError(response.error);
        break;
    }
  }
}
```

### 4.2 Cliente Dart/Flutter

```dart
// models.dart
class UnifiedAPIResponse {
  final String type;
  final bool success;
  final Map<String, dynamic>? data;
  final Map<String, String>? error;
  final Map<String, dynamic> metadata;

  UnifiedAPIResponse({
    required this.type,
    required this.success,
    this.data,
    this.error,
    required this.metadata,
  });

  factory UnifiedAPIResponse.fromJson(Map<String, dynamic> json) {
    return UnifiedAPIResponse(
      type: json['type'],
      success: json['success'],
      data: json['data'],
      error: json['error']?.cast<String, String>(),
      metadata: json['metadata'],
    );
  }
}

// adk_service.dart
class ADKService {
  final String baseUrl;
  final http.Client client = http.Client();

  ADKService({required this.baseUrl});

  Future<UnifiedAPIResponse> sendMessage({
    required String message,
    required String sessionId,
    required String userId,
  }) async {
    final response = await client.post(
      Uri.parse('$baseUrl/run'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'appName': 'educational_agent',
        'userId': userId,
        'sessionId': sessionId,
        'newMessage': {
          'role': 'user',
          'parts': [{'text': message}]
        }
      }),
    );

    return UnifiedAPIResponse.fromJson(jsonDecode(response.body));
  }

  Future<UnifiedAPIResponse> uploadFile({
    required File file,
    required String sessionId,
    required String userId,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/v1/upload'),
    );
    
    request.fields['user_id'] = userId;
    request.fields['session_id'] = sessionId;
    request.files.add(await http.MultipartFile.fromPath('file', file.path));
    
    final response = await request.send();
    final responseBody = await response.stream.bytesToString();
    
    return UnifiedAPIResponse.fromJson(jsonDecode(responseBody));
  }
}
```

## 5. Alternativas e workarounds

### 5.1 ADK como biblioteca vs Runner

**Opção 1: ADK como biblioteca (máximo controle)**
```python
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from fastapi import FastAPI

app = FastAPI()

# Configurar agente e runner manualmente
agent = create_educational_agent()
session_service = InMemorySessionService()
runner = Runner(agent=agent, session_service=session_service)

@app.post("/custom-run", response_model=UnifiedAPIResponse)
async def custom_run(request: dict):
    """Endpoint totalmente customizado"""
    events = []
    async for event in runner.run_async(...):
        events.append(event)
    
    # Processar eventos e retornar formato unificado
    return create_unified_response(events)
```

**Opção 2: Proxy/API Gateway**
```nginx
# nginx.conf para padronizar respostas
location /api/ {
    proxy_pass http://adk-backend:8000/;
    
    # Adicionar header para identificar respostas
    add_header X-Response-Format "unified" always;
    
    # Usar sub_filter para modificar respostas
    sub_filter_types application/json;
    sub_filter '"type":' '"responseType":';
}
```

### 5.2 Servidor wrapper customizado

```python
from fastapi import FastAPI, Request
import httpx
import json

wrapper_app = FastAPI()

# Cliente para ADK backend
adk_client = httpx.AsyncClient(base_url="http://localhost:8000")

@wrapper_app.post("/api/{path:path}")
async def proxy_with_transformation(path: str, request: Request):
    """Proxy que transforma todas as respostas para formato unificado"""
    
    # Forward request para ADK
    body = await request.body()
    adk_response = await adk_client.post(
        f"/{path}",
        content=body,
        headers=dict(request.headers)
    )
    
    # Transformar resposta
    original_data = adk_response.json()
    
    return UnifiedAPIResponse(
        type=determine_type_from_path(path),
        success=adk_response.status_code < 400,
        data=original_data,
        metadata={
            "originalPath": path,
            "timestamp": time.time()
        }
    )
```

## 6. Configuração completa para produção

### 6.1 Estrutura de projeto recomendada

```
educational-agent/
├── agents/
│   └── educational_agent.py
├── middleware/
│   └── response_unifier.py
├── schemas/
│   └── unified_response.py
├── tools/
│   └── file_upload_tool.py
├── main.py
├── requirements.txt
└── Dockerfile
```

### 6.2 Arquivo main.py completo

```python
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from middleware.response_unifier import UnifiedResponseMiddleware
from schemas.unified_response import UnifiedAPIResponse
import os

# Configurar ADK app
app = get_fast_api_app(
    agent_dir="./agents",
    session_db_url=os.getenv("DATABASE_URL", "sqlite:///sessions.db"),
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    web=False  # Sem UI em produção
)

# Adicionar middleware de unificação
app.add_middleware(UnifiedResponseMiddleware)

# Endpoints customizados
@app.post("/api/v1/upload", response_model=UnifiedAPIResponse)
async def upload_file(...):
    # Implementação do upload
    pass

# Health check
@app.get("/health", response_model=UnifiedAPIResponse)
async def health_check():
    return UnifiedAPIResponse(
        type="message",
        success=True,
        data={"status": "healthy"},
        metadata={"version": "1.0.0"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 6.3 Docker deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GOOGLE_CLOUD_PROJECT=your-project
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Conclusões e recomendações

### Principais descobertas

1. **Não há controle direto sobre respostas HTTP** no ADK Runner, mas existem várias estratégias viáveis
2. **Callbacks são a forma mais limpa** de modificar respostas sem alterar a infraestrutura
3. **get_fast_api_app() oferece flexibilidade** para adicionar middleware e endpoints customizados
4. **Não existe /upload nativo** - deve ser implementado como endpoint customizado

### Recomendações para implementação

1. **Para máximo controle**: Use ADK como biblioteca com FastAPI customizado
2. **Para desenvolvimento rápido**: Use callbacks + middleware no get_fast_api_app()
3. **Para produção em escala**: Implemente API Gateway ou proxy wrapper
4. **Para consistência**: Defina schemas Pydantic para TODAS as operações

### Padrão recomendado para contrato unificado

```python
# Sempre retorne este formato, independente da operação:
{
    "type": "upload|message|error|session",
    "success": true|false,
    "data": {...},  # Dados específicos da operação
    "error": {      # Apenas se success=false
        "code": "ERROR_CODE",
        "message": "Descrição do erro"
    },
    "metadata": {
        "timestamp": 1234567890,
        "requestId": "req_abc123",
        # ... outros metadados
    }
}
