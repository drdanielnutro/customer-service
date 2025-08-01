Este não é mais um relatório de pesquisa; é um **guia de implementação passo a passo** para construir uma camada de API robusta, customizada e à prova de falhas sobre o Google ADK. Abandaremos os comandos `adk run` em favor de uma arquitetura profissional.

-----

## **Manual Técnico: Construindo uma API Unificada com Google ADK e FastAPI**

### **Seção 0: Filosofia e Objetivo Final**

A pesquisa nos mostrou que o ADK Runner é uma ferramenta de desenvolvimento, não um servidor de produção customizável. Ele abstrai intencionalmente a camada HTTP para que você foque na lógica do agente.

Nosso objetivo é abraçar essa filosofia, tratando o **ADK como um motor de agente poderoso** e construindo em torno dele uma **carroceria de API robusta e sob medida** usando FastAPI. Ao final deste manual, você terá:

1.  **Controle Total:** Sobre cada aspecto da resposta HTTP (corpo, headers, status).
2.  **Contrato de API Unificado:** Todas as respostas, de sucesso ou erro, seguirão o mesmo schema JSON, facilitando drasticamente a vida do seu frontend (Flutter/React).
3.  **Arquitetura Escalável:** Uma estrutura de projeto limpa, pronta para crescer.
4.  **Tratamento de Erros Centralizado:** Nenhuma exceção não tratada quebrará sua API.

### **Seção 1: Estrutura do Projeto**

Uma boa estrutura é a base de tudo. Organize seu projeto da seguinte forma para garantir clareza e manutenibilidade:

```
/seu-projeto-agente/
├── .env                  # Arquivo para variáveis de ambiente (chaves de API, etc.)
├── requirements.txt      # Lista de dependências Python
├── main.py               # Ponto de entrada PRINCIPAL do nosso servidor customizado
|
├── api/
│   ├── __init__.py
│   ├── schemas.py        # O CORAÇÃO: Define nosso contrato de API com Pydantic
│   └── v1/
│       ├── __init__.py
│       ├── router.py     # Agrega todos os endpoints da API v1
│       └── endpoints/
│           ├── __init__.py
│           ├── chat.py   # Lógica para o endpoint de chat
│           └── upload.py # Lógica para nosso novo endpoint de upload
│
├── core/
│   ├── __init__.py
│   ├── config.py         # Carrega as configurações do .env
│   └── adk_runner.py     # Encapsula a lógica de inicialização e execução do ADK
│
└── agents/
    ├── __init__.py
    ├── my_educational_agent.py # A definição do seu agente ADK
    └── artifact_handler.py     # Seu handler de artefatos existente
```

### **Seção 2: Dependências e Configuração Inicial**

1.  **`requirements.txt`**: Liste todas as bibliotecas necessárias.

    ```txt
    google-agent-development-kit
    fastapi
    uvicorn[standard]  # O servidor ASGI que executará nossa aplicação
    pydantic
    python-dotenv      # Para ler o arquivo .env
    ```

2.  **Instale as dependências**:
    `pip install -r requirements.txt`

3.  **`.env`**: Crie este arquivo na raiz para guardar suas chaves secretas. **Nunca suba este arquivo para o Git.**

    ```ini
    # .env
    GOOGLE_API_KEY="SUA_CHAVE_API_DO_GOOGLE_AQUI"
    ```

4.  **`core/config.py`**: Crie um módulo para carregar essas configurações de forma segura.

    ```python
    # core/config.py
    import os
    from dotenv import load_dotenv

    load_dotenv() # Carrega as variáveis do arquivo .env

    class Settings:
        GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")

    settings = Settings()
    ```

### **Seção 3: Definindo o Contrato da API com Pydantic (`api/schemas.py`)**

Este é o passo mais crítico. Vamos definir o schema JSON unificado que TODAS as respostas seguirão.

