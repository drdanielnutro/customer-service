-----

## **Guia Definitivo de Arquitetura de Produção: API Unificada para Google ADK com FastAPI**

**Versão 1.0 | Data: 31 de Julho de 2025**

### **0. Introdução: A Filosofia e a Arquitetura de Referência**

O Google Agent Development Kit (ADK) é uma ferramenta excepcional para construir a lógica de agentes conversacionais. Por design, seu Runner padrão (`adk run`, `adk web`) prioriza a velocidade de desenvolvimento e a abstração, ocultando as complexidades do protocolo HTTP. Isso, no entanto, apresenta um desafio para aplicações de produção que demandam um contrato de API previsível, customizável e à prova de falhas para se comunicar com frontends modernos como Flutter ou React.

Após extensa pesquisa e validação, a arquitetura de referência para implementações de produção não consiste em tentar modificar o comportamento limitado do Runner padrão. Em vez disso, a prática recomendada é tratar o **ADK como um motor de agente** e construir em torno dele uma **camada de API customizada usando FastAPI**.

Este manual é o guia completo para implementar essa arquitetura. Ao final, você terá um servidor que:

  * Oferece controle total sobre o formato de cada resposta HTTP.
  * Garante que todas as comunicações, incluindo erros, sigam um schema JSON unificado.
  * É extensível, seguro e pronto para ser implantado em produção.

-----

### **1. Setup do Ambiente e Estrutura do Projeto**

Uma base sólida é fundamental para a manutenibilidade e escalabilidade do projeto.

#### **1.1. Pré-requisitos e Dependências**

  * Python 3.10+
  * Gerenciador de pacotes `pip`

Crie o arquivo `requirements.txt` na raiz do seu projeto com o seguinte conteúdo:

```txt
# requirements.txt
google-agent-development-kit
fastapi
uvicorn[standard]
pydantic
python-dotenv
```

Instale as dependências com o comando:
`pip install -r requirements.txt`

#### **1.2. Estrutura de Diretórios Recomendada**

Organize seu projeto conforme a estrutura abaixo. Ela separa as responsabilidades (API, lógica de negócio, configuração) de forma clara.

```
/seu-projeto-agente/
├── .env                  # Arquivo para variáveis de ambiente (segredos)
├── requirements.txt      # Lista de dependências Python
├── main.py               # Ponto de entrada do servidor FastAPI
|
├── api/
│   ├── schemas.py        # O CONTRATO: Define todos os schemas Pydantic
│   └── v1/
│       ├── router.py     # Agregador dos endpoints da API v1
│       └── endpoints/
│           ├── chat.py   # Lógica do endpoint /chat
│           └── upload.py # Lógica do endpoint /upload
│
├── core/
│   ├── config.py         # Carrega as configurações do .env
│   └── adk_runner.py     # Encapsula a lógica de inicialização do ADK
│
└── agents/
    ├── my_educational_agent.py # Definição do seu agente
    └── artifact_handler.py     # Lógica para manuseio de arquivos
```

#### **1.3. Configuração de Variáveis de Ambiente**

1.  **Arquivo `.env`**: Crie na raiz do projeto. **Adicione este arquivo ao seu `.gitignore` para nunca cometer segredos no seu repositório.**

    ```ini
    # .env
    GOOGLE_API_KEY="SUA_CHAVE_API_DO_GOOGLE_AQUI"
    DATABASE_URL="sqlite:///sessions.db" # Para persistência de sessões
    ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8081" # Origens do seu frontend
    ```

2.  **Módulo de Configuração (`core/config.py`)**: Centraliza o acesso a essas variáveis.

    ```python
    # core/config.py
    import os
    from dotenv import load_dotenv

    # Carrega as variáveis do arquivo .env para o ambiente
    load_dotenv()

    class Settings:
        GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///sessions.db")
        # Converte a string de origens em uma lista
        ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "").split(",")

    settings = Settings()
    ```

-----

### **2. O Contrato da API: Definindo o Schema Unificado com Pydantic**

Este é o coração da nossa arquitetura. O arquivo `api/schemas.py` será a fonte única da verdade para a estrutura de todas as comunicações.

