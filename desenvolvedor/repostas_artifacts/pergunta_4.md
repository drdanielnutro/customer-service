# Dúvida:
4. Arquitetura Correta para Upload via Frontend

  Cenário: Frontend Flutter enviando arquivos via HTTP POST para o backend ADK.

  Perguntas:
  - Como o Runner do ADK expõe endpoints HTTP para upload?
  - É necessário criar uma Tool específica para processar uploads?
  - O InvocationContext é acessível diretamente em handlers HTTP ou apenas dentro de Tools/Callbacks?
  - Existe algum exemplo oficial de integração frontend->ADK para uploads?

# Resposta:
Research Report: Implementing File Uploads in the Agent Development Kit (ADK)
1. Exposição de Endpoints HTTP pelo ADK Runner
The Agent Development Kit (ADK) abstracts the underlying web server to allow developers to focus on agent logic. It exposes agent functionalities as web services primarily through the adk api_server command. github.io youtube.com This command launches a local web server, ideal for local testing, development, and integration with custom frontends. github.io youtube.com

Mecanismo de inicialização do servidor web
Executing adk api_server starts a Uvicorn server that hosts a FastAPI application, typically on port 8000. github.io youtube.com This server automatically exposes a set of RESTful API endpoints for managing sessions and executing agents. github.io medium.com Key endpoints include:

Session Management: Routes for creating (POST), retrieving (GET), and deleting (DELETE) agent sessions under /apps/{app_name}/users/{user_id}/sessions/{session_id}. medium.com
Agent Execution: Endpoints like POST /run for synchronous execution, POST /run_sse for streaming events with Server-Sent Events (SSE), and WEBSOCKET /run_live for real-time bidirectional communication. medium.com
For debugging, the API server automatically generates interactive Swagger UI documentation, which is accessible at http://localhost:8000/docs. github.io This interface allows developers to inspect all available endpoints, their parameters, and schemas, and to send live requests to running agents. github.io

Mapeamento automático de Tools para rotas HTTP
The ADK framework does not map each Tool to a unique HTTP route. Instead, it abstracts the web layer entirely. All interactions with tools are funneled through the main agent execution endpoints (/run, /run_sse, etc.). The agent's Large Language Model (LLM) is responsible for interpreting the user's prompt and deciding which registered Tool to invoke based on its schema and description.

Como registrar rotas POST para lidar com requisições multipart/form-data
The ADK documentation does not provide a direct mechanism for developers to define and register custom HTTP routes, such as a POST endpoint to handle multipart/form-data requests. The framework is not designed for developers to handle HTTP request and response objects directly. The intended architectural pattern for managing file uploads is through the built-in Artifact Service. The responsibility for receiving the upload and creating the artifact is implicitly handled by the ADK framework, which then makes the file available to tools via the InvocationContext.

2. Implementação de uma Tool para Upload de Arquivos
In the ADK, a Tool represents a capability an agent can use to interact with the outside world. For processing file uploads, the recommended approach is to use a FunctionTool in combination with the Artifact Service, rather than creating a tool that directly ingests an HTTP request.

Estrutura e definição de uma adk.Tool para upload
The most common method for creating a tool is with FunctionTool, which converts a standard Python function into a tool usable by the agent. The ADK inspects the function's signature—its name, docstring, parameters, and type annotations—to generate a schema. This schema is used by the LLM to understand how and when to call the tool.

For file processing, a function can be defined to accept the file's identifier (e.g., its name) as a string parameter. The logic for accessing and processing the file's content is implemented within this function, using the ToolContext.

Diferenças entre receber dados JSON e multipart/form-data
A FunctionTool in the ADK does not directly receive raw request data like JSON or multipart/form-data. The data flow is abstracted:

JSON Data: Simple data types like strings and integers, typically sent in a JSON payload to the /run endpoint, can be mapped directly to the function's parameters by the LLM.
File Data (multipart/form-data): File data is not passed directly to the tool's function. The architectural pattern requires the file to be first uploaded and stored as an "Artifact." The user prompt or application logic then instructs the agent to run the tool, passing the name of the artifact as a string argument. The tool then uses the ToolContext to load the artifact's content for processing.
A necessidade (ou não) de uma Tool exclusiva para a funcionalidade de upload
It is not necessary to create a specialized subclass of adk.Tool to handle file uploads. The FunctionTool class is flexible enough for this task. A well-defined FunctionTool that leverages the ToolContext to access artifacts is the standard and recommended approach within the ADK architecture. The core challenge is not in the tool's implementation but in orchestrating the initial upload to the Artifact Service, a step that is not explicitly detailed in the documentation for custom frontend integrations.

