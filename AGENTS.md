# AGENTS.md

## 1. Missão
- Fazer backup completo da pasta `customer-service` antes de qualquer outra ação.
- Refatorar os arquivos do diretório `customer-service/customer_service` seguindo as instruções em `tasks.json`.
- Garantir que cada passo seja registrado e validado para facilitar o acompanhamento.

## 2. Escopo
- **Origem do código:** `customer-service/customer_service`  
- **Ignorar:** quaisquer pastas fora de `customer-service`, como `assets`, logs antigos etc.  
- **Configuração prévia:**  
  - Garantir que o Python 3.10+ esteja instalado.  
  - Criar e ativar um ambiente virtual (venv/virtualenv).  
  - Verificar existência do backup antes de começar.

## 3. Fluxo de Execução de Tarefas
1. **Carregar** o arquivo `tasks.json`.  
2. **Iterar** sobre cada `task` e suas `subtasks`, na ordem em que aparecem.  
3. Para **cada** item:
   - Ao **iniciar**, atualizar `"status"` de `"pending"` para `"in progress"`.  
   - Executar o script ou comando Python correspondente à refatoração.  
   - Ao **concluir**, atualizar `"status"` para `"done"`.

## 4. Revisão de Modularização
- Após todas as tarefas, revisar cada arquivo original para confirmar que a lógica foi corretamente dividida em módulos.  
- Verificar imports, estrutura de pacotes e nomes de funções/classes para garantir consistência.

## 5. Prepare o Push Request para o Github
- Deixe a branch preparada para fazermos o "push" para o github, após todas as etapas terem sido concluídas.