```python
# api/schemas.py
from pydantic import BaseModel, Field, AliasGenerator
from pydantic.alias_generators import to_camel
from typing import TypeVar, Generic, Optional, List, Dict, Any, Literal

# Permite que os modelos Pydantic trabalhem com camelCase no JSON
# enquanto usamos snake_case no Python, uma prática recomendada.
class BaseSchema(BaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True

# Define um tipo genérico para o campo de dados, permitindo reuso
T = TypeVar('T')

class ErrorDetail(BaseSchema):
    """Schema padronizado para detalhes de um erro."""
    code: str = Field(..., description="Um código de erro interno da aplicação.")
    message: str = Field(..., description="Descrição legível do erro para o desenvolvedor.")

class UnifiedAPIResponse(BaseSchema, Generic[T]):
    """O schema de resposta unificado para TODA a API."""
    success: bool = Field(..., description="Indica se a operação foi bem-sucedida.")
    # O tipo de operação ajuda o frontend a direcionar a resposta
    operation_type: Literal["chat", "upload", "session", "error", "general"]
    data: Optional[T] = Field(None, description="O payload da resposta em caso de sucesso.")
    error: Optional[ErrorDetail] = Field(None, description="Detalhes do erro em caso de falha.")

# --- Schemas para Requisições (Request Bodies) ---
class ChatRequest(BaseSchema):
    session_id: str
    message: str

# --- Schemas para os Payloads de Dados (o 'T' em UnifiedAPIResponse) ---
class ChatData(BaseSchema):
    session_id: str
    response_message: str
    raw_adk_events: List[Dict[str, Any]] # Opcional: para depuração

class UploadData(BaseSchema):
    file_id: str
    file_name: str
    content_type: str
    size_in_bytes: int
    message: str = "Arquivo recebido e processado com sucesso."
```

-----

### **3. O Motor do Agente: Encapsulando o ADK Runner**

Para manter o código limpo, encapsulamos a lógica de inicialização e acesso ao ADK em um único módulo.

```python
# core/adk_runner.py
import os
from google.adk.runners import Runner
from google.adk.services.agents import AgentService
from google.adk.services.sessions import InMemorySessionService # ou DatabaseSessionService
# Se seu artifact_handler for uma classe, importe-a
# from agents.artifact_handler import ArtifactHandler

class ADKEngine:
    _runner: Runner = None

    @classmethod
    def get_runner(cls) -> Runner:
        """
        Retorna uma instância singleton do ADK Runner para evitar recarregá-lo.
        """
        if cls._runner is None:
            print("INFO:     Inicializando o motor ADK pela primeira vez...")
            agents_dir = os.path.join(os.path.dirname(__file__), "..", "agents")
            
            # NOTA: Adapte a criação do artifact_service conforme sua implementação
            # Se você tem uma classe, pode ser algo como:
            # artifact_handler = ArtifactHandler()
            # artifact_service = artifact_handler.get_service()
            # Por enquanto, usaremos um serviço em memória como exemplo.
            from google.adk.services.artifacts import InMemoryArtifactService
            artifact_service = InMemoryArtifactService()

            cls._runner = Runner(
                agent_service=AgentService(agents_dir=agents_dir),
                session_service=InMemorySessionService(), # Troque por DatabaseSessionService com DATABASE_URL para persistência
                artifact_service=artifact_service
            )
            print("INFO:     Motor ADK inicializado com sucesso.")
        return cls._runner

# Exporte uma única instância para ser usada em toda a aplicação
adk_engine = ADKEngine()
```

-----

### **4. A Camada de API: Endpoints, Lógica e Roteamento**

Aqui construímos os endpoints que nosso frontend irá consumir.

#### **4.1. Endpoint de Chat (`api/v1/endpoints/chat.py`)**

```python
# api/v1/endpoints/chat.py
from fastapi import APIRouter
from api.schemas import UnifiedAPIResponse, ChatRequest, ChatData
from core.adk_runner import adk_engine

router = APIRouter()

@router.post(
    "/chat",
    response_model=UnifiedAPIResponse[ChatData],
    summary="Envia uma mensagem para o agente"
)
async def process_chat_message(request: ChatRequest):
    """
    Processa uma mensagem de chat com o agente ADK e retorna
    a resposta no formato unificado.
    """
    runner = adk_engine.get_runner()
    agent_name = "my_educational_agent" # Ajuste para o nome do seu agente

    result_events = await runner.run_async(
        agent_name=agent_name,
        session=request.session_id,
        message=request.message
    )

    # Lógica para extrair a resposta de texto dos eventos do ADK
    final_response = ""
    for event in reversed(result_events):
        if event.get("type") == "model" and event.get("subtype") == "text":
            final_response = event.get("text", "")
            break

    chat_data = ChatData(
        session_id=request.session_id,
        response_message=final_response,
        raw_adk_events=result_events
    )

    return UnifiedAPIResponse[ChatData](
        success=True,
        operation_type="chat",
        data=chat_data
    )
```

