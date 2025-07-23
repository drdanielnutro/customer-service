{
  "tasks": [
    {
      "id": 1,
      "title": "Backup do projeto",
      "description": "Criar uma cópia completa do diretório customer-service antes de qualquer alteração.",
      "status": "pending",
      "dependencies": [],
      "priority": "high",
      "details": "Usar cp -r para gerar backup em customer-service.bak.",
      "testStrategy": "Verificar se o diretório backup foi criado com sucesso."
    },
    {
      "id": 2,
      "title": "Mapeamento da estrutura atual",
      "description": "Analisar os arquivos originais e registrar números de linhas e dependências.",
      "status": "pending",
      "dependencies": [1],
      "priority": "high",
      "details": "Executar wc -l e grep conforme instruções do AGENTS.md.",
      "testStrategy": "Resultados gravados em arquivo de mapeamento."
    },
    {
      "id": 3,
      "title": "Criar diretórios base",
      "description": "Gerar estrutura vazia para tools/ e shared_libraries/callbacks/ conforme modelo proposto.",
      "status": "pending",
      "dependencies": [2],
      "priority": "high",
      "details": "Incluir subpastas para cada ferramenta e callback.",
      "testStrategy": "Conferir com comando find se pastas foram criadas."
    },
    {
      "id": 4,
      "title": "Copiar módulos monolíticos",
      "description": "Copiar arquivos tools.py e callbacks.py para as novas localizações como base para extração.",
      "status": "pending",
      "dependencies": [3],
      "priority": "high",
      "details": "Mantém versão original para referência durante refatoração.",
      "testStrategy": "Abrir novos arquivos e confirmar que conteúdo foi copiado."
    },
    {
      "id": 5,
      "title": "Extrair funções de ferramentas",
      "description": "Mover cada função do antigo tools.py para seu próprio módulo.",
      "status": "pending",
      "dependencies": [4],
      "priority": "high",
      "details": "Criar um pacote por função dentro de tools/ com __init__.py e arquivo da função.",
      "testStrategy": "Importar cada função individualmente a partir do novo pacote.",
      "subtasks": [
        {"id": 1, "title": "send_call_companion_link", "description": "Extrair função send_call_companion_link.", "dependencies": [], "details": "Criar pasta tools/send_call_companion_link e mover implementação.", "status": "pending", "parentTaskId": 5},
        {"id": 2, "title": "approve_discount", "description": "Extrair função approve_discount.", "dependencies": [1], "details": "Criar pasta tools/approve_discount.", "status": "pending", "parentTaskId": 5},
        {"id": 3, "title": "sync_ask_for_approval", "description": "Extrair função sync_ask_for_approval.", "dependencies": [2], "details": "Criar pasta tools/sync_ask_for_approval.", "status": "pending", "parentTaskId": 5},
        {"id": 4, "title": "update_salesforce_crm", "description": "Extrair função update_salesforce_crm.", "dependencies": [3], "details": "Criar pasta tools/update_salesforce_crm.", "status": "pending", "parentTaskId": 5},
        {"id": 5, "title": "access_cart_information", "description": "Extrair função access_cart_information.", "dependencies": [4], "details": "Criar pasta tools/access_cart_information.", "status": "pending", "parentTaskId": 5},
        {"id": 6, "title": "modify_cart", "description": "Extrair função modify_cart.", "dependencies": [5], "details": "Criar pasta tools/modify_cart.", "status": "pending", "parentTaskId": 5},
        {"id": 7, "title": "get_product_recommendations", "description": "Extrair função get_product_recommendations.", "dependencies": [6], "details": "Criar pasta tools/get_product_recommendations.", "status": "pending", "parentTaskId": 5},
        {"id": 8, "title": "check_product_availability", "description": "Extrair função check_product_availability.", "dependencies": [7], "details": "Criar pasta tools/check_product_availability.", "status": "pending", "parentTaskId": 5},
        {"id": 9, "title": "schedule_planting_service", "description": "Extrair função schedule_planting_service.", "dependencies": [8], "details": "Criar pasta tools/schedule_planting_service.", "status": "pending", "parentTaskId": 5},
        {"id": 10, "title": "get_available_planting_times", "description": "Extrair função get_available_planting_times.", "dependencies": [9], "details": "Criar pasta tools/get_available_planting_times.", "status": "pending", "parentTaskId": 5},
        {"id": 11, "title": "send_care_instructions", "description": "Extrair função send_care_instructions.", "dependencies": [10], "details": "Criar pasta tools/send_care_instructions.", "status": "pending", "parentTaskId": 5},
        {"id": 12, "title": "generate_qr_code", "description": "Extrair função generate_qr_code.", "dependencies": [11], "details": "Criar pasta tools/generate_qr_code.", "status": "pending", "parentTaskId": 5}
      ]
    },
    {
      "id": 6,
      "title": "Extrair callbacks",
      "description": "Separar cada callback do arquivo callbacks.py em módulos individuais.",
      "status": "pending",
      "dependencies": [4],
      "priority": "high",
      "details": "Criar arquivos separados dentro de shared_libraries/callbacks/",
      "testStrategy": "Importar callbacks individualmente após a extração.",
      "subtasks": [
        {"id": 1, "title": "rate_limit_callback", "description": "Extrair rate_limit_callback.", "dependencies": [], "details": "Criar rate_limit_callback.py.", "status": "pending", "parentTaskId": 6},
        {"id": 2, "title": "validate_customer_id", "description": "Extrair validate_customer_id.", "dependencies": [1], "details": "Criar validate_customer_id_callback.py.", "status": "pending", "parentTaskId": 6},
        {"id": 3, "title": "lowercase_value", "description": "Extrair lowercase_value.", "dependencies": [2], "details": "Criar lowercase_value.py.", "status": "pending", "parentTaskId": 6},
        {"id": 4, "title": "before_tool", "description": "Extrair before_tool.", "dependencies": [3], "details": "Criar before_tool_callback.py.", "status": "pending", "parentTaskId": 6},
        {"id": 5, "title": "after_tool", "description": "Extrair after_tool.", "dependencies": [4], "details": "Criar after_tool_callback.py.", "status": "pending", "parentTaskId": 6},
        {"id": 6, "title": "before_agent", "description": "Extrair before_agent.", "dependencies": [5], "details": "Criar before_agent_callback.py.", "status": "pending", "parentTaskId": 6}
      ]
    },
    {
      "id": 7,
      "title": "Ajustar exports dos pacotes",
      "description": "Atualizar __init__.py em tools/ e callbacks/ para exportar corretamente as funções.",
      "status": "pending",
      "dependencies": [5,6],
      "priority": "high",
      "details": "Adicionar from .<modulo> import <funcao> em cada __init__.py",
      "testStrategy": "Importar pacote e verificar disponibilidade das funções."
    },
    {
      "id": 8,
      "title": "Atualizar agent.py",
      "description": "Modificar imports no arquivo principal para refletir a nova estrutura modular.",
      "status": "pending",
      "dependencies": [7],
      "priority": "high",
      "details": "Substituir imports antigos de tools e callbacks pelos novos caminhos.",
      "testStrategy": "Executar lint ou import manual para garantir que não há erros."
    },
    {
      "id": 9,
      "title": "Testar importação do agente",
      "description": "Executar python -c 'from customer_service import root_agent' e garantir que não ocorrem exceções.",
      "status": "pending",
      "dependencies": [8],
      "priority": "high",
      "details": "Usar ambiente uv conforme documentação.",
      "testStrategy": "Saída sem erros confirma sucesso do refactor."
    },
    {
      "id": 10,
      "title": "Atualizar README",
      "description": "Documentar a nova árvore de diretórios e instruções de importação.",
      "status": "pending",
      "dependencies": [9],
      "priority": "medium",
      "details": "Adicionar seção com tree da estrutura modular.",
      "testStrategy": "Revisar markdown e verificar links e exemplos."
    },
    {
      "id": 11,
      "title": "Revisão de modularização",
      "description": "Conferir se todos os arquivos originais foram devidamente divididos e removidos das versões monolíticas.",
      "status": "pending",
      "dependencies": [9],
      "priority": "medium",
      "details": "Comparar conteúdo dos novos módulos com os originais.",
      "testStrategy": "Examinar cada pasta e confirmar ausência de código residual." 
    },
    {
      "id": 12,
      "title": "Gerar log final",
      "description": "Criar arquivo de log na raiz do projeto explicando todas as etapas realizadas na refatoração.",
      "status": "pending",
      "dependencies": [10,11],
      "priority": "medium",
      "details": "Log deve listar ações executadas e data/hora.",
      "testStrategy": "Abrir log e verificar presença das descrições de cada tarefa."
    }
  ],
  "metadata": {
    "projectName": "customer-service",
    "totalTasks": 12,
    "sourceFile": "tasks.md",
    "generatedAt": "2025-07-22T14:29:32Z"
  }
}