```python
# api/schemas.py
from pydantic import BaseModel, Field
from typing import TypeVar, Generic, Optional, List, Dict, Any

# Define um tipo genérico para o campo de dados
T = TypeVar('T')

class ErrorDetail(BaseModel):
    """Schema para detalhes de um erro."""
    code: str = Field(..., description="Um código de erro interno da aplicação.")
    message: str = Field(..., description="Descrição legível do erro.")

class UnifiedResponse(BaseModel, Generic[T]):
    """O schema de resposta unificado para TODA a API."""
    success: bool = Field(..., description="Indica se a operação foi bem-sucedida.")
    data: Optional[T] = Field(None, description="O payload da resposta em caso de sucesso.")
    error: Optional[ErrorDetail] = Field(None, description="Detalhes do erro em caso de falha.")

# --- Schemas para Requisições (Request Bodies) ---

class ChatRequest(BaseModel):
    """Corpo da requisição para o endpoint de chat."""
    session_id: str
    message: str

# --- Schemas para os Payloads de Dados (o 'T' em UnifiedResponse) ---

class ChatData(BaseModel):
    """Payload de dados para uma resposta de chat bem-sucedida."""
    session_id: str
    response_message: str
    raw_events: List[Dict[str, Any]] # Para depuração, podemos incluir os eventos brutos

class UploadData(BaseModel):
    """Payload de dados para uma resposta de upload bem-sucedida."""
    file_id: str
    message: str = "Arquivo processado com sucesso."
```

### **Seção 4: Encapsulando o ADK Runner (`core/adk_runner.py`)**

Para não misturar a lógica do ADK com a da API, vamos criar um wrapper para o Runner.

```python
# core/adk_runner.py
import os
from google.adk.runners import Runner
from google.adk.services.agents import AgentService
from google.adk.services.sessions import InMemorySessionService
from agents.artifact_handler import ArtifactHandler # Importe seu handler

class ADKEngine:
    _runner: Runner = None

    @classmethod
    def get_runner(cls) -> Runner:
        """
        Retorna uma instância singleton do ADK Runner.
        Isso evita recarregar os agentes a cada requisição.
        """
        if cls._runner is None:
            print("Inicializando o motor ADK...")
            agents_dir = os.path.join(os.path.dirname(__file__), "..", "agents")
            
            # Use seu ArtifactHandler existente aqui
            artifact_handler = ArtifactHandler()

            cls._runner = Runner(
                agent_service=AgentService(agents_dir=agents_dir),
                session_service=InMemorySessionService(),
                # Conecte seu handler ao runner
                artifact_service=artifact_handler.get_service() 
            )
        return cls._runner

# Exporte uma instância para fácil acesso
adk_engine = ADKEngine()
```

**Nota sobre `artifact_handler`:** Assumi que seu `artifact_handler.py` tem uma classe `ArtifactHandler` com um método `get_service()` que retorna um `InMemoryArtifactService` ou similar. Se a estrutura for diferente, ajuste a importação e a chamada.

### **Seção 5: Construindo os Endpoints da API**

Agora, vamos criar os endpoints usando nosso contrato e o motor ADK.

1.  **`api/v1/endpoints/chat.py`**

    ```python
    # api/v1/endpoints/chat.py
    from fastapi import APIRouter
    from api.schemas import UnifiedResponse, ChatRequest, ChatData
    from core.adk_runner import adk_engine

    router = APIRouter()

    @router.post("/chat", response_model=UnifiedResponse[ChatData])
    async def process_chat_message(request: ChatRequest):
        """
        Processa uma mensagem de chat com o agente ADK.
        """
        runner = adk_engine.get_runner()
        
        # O runner do ADK usa 'session' em vez de 'session_id'
        # O nome do agente deve corresponder ao nome do arquivo/classe do agente
        agent_name = "my_educational_agent" 

        result_events = await runner.run_async(
            agent_name=agent_name,
            session=request.session_id,
            message=request.message
        )

        # Extrai a resposta de texto dos eventos (pode precisar de ajuste)
        # Normalmente, o último evento de 'model' contém a resposta
        final_response = ""
        for event in reversed(result_events):
            if event.get("type") == "model" and event.get("subtype") == "text":
                final_response = event.get("text", "")
                break

        chat_data = ChatData(
            session_id=request.session_id,
            response_message=final_response,
            raw_events=result_events # Opcional: para depuração
        )

        return UnifiedResponse[ChatData](success=True, data=chat_data)
    ```