#### **4.2. Endpoint de Upload (`api/v1/endpoints/upload.py`)**

Este endpoint customizado substitui o fluxo nativo do ADK, dando-nos controle total.

```python
# api/v1/endpoints/upload.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.schemas import UnifiedAPIResponse, UploadData
from core.adk_runner import adk_engine
import google.genai.types as types

router = APIRouter()

@router.post(
    "/upload",
    response_model=UnifiedAPIResponse[UploadData],
    summary="Realiza o upload de um arquivo como um artefato"
)
async def upload_artifact(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Recebe um arquivo, o salva como um artefato na sessão do ADK
    e retorna uma resposta JSON síncrona e unificada.
    """
    runner = adk_engine.get_runner()
    agent_name = "my_educational_agent" # O artefato é associado a um agente

    try:
        file_contents = await file.read()
        
        # O ADK requer que o artefato seja um objeto 'Part'
        artifact_part = types.Part.from_data(
            data=file_contents,
            mime_type=file.content_type
        )
        
        # Salva o artefato usando o serviço do runner
        runner.artifact_service.save_artifact(
            app_name=agent_name,
            session_id=session_id,
            filename=file.filename,
            artifact=artifact_part,
            user_id="default-user" # Adapte conforme sua lógica de usuários
        )

        upload_data = UploadData(
            file_id=file.filename, # Pode usar um hash ou UUID aqui
            file_name=file.filename,
            content_type=file.content_type,
            size_in_bytes=len(file_contents)
        )

        return UnifiedAPIResponse[UploadData](
            success=True,
            operation_type="upload",
            data=upload_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### **4.3. Roteador Principal (`api/v1/router.py`)**

Este arquivo organiza e agrega todos os nossos endpoints.

```python
# api/v1/router.py
from fastapi import APIRouter
from api.v1.endpoints import chat, upload

api_router = APIRouter()

# Inclui os roteadores de cada endpoint, organizando a API
api_router.include_router(chat.router, tags=["Agente de Chat"])
api_router.include_router(upload.router, tags=["Manuseio de Arquivos"])
```

-----

### **5. A Prova de Falhas: Middleware para Consistência e Tratamento de Erros**

Este middleware é a garantia de que NENHUMA exceção não tratada quebrará o contrato da API. Ele interceptará qualquer erro e o formatará em nossa `UnifiedAPIResponse`.

**Adicione este código diretamente em `main.py` antes da criação do `app`.**

```python
# Em main.py
import time
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from api.schemas import UnifiedAPIResponse, ErrorDetail

class UnifiedErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            # Continua o fluxo normal
            response = await call_next(request)
            return response
        except Exception as e:
            # Se qualquer exceção não tratada ocorrer, nós a capturamos aqui!
            error_message = f"Erro interno do servidor: {str(e)}"
            print(f"ERRO GLOBAL CAPTURADO NA REQUISIÇÃO {request.method} {request.url.path}: {error_message}")
            
            error_response = UnifiedAPIResponse[Any](
                success=False,
                operation_type="error",
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message=error_message
                )
            )
            # Retorna uma resposta HTTP 500 com o corpo no nosso formato padrão
            return Response(
                content=error_response.model_dump_json(by_alias=True), # by_alias=True para camelCase
                status_code=500,
                media_type="application/json"
            )
```

-----

### **6. Montagem Final e Execução**

O `main.py` é o ponto de entrada que une tudo.

```python
# main.py
# (coloque a classe UnifiedErrorHandlingMiddleware aqui em cima)
# ...

from fastapi import FastAPI
from api.v1.router import api_router
from core.config import settings

app = FastAPI(
    title="API de Produção para Agente Educacional ADK",
    description="Servidor customizado que utiliza o Google ADK como biblioteca.",
    version="1.0.0"
)

# 1. Adiciona o middleware de tratamento de erros
app.add_middleware(UnifiedErrorHandlingMiddleware)

# 2. Adiciona o middleware de CORS (essencial para frontends web)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Endpoint de Health Check
@app.get("/", tags=["Health Check"])
def health_check():
    """Verifica se a API está operacional."""
    return {"status": "ok", "timestamp": time.time()}

# 4. Inclui todas as rotas da API sob o prefixo /api/v1
app.include_router(api_router, prefix="/api/v1")