3. O Papel do InvocationContext no Manuseio de Arquivos
The adk.InvocationContext is a central object that encapsulates all relevant information for a complete agent interaction cycle. Its primary role in file handling is not to hold the file data itself, but to provide access to the services that manage these files.

Definição e escopo do InvocationContext em requisições HTTP
The InvocationContext is created by the framework at the beginning of an invocation (e.g., a call to /run_sse) and is passed implicitly to the agent's code, callbacks, and tools. It provides access to the entire state of the current invocation. More specific, derived contexts exist:

ToolContext: Passed to tool functions, containing information specific to that tool call.
CallbackContext: Passed to callback functions (e.g., before_tool_callback).
Crucially, the context abstracts away the low-level HTTP request object, providing a higher-level interface to the interaction's state and services.

Atributos e métodos para acessar arquivos carregados
The InvocationContext and its derivatives provide access to configured services, most importantly the artifact_service. This service is responsible for storing and retrieving binary data, referred to as "Artifacts." The methods for file manipulation are exposed on the ToolContext and CallbackContext for convenience.

Método	Argumentos	Retorna	Descrição
load_artifact()	filename: str	google.genai.types.Part	Primary read method. Loads the content of a previously saved artifact. The returned Part object contains the file's bytes and its mime_type.
save_artifact()	filename: str, artifact: Part	None	Saves or updates an artifact in the ArtifactService. Useful if a tool generates a new file.
list_artifacts()	None	List[ArtifactMetadata]	Lists metadata for all available artifacts in the current session.
delete_artifact()	filename: str, version: Optional[int] = None	None	Removes an artifact from the ArtifactService.
Como extrair o conteúdo do arquivo, nome, e tipo MIME
To process an uploaded file within a FunctionTool, a developer uses the load_artifact method provided by the ToolContext.

The filename is passed as a string argument to the tool function.
The tool calls tool_context.load_artifact(filename=the_filename).
This method returns a Part object, from which the file content (as bytes) and its MIME type can be accessed.
4. Fluxo de Dados Completo e Exemplo Prático
While the ADK documentation provides the necessary components for building a file upload feature, it lacks a single, end-to-end tutorial demonstrating the complete flow from a custom frontend. The following data flow is inferred from the available documentation and community discussions.

Resumo do fluxo: Requisição HTTP do frontend -> Recepção pelo Runner do ADK -> Processamento pela Tool
Server Initialization: A developer starts the ADK web server using adk api_server.
Artifact Creation: A frontend application sends the file (e.g., via a multipart/form-data POST request) to the backend. The ADK server receives this and uses the configured ArtifactService (e.g., InMemoryArtifactService or GcsArtifactService) to save the file as a named artifact. This step is handled transparently by the adk web interface but must be orchestrated in a custom integration.
Agent Invocation: The frontend sends a second request to an agent execution endpoint (e.g., /run_sse). The payload of this request includes a user prompt that references the newly created artifact by its name.
Tool Selection: The agent's LLM processes the prompt and determines that a specific FunctionTool designed for file processing should be called, passing the artifact's name as an argument.
File Processing: Inside the tool's function, the ToolContext is used to call load_artifact(filename). This retrieves the file's content from the ArtifactService.
Response: The tool processes the file and returns a result to the agent. The agent then formulates a final response, which is sent back to the frontend over the established HTTP connection.
Análise de exemplos de código ou tutoriais oficiais (se disponíveis)
Research into the official ADK documentation and related community resources did not uncover any end-to-end examples or official tutorials that specifically demonstrate how to implement a file upload endpoint connecting a custom frontend to an ADK backend. Existing tutorials focus on text-based communication. This lack of a clear, cohesive example connecting the frontend upload to the backend artifact creation represents the primary gap in the current documentation for this use case.

Demonstração de um snippet de código para um endpoint de upload completo
Given the absence of an official example, a complete code snippet cannot be provided. However, a developer can implement this functionality by combining the documented components:

Run the agent as an API server.
Implement a FunctionTool that accepts a filename as a string.
Within that function, use the tool_context.load_artifact() method to access file content.
For the frontend, orchestrate a two-step process: first, upload the file to create the artifact, and second, call the agent with a prompt referencing the artifact's name. The mechanism for the first step in a custom FastAPI setup is the part that would require implementation beyond the direct guidance of the ADK documentation.