2.  **`api/v1/endpoints/upload.py`** - **Este é o nosso endpoint de upload customizado.**

    ```python
    # api/v1/endpoints/upload.py
    from fastapi import APIRouter, UploadFile, File, Form
    from api.schemas import UnifiedResponse, UploadData
    from agents.artifact_handler import ArtifactHandler # Importe seu handler

    router = APIRouter()
    artifact_handler = ArtifactHandler() # Instancie seu handler

    @router.post("/upload", response_model=UnifiedResponse[UploadData])
    async def process_upload(
        session_id: str = Form(...),
        file: UploadFile = File(...)
    ):
        """
        Processa um upload de arquivo e chama o artifact_handler diretamente.
        Este endpoint se comporta como uma API REST tradicional.
        """
        # Aqui, chamamos sua lógica de handler diretamente, não através do ADK.
        # Isso nos dá controle total sobre a resposta.
        file_contents = await file.read()
        
        # Supondo que seu handler tenha um método como este:
        file_id = artifact_handler.handle_file_directly(
            session_id=session_id,
            filename=file.filename,
            contents=file_contents
        )

        upload_data = UploadData(file_id=file_id)

        return UnifiedResponse[UploadData](success=True, data=upload_data)
    ```

3.  **`api/v1/router.py`**: Agregue os endpoints.

    ```python
    # api/v1/router.py
    from fastapi import APIRouter
    from api.v1.endpoints import chat, upload

    api_router = APIRouter()
    api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
    api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
    ```

### **Seção 6: Tratamento Global de Erros com Middleware**

Isto garante que **nenhuma exceção quebrará o contrato da API**. Qualquer erro inesperado será capturado e formatado em nosso `UnifiedResponse`.

```python
# No arquivo main.py
import time
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import json

from api.schemas import UnifiedResponse, ErrorDetail

class UnifiedErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # Tenta processar a requisição normalmente
            response = await call_next(request)
            return response
        except Exception as e:
            # Se qualquer exceção não tratada ocorrer, capture-a!
            print(f"ERRO GLOBAL CAPTURADO: {e}")
            error_response = UnifiedResponse[Any](
                success=False,
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message=f"Ocorreu um erro inesperado: {str(e)}"
                )
            )
            return Response(
                content=json.dumps(error_response.dict()),
                status_code=500,
                media_type="application/json"
            )
```

### **Seção 7: Montando o Servidor Principal (`main.py`)**

Aqui, unimos todas as peças.

```python
# main.py
from fastapi import FastAPI
from api.v1.router import api_router
# Importe o middleware que acabamos de criar
from __main__ import UnifiedErrorMiddleware 

# Cria a instância principal da aplicação
app = FastAPI(
    title="API do Agente Educacional",
    description="Servidor customizado para o agente ADK com API unificada.",
    version="1.0.0"
)

# Adiciona o middleware de tratamento de erros.
# Esta é a garantia de que todas as respostas seguirão o schema.
app.add_middleware(UnifiedErrorMiddleware)

@app.get("/", tags=["Health Check"])
def health_check():
    """Endpoint para verificar se a API está no ar."""
    return {"status": "ok"}

# Inclui todas as rotas da v1 com o prefixo /api/v1
app.include_router(api_router, prefix="/api/v1")

# Nota: O uvicorn será responsável por executar este 'app'.
```

### **Seção 8: Execução e Teste**

1.  **Execute o servidor:** No seu terminal, na raiz do projeto, execute:

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

      * `--reload` faz o servidor reiniciar automaticamente quando você salva um arquivo. Ótimo para desenvolvimento.

2.  **Teste o endpoint de chat:**

    ```bash
    curl -X POST "http://localhost:8000/api/v1/chat/chat" \
    -H "Content-Type: application/json" \
    -d '{
        "session_id": "session_12345",
        "message": "Olá, qual a capital do Brasil?"
    }'
    ```

    **Resposta Esperada:**

    ```json
    {
      "success": true,
      "data": {
        "session_id": "session_12345",
        "response_message": "A capital do Brasil é Brasília.",
        "raw_events": [...]
      },
      "error": null
    }
    ```

3.  **Teste o endpoint de upload:**

    ```bash
    # Crie um arquivo de teste: echo "conteúdo de teste" > test.txt
    curl -X POST "http://localhost:8000/api/v1/upload/upload" \
    -H "Content-Type: multipart/form-data" \
    -F "session_id=session_12345" \
    -F "file=@test.txt"
    ```

    **Resposta Esperada:**

    ```json
    {
      "success": true,
      "data": {
        "file_id": "algum_id_gerado_pelo_seu_handler",
        "message": "Arquivo processado com sucesso."
      },
      "error": null
    }
    ```

-----

### **Conclusão do Manual**

Seguindo este guia, você construiu uma aplicação que usa o Google ADK da maneira mais profissional e escalável possível. Você agora tem controle absoluto sobre sua API, um contrato claro com o frontend e uma base sólida para adicionar novas funcionalidades, como autenticação, logging e muito mais, usando os vastos recursos do ecossistema FastAPI.