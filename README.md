# Agente de Atendimento ao Cliente Cymbal Home & Garden

Este projeto implementa um agente de atendimento ao cliente alimentado por IA para a Cymbal Home & Garden, uma grande varejista especializada em melhorias domésticas, jardinagem e suprimentos relacionados. O agente foi projetado para fornecer excelente atendimento ao cliente, auxiliar clientes na seleção de produtos, gerenciar pedidos, agendar serviços e oferecer recomendações personalizadas.

## Visão Geral

O Agente de Atendimento ao Cliente da Cymbal Home & Garden foi projetado para proporcionar uma experiência de compra perfeita e personalizada para os clientes. Ele utiliza o Gemini para entender as necessidades dos clientes, oferecer recomendações de produtos sob medida, gerenciar pedidos e agendar serviços. O agente foi projetado para ser amigável, empático e altamente eficiente, garantindo que os clientes recebam o melhor atendimento possível.

## Detalhes do Agente

As principais características do Agente de Atendimento ao Cliente incluem:

| Característica      | Descrição               |
| ------------------- | ----------------------- |
| _Tipo de Interação_ | Conversacional          |
| _Complexidade_      | Intermediária           |
| _Tipo de Agente_    | Agente Único            |
| _Componentes_       | Tools, Multimodal, Live |
| _Vertical_          | Varejo                  |

### Arquitetura do Agente

![Fluxo de Trabalho do Agente de Atendimento ao Cliente](customer_service_workflow.png)

O agente é construído usando uma arquitetura multimodal, combinando entradas de texto e vídeo para proporcionar uma experiência rica e interativa. Ele simula interações com várias ferramentas e serviços, incluindo catálogo de produtos, gerenciamento de inventário, processamento de pedidos e sistemas de agendamento de compromissos. O agente também utiliza um sistema de gerenciamento de sessão para manter o contexto entre as interações e personalizar a experiência do cliente.

É importante notar que este agente não está integrado a um backend real e o comportamento é baseado em ferramentas simuladas. Se você quiser implementar este agente com integração de backend real, precisará editar [customer_service/tools.py](./customer_service/tools/tools.py)

Como as ferramentas são simuladas, você pode notar que algumas mudanças solicitadas não serão aplicadas. Por exemplo, itens recém-adicionados ao carrinho não aparecerão se posteriormente um usuário pedir ao agente para listar todos os itens.

### Características Principais

- **Assistência Personalizada ao Cliente:**
  - Cumprimenta clientes recorrentes pelo nome e reconhece seu histórico de compras.
  - Mantém um tom amigável, empático e prestativo.
- **Identificação e Recomendação de Produtos:**
  - Auxilia clientes na identificação de plantas, mesmo a partir de descrições vagas.
  - Solicita e utiliza recursos visuais (vídeo) para identificar plantas com precisão.
  - Fornece recomendações de produtos personalizadas baseadas em plantas identificadas, necessidades do cliente e localização (ex: Las Vegas, NV).
  - Oferece alternativas aos itens no carrinho do cliente se existirem opções melhores.
- **Gerenciamento de Pedidos:**
  - Acessa e exibe o conteúdo do carrinho de compras do cliente.
  - Modifica o carrinho adicionando e removendo itens baseado em recomendações e aprovação do cliente.
  - Informa clientes sobre vendas e promoções relevantes.
- **Upselling e Promoção de Serviços:**
  - Sugere serviços relevantes, como serviços profissionais de plantio.
  - Lida com consultas sobre preços e descontos, incluindo ofertas de concorrentes.
  - Solicita aprovação do gerente para descontos quando necessário.
- **Agendamento de Compromissos:**
  - Agenda compromissos para serviços de plantio (ou outros serviços).
  - Verifica horários disponíveis e os apresenta ao cliente.
  - Confirma detalhes do compromisso e envia uma confirmação/convite de calendário.
- **Suporte e Engajamento do Cliente:**
  - Envia via SMS ou email instruções de cuidado de plantas relevantes às compras e localização do cliente.
  - Oferece um código QR de desconto para futuras compras na loja para clientes fiéis.
- **Interações Baseadas em Ferramentas:**
  - O agente interage com o usuário usando um conjunto de ferramentas.
  - O agente pode usar múltiplas ferramentas em uma única interação.
  - O agente pode usar as ferramentas para obter informações e modificar o estado da transação do usuário.
- **Avaliação:**
  - O agente pode ser avaliado usando um conjunto de casos de teste.
  - A avaliação é baseada na capacidade do agente de usar as ferramentas e responder às solicitações do usuário.

