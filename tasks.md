# Plano de Refatoração do Customer Service Agent

## 1. Leitura e Contexto

### 1.1 Mapeamento da estrutura atual

O relatório de mapeamento detalhado ("customer_service_mapeamento_orginal.md") descreve a arquitetura monolítica atual do pacote `customer_service`:

```text
# customer_service_mapeamento_orginal.md (linhas 1–39)
# … Arquitetura de Alto Nível …
agentePrincipal → usa → toolsModule / sharedLibsModule / entitiesModule / promptsModule / configModule
```

Em resumo, hoje temos:

```
customer_service/
├── agent.py                 # Lógica central do agente
├── config.py                # Configurações
├── prompts.py               # Todos os prompts
├── entities/                # Modelos de domínio (entidades)
├── shared_libraries/
│   └── callbacks.py         # Todas as callbacks num único módulo
└── tools/
    └── tools.py             # Todas as ferramentas num único módulo
```

### 1.2 Diretrizes de refatoração (AGENTS.md)

O **AGENTS.md** dita as regras para transformar monolitos em estruturas modulares:

- **Estrutura Padrão**: sub‑agentes LLM devem ter três arquivos (`__init__.py`, `agent.py`, `prompt.py`).
- **Estruturas Auxiliares**: callbacks e ferramentas em pacotes dedicados (`callbacks/`, `tools/`).
- **Planejamento Estruturado**: refatoração faseada (criar dirs, extrair, ajustar imports, testar).

## 2. Objetivo da Refatoração

> Modularizar o código: cada tool em seu próprio módulo, cada callback em seu módulo próprio, sem alterar o comportamento do agente.

## 3. Proposta de Estrutura Modular

A estrutura alvo proposta:

```
customer_service/
├── __init__.py
├── agent.py
├── config.py
├── prompts.py
├── entities/
│   ├── __init__.py
│   └── customer.py
├── shared_libraries/
│   └── callbacks/
│       ├── __init__.py
│       ├── rate_limit_callback.py
│       ├── before_agent_callback.py
│       ├── before_tool_callback.py
│       ├── after_tool_callback.py
│       └── validate_customer_id_callback.py
└── tools/
    ├── __init__.py
    ├── send_call_companion_link/
    │   ├── __init__.py
    │   └── send_call_companion_link.py
    ├── approve_discount/
    │   ├── __init__.py
    │   └── approve_discount.py
    ├── sync_ask_for_approval/
    │   ├── __init__.py
    │   └── sync_ask_for_approval.py
    ├── update_salesforce_crm/
    │   ├── __init__.py
    │   └── update_salesforce_crm.py
    ├── access_cart_information/
    │   ├── __init__.py
    │   └── access_cart_information.py
    ├── modify_cart/
    │   ├── __init__.py
    │   └── modify_cart.py
    ├── get_product_recommendations/
    │   ├── __init__.py
    │   └── get_product_recommendations.py
    ├── check_product_availability/
    │   ├── __init__.py
    │   └── check_product_availability.py
    ├── schedule_planting_service/
    │   ├── __init__.py
    │   └── schedule_planting_service.py
    ├── get_available_planting_times/
    │   ├── __init__.py
    │   └── get_available_planting_times.py
    ├── send_care_instructions/
    │   ├── __init__.py
    │   └── send_care_instructions.py
    └── generate_qr_code/
        ├── __init__.py
        └── generate_qr_code.py
```

## 4. Fases de Refatoração

| Fase | Descrição                                                                                       |
|:----:|:------------------------------------------------------------------------------------------------|
| 1    | **Criar estrutura de diretórios vazia** (_tools_/ sub‑folders; _shared_libraries/callbacks_).    |
| 2    | **Copiar** `tools.py` e `callbacks.py` para novos módulos correspondentes.                       |
| 3    | **Extrair** cada função de tool para seu arquivo próprio.                                       |
| 4    | **Extrair** cada callback para seu módulo próprio.                                              |
| 5    | **Ajustar** `__init__.py` em _tools_/ e em _callbacks_/ para exportar as funções no nível de pacote. |
| 6    | **Atualizar** `agent.py`: ajustar imports de _tools_ e _callbacks_ para os novos caminhos.       |
| 7    | **Testar** importações e executar o agente (`python -c "from customer_service import root_agent"`). |

## 5. Pontos de Atenção

### 5.1 Código Monolito Atual

- **tools.py** e **callbacks.py** concentram múltiplas funções num único arquivo.
- **agent.py** importa tudo de uma vez, criando alto acoplamento.

### 5.2 Guia "Mirror, Don’t Improve"

> Durante todo o processo, **não** criar abstrações extras nem funcionalidades novas. Apenas **mover/renomear** código existente.

## 6. Atualização da Documentação

> Atualizar **README.md** com a nova árvore de diretórios e instruções de importação.

## 7. Checklist Final

- [ ] Cada tool em seu módulo dedicado sob `tools/`.
- [ ] Cada callback em seu módulo dedicado sob `shared_libraries/callbacks/`.
- [ ] `__init__.py` exporta corretamente funções nos novos pacotes.
- [ ] `agent.py` principal carregando _tools_ e _callbacks_ sem erro.
- [ ] Teste de importação concluído com sucesso.
- [ ] Documentação atualizada com a nova estrutura.
