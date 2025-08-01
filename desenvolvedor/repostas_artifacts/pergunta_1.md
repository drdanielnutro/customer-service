# Duvida: 
- 1. InvocationContext vs ToolContext/CallbackContext
  **Minha interpretação**: A documentação afirma que os métodos `save_artifact`, `load_artifact` e `list_artifacts` estão disponíveis apenas em `CallbackContext` e `ToolContext`, NÃO em
  `InvocationContext`.

  **Código em questão**:
  ```python
  from google.adk.agents.invocation_context import InvocationContext

  async def handle_file_upload(file_data: Dict[str, Any], context: InvocationContext):
      version = await context.save_artifact(filename=file_data['filename'], artifact=artifact)

- Pergunta: Este código está INCORRETO porque InvocationContext não possui o método save_artifact? Qual seria o contexto correto a usar?

# Resposta:
1. Validação e Correção do Código
A análise confirma que a sua interpretação está correta. O uso da classe InvocationContext no código de exemplo é, de fato, incorreto, pois essa classe não foi projetada para gerenciar artefatos e, portanto, não possui o método save_artifact.

O InvocationContext foi concebido para fornecer informações contextuais sobre a chamada inicial que acionou o agente, não para interagir com o estado ou os arquivos gerados durante a execução da sua lógica.

Para uma função que manipula arquivos, como handle_file_upload, o contexto apropriado seria ToolContext ou CallbackContext. A escolha depende de como a função é invocada. Se for registrada como uma ferramenta (@tool) que o agente pode utilizar, o contexto correto é ToolContext.

Código Corrigido (assumindo o uso como ferramenta):

from google.adk.agents.tool_context import ToolContext

async def handle_file_upload(file_data: Dict[str, Any], context: ToolContext):
    # Esta é a abordagem correta, pois ToolContext possui o método save_artifact.
    version = await context.save_artifact(filename=file_data['filename'], artifact=artifact)
2. Comparativo de Métodos por Contexto
Uma análise detalhada das classes de contexto do ADK revela diferenças funcionais claras, especialmente no que diz respeito ao gerenciamento de artefatos. A tabela a seguir resume a disponibilidade dos métodos save_artifact, load_artifact e list_artifacts em cada contexto.

Método	InvocationContext	ToolContext	CallbackContext
save_artifact	❌	✅	✅
load_artifact	❌	✅	✅
list_artifacts	❌	✅	✅
3. O Propósito do InvocationContext
O InvocationContext serve a um propósito muito específico: fornecer metadados sobre o evento de invocação que iniciou a execução do agente. Pode ser comparado ao envelope que contém a solicitação inicial. Ele informa ao agente "quem" o chamou e fornece um ID de invocação exclusivo, mas não se envolve com o conteúdo ou os dados que o agente cria subsequentemente. Por esse motivo, sua funcionalidade é intencionalmente limitada e não inclui métodos para manipulação de estado ou arquivos, como save_artifact.

4. A Função do ToolContext e CallbackContext
Em contraste com o InvocationContext, o ToolContext e o CallbackContext funcionam como "conjuntos de ferramentas" fornecidos ao agente quando ele precisa realizar um trabalho concreto.

ToolContext: Este contexto é injetado em qualquer função definida e registrada como uma ferramenta (@tool). Como as ferramentas são destinadas a executar ações—como chamar uma API, consultar um banco de dados ou criar um arquivo—elas requerem a capacidade de salvar os resultados dessas ações. Portanto, o ToolContext está equipado com os métodos save_artifact, load_artifact e list_artifacts.

CallbackContext: Funcionalmente, é muito semelhante ao ToolContext (na verdade, herda dele) e é usado em cenários de retorno de chamada (callbacks). Ele garante que, mesmo em fluxos de execução assíncronos ou etapas de processamento intermediárias, a lógica do agente mantenha a capacidade de gerenciar artefatos de forma consistente.

5. Resumo e Boas Práticas
Para sintetizar as diferenças e orientar o desenvolvimento futuro, as seguintes diretrizes podem ser aplicadas:

Use InvocationContext no ponto de entrada principal do seu agente (@agent) quando precisar acessar metadados sobre a chamada inicial, como o invocation_id.
Use ToolContext no decorador @tool de qualquer função que precise executar uma ação e gerenciar seu resultado, especialmente se essa ação envolver salvar, carregar ou listar arquivos e artefatos.
Use CallbackContext em funções de callback que necessitam interagir com o estado e os artefatos da mesma maneira que uma ferramenta faria, garantindo consistência em diferentes partes do fluxo de execução.
A regra prática é: se a função está executando uma tarefa que pode gerar um arquivo ou dados que precisam ser persistidos, ela deve receber um ToolContext ou CallbackContext, não um InvocationContext.