#### Estado do Agente - Informações padrão do cliente

O estado da sessão do agente é pré-carregado com dados de exemplo do cliente, simulando uma conversa real. Idealmente, este estado deveria ser carregado de um sistema CRM no início da conversa, usando as informações do usuário. Isso assume que ou o agente autentica o usuário ou o usuário já está logado. Se este comportamento deve ser modificado, edite a função [get_customer(current_customer_id: str) em customer.py](./customer_service/entities/customer.py)

#### Ferramentas

O agente tem acesso às seguintes ferramentas:

- `send_call_companion_link(phone_number: str) -> str`: Envia um link para conexão de vídeo.
- `approve_discount(type: str, value: float, reason: str) -> str`: Aprova um desconto (dentro de limites pré-definidos).
- `sync_ask_for_approval(type: str, value: float, reason: str) -> str`: Solicita aprovação de desconto de um gerente.
- `update_salesforce_crm(customer_id: str, details: str) -> dict`: Atualiza registros do cliente no Salesforce.
- `access_cart_information(customer_id: str) -> dict`: Recupera o conteúdo do carrinho do cliente.
- `modify_cart(customer_id: str, items_to_add: list, items_to_remove: list) -> dict`: Atualiza o carrinho do cliente.
- `get_product_recommendations(plant_type: str, customer_id: str) -> dict`: Sugere produtos adequados.
- `check_product_availability(product_id: str, store_id: str) -> dict`: Verifica estoque do produto.
- `schedule_planting_service(customer_id: str, date: str, time_range: str, details: str) -> dict`: Agenda um compromisso de serviço de plantio.
- `get_available_planting_times(date: str) -> list`: Recupera horários disponíveis.
- `send_care_instructions(customer_id: str, plant_type: str, delivery_method: str) -> dict`: Envia informações de cuidado de plantas.
- `generate_qr_code(customer_id: str, discount_value: float, discount_type: str, expiration_days: int) -> dict`: Cria um código QR de desconto.

## Configuração e Instalações

### Pré-requisitos

- Python 3.11+
- Poetry (para gerenciamento de dependências)
- Google ADK SDK (instalado via Poetry)
- Projeto Google Cloud (para integração com Vertex AI Gemini)