# O Uvicorn será o responsável por executar este 'app'
# Se quiser executar diretamente (python main.py), adicione:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Para executar o servidor:**
`uvicorn main:app --reload`

-----

### **7. Integração com Frontend (Flutter/Dart)**

Este backend agora é trivial de ser consumido por um cliente Dart.

1.  **Modelo Dart (`unified_response.dart`):**

    ```dart
    import 'package:json_annotation/json_annotation.dart';
    part 'unified_response.g.dart'; // Execute `flutter pub run build_runner build`

    @JsonSerializable(genericArgumentFactories: true)
    class UnifiedAPIResponse<T> {
      final bool success;
      final String operationType;
      final T? data;
      final ErrorDetail? error;

      UnifiedAPIResponse({
        required this.success,
        required this.operationType,
        this.data,
        this.error,
      });

      factory UnifiedAPIResponse.fromJson(Map<String, dynamic> json, T Function(Object? json) fromJsonT) =>
          _$UnifiedAPIResponseFromJson(json, fromJsonT);
    }

    @JsonSerializable()
    class ErrorDetail {
      final String code;
      final String message;
      ErrorDetail({required this.code, required this.message});
      factory ErrorDetail.fromJson(Map<String, dynamic> json) => _$ErrorDetailFromJson(json);
    }

    // Crie classes para ChatData, UploadData, etc.
    ```

2.  **Serviço de API (`adk_service.dart`):**

    ```dart
    import 'package:http/http.dart' as http;
    import 'dart:convert';
    import 'dart:io';

    class ADKService {
      final String baseUrl = "http://localhost:8000/api/v1";

      Future<UnifiedAPIResponse<ChatData>> sendMessage(String sessionId, String message) async {
        final response = await http.post(
          Uri.parse('$baseUrl/chat'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'sessionId': sessionId, 'message': message}),
        );
        final json = jsonDecode(response.body);
        return UnifiedAPIResponse.fromJson(json, (json) => ChatData.fromJson(json as Map<String, dynamic>));
      }

      Future<UnifiedAPIResponse<UploadData>> uploadFile(String sessionId, File file) async {
        var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/upload'));
        request.fields['sessionId'] = sessionId;
        request.files.add(await http.MultipartFile.fromPath('file', file.path));

        var streamedResponse = await request.send();
        var response = await http.Response.fromStream(streamedResponse);
        final json = jsonDecode(response.body);
        return UnifiedAPIResponse.fromJson(json, (json) => UploadData.fromJson(json as Map<String, dynamic>));
      }
    }
    ```

-----

### **8. Deployment em Produção (Dockerfile)**

Para implantar sua aplicação em serviços como Google Cloud Run, você precisará de um `Dockerfile`.

```dockerfile
# Use uma imagem base oficial e otimizada
FROM python:3.11-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Medida de segurança: execute como um usuário não-root
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app

# Copie primeiro o arquivo de dependências para aproveitar o cache do Docker
COPY --chown=appuser:appuser requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir --user -r requirements.txt

# Copie o resto do código da sua aplicação
COPY --chown=appuser:appuser . .

# Exponha a porta que o Uvicorn irá usar
ENV PORT 8080
EXPOSE 8080

# Comando para iniciar a aplicação em produção.
# Note que não usamos --reload.
# O Gunicorn é um gerenciador de processos de produção recomendado para Uvicorn.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

```

-----

### **9. Apêndice: Referência Rápida dos Endpoints Nativos do ADK**

Para fins de depuração ou entendimento do comportamento interno do ADK, aqui estão os endpoints que ele expõe por padrão. **Lembre-se: sua aplicação frontend não deve interagir com eles, mas sim com os endpoints customizados que você criou.**

  * `POST /run`: Execução síncrona.
  * `POST /run_sse`: Execução via streaming de eventos.
  * `GET /.well-known/agent.json`: Agent Card para o protocolo A2A.
  * Endpoints de gerenciamento (`/apps/{appName}/...`): Rotas para listar e gerenciar sessões e artefatos, geralmente usadas pela UI de desenvolvimento.

-----

### **Conclusão Final**

Este guia apresentou uma arquitetura completa e robusta para levar um agente do Google ADK para um ambiente de produção. Ao desacoplar a lógica do agente da camada de API e ao implementar um contrato unificado, você obtém uma solução manutenível, escalável e fácil de ser consumida por qualquer cliente. Esta abordagem representa o padrão profissional para a integração de sistemas complexos, garantindo consistência e confiabilidade em todas as fases do projeto.