### Instalação
1.  **Pré-requisitos:**

    Para as etapas de implantação do Agent Engine, você precisará
    de um Projeto Google Cloud. Depois de criar seu projeto,
    [instale o Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
    Em seguida, execute o seguinte comando para autenticar com seu projeto:
    ```bash
    gcloud auth login
    ```
    Você também precisa habilitar certas APIs. Execute o seguinte comando para habilitar
    as APIs necessárias:
    ```bash
    gcloud services enable aiplatform.googleapis.com
    ```

1.  Clone o repositório:

    ```bash
    git clone https://github.com/google/adk-samples.git
    cd adk-samples/python/agents/customer-service
    ```

    Para o resto deste tutorial **certifique-se de permanecer no diretório `agents/customer-service`**.

2.  Instale as dependências usando Poetry:

- se você não instalou o poetry antes, execute `pip install poetry` primeiro. então você pode criar seu ambiente virtual e instalar todas as dependências usando:

  ```bash
  poetry install
  ```

  Para ativar o ambiente virtual execute:

  ```bash
  poetry env activate
  ```

3.  Configure as credenciais do Google Cloud:

    - Certifique-se de ter um projeto Google Cloud.
    - Certifique-se de ter a API Vertex AI habilitada em seu projeto.
    - Defina as variáveis de ambiente `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT` e `GOOGLE_CLOUD_LOCATION`. Você pode defini-las em seu arquivo `.env` (modifique e renomeie o arquivo .env_sample para .env) ou diretamente em seu shell. Alternativamente, você pode editar [customer_service/config.py](./customer_service/config.py)

    ```bash
    export GOOGLE_CLOUD_PROJECT=SEU_NOME_DO_PROJETO_AQUI
    export GOOGLE_GENAI_USE_VERTEXAI=1
    export GOOGLE_CLOUD_LOCATION=us-central1
    ```

## Executando o Agente

Você pode executar o agente usando o comando ADK em seu terminal.
do diretório raiz do projeto:

1.  Execute o agente no CLI:

    ```bash
    adk run customer_service
    ```

2.  Execute o agente com ADK Web UI:
    ```bash
    adk web
    ```
    Selecione o customer_service no dropdown

### Exemplo de Interação

Aqui está um exemplo rápido de como um usuário pode interagir com o agente:

**Usuário:**:
oi

**Agente**:
Oi Alex, vejo que você é cliente da Cymbal Home & Garden há alguns anos - agradecemos seu negócio! Também vejo que você já tem algumas coisas no seu carrinho. Como posso ajudá-lo a fazer seu jardim crescer hoje?

**Usuário**:
Sim, então estou um pouco confuso. Acabei de comprar algumas...uh...plantas ou flores que queria colocar no quintal. Elas só dizem "anuais que amam sol" nelas. Esqueci completamente de pegar terra para vasos, então estou fazendo um pedido para retirada agora. O problema é que não tenho certeza se a terra para vasos e fertilizante que escolhi são os certos.

**Agente**:
Entendo – pode ser complicado quando você não tem certeza do que tem! Vamos descobrir isso juntos. Não se preocupe, vamos dar o cuidado certo às suas plantas. Para melhor ajudá-lo, você estaria disposto a compartilhar um vídeo rápido das plantas que comprou? Isso me ajudará a identificá-las e garantir que você tenha os suprimentos certos.

**Usuário**:
Claro, como faço isso?

**Agente**:
Acabei de enviar um link por mensagem para o número em seu perfil. Apenas clique nele, e abrirá uma conexão de vídeo segura.

```tool_code
print(send_call_companion_link(phone_number='+12065550123'))
```

```tool_outputs
{'status': 'success', 'message': 'Link sent to +12065550123'}
```

**Usuário**:
Ok, cliquei no link...você consegue ver isso?

**Agente**:
Sim, posso ver você Alex! Você pode apontar a câmera para suas plantas para que eu possa inspecioná-las?

**Usuário**:
Sim, claro!
...

## Avaliando o Agente

Os testes de avaliação avaliam o desempenho geral e as capacidades do agente de maneira holística.

**Passos:**

1.  **Execute os Testes de Avaliação:**

    ```bash
    pytest eval
    ```

    - Este comando executa todos os arquivos de teste dentro do diretório `eval`.

## Testes Unitários

Os testes unitários focam em testar unidades ou componentes individuais do código de forma isolada.

**Passos:**

1.  **Execute os Testes Unitários:**

    ```bash
    pytest tests/unit
    ```

    - Este comando executa todos os arquivos de teste dentro do diretório `tests/unit`.

## Configuração

Você pode encontrar parâmetros de configuração adicionais em [customer_service/config.py](./customer_service/config.py). Isso inclui parâmetros como nome do agente, nome do app e modelo LLM usado pelo agente.

## Implantação no Google Agent Engine

Para herdar todas as dependências do seu agente, você pode construir o arquivo wheel do agente e executar a implantação.

1.  **Construa o arquivo WHL do Agente de Atendimento ao Cliente**

    ```bash
    poetry build --format=wheel --output=deployment
    ```

1.  **Implante o agente no agents engine**
    É importante executar deploy.py de dentro da pasta deployment para que os caminhos estejam corretos

    ```bash
    cd deployment
    python deploy.py
    ```

### Testando a implantação

Este trecho de código é um exemplo de como testar o agente implantado.

```
import vertexai
from customer_service.config import Config
from vertexai.preview.reasoning_engines import AdkApp


configs = Config()

vertexai.init(
    project="<GOOGLE_CLOUD_LOCATION_PROJECT_ID>",
    location="<GOOGLE_CLOUD_LOCATION>"
)

# obtenha o agente baseado no resource id
agent_engine = vertexai.agent_engines.get('DEPLOYMENT_RESOURCE_NAME') # parece com isso projects/PROJECT_ID/locations/LOCATION/reasoningEngines/REASONING_ENGINE_ID

for event in remote_agent.stream_query(
    user_id=USER_ID,
    session_id=session["id"],
    message="Olá!",
):
    print(event)

```

## Aviso Legal

Este exemplo de agente é fornecido apenas para fins ilustrativos e não se destina ao uso em produção. Serve como um exemplo básico de um agente e um ponto de partida fundamental para indivíduos ou equipes desenvolverem seus próprios agentes.

Este exemplo não foi rigorosamente testado, pode conter bugs ou limitações, e não inclui recursos ou otimizações tipicamente necessários para um ambiente de produção (ex: tratamento robusto de erros, medidas de segurança, escalabilidade, considerações de desempenho, logging abrangente, ou opções avançadas de configuração).

Os usuários são os únicos responsáveis por qualquer desenvolvimento adicional, teste, endurecimento de segurança e implantação de agentes baseados neste exemplo. Recomendamos revisão completa, teste e implementação de salvaguardas apropriadas antes de usar qualquer agente derivado em um sistema ativo ou crítico.
