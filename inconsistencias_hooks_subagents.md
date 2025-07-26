# Inconsistências entre a implementação sugerida e a documentação

## 1. Formato do campo `name` dos subagentes
A documentação de sub agents exige que o identificador use apenas letras minúsculas e hífens:
```
| `name`        | Yes      | Unique identifier using lowercase letters and hyphens |
```
Fonte: `_documentos_claude_code/subagents_on_claude_code.md` linhas 104‑110.

No exemplo, os arquivos `task_creator.md` e `task_validator.md` definem:
```
name: task_creator
```
(undeline: `task_creator`), e o mesmo para `task_validator`.
Isso viola a regra de usar hífens.
**Correção sugerida:** renomear para `task-creator` e `task-validator`, ajustando todas as referências a esses nomes.

## 2. Invocação de subagente em hook
O arquivo `CLAUDE.md` instrui que hooks não devem chamar outros subagentes diretamente:
```
3. Remember: hooks cannot invoke other subagents directly
```
Fonte: `CLAUDE.md` linhas 154‑161.

Entretanto `validate-task.sh` usa o comando:
```
VALIDATION=$(claude "Use the task_validator sub agent to validar última tarefa")
```
(linhas 102‑103 do exemplo). Isso chama um subagente a partir do hook, contrariando a recomendação.
**Correção sugerida:** mover a validação para um script autônomo (bash ou Python) sem usar subagente, ou executar o `task-validator` fora do hook no fluxo principal.

## 3. Campo `subagent_name` não documentado
O script assume que `tool_input` contém `subagent_name`:
```
SUBAGENT=$(jq -r '.tool_input.subagent_name // empty' <<<"$INPUT_JSON")
```
(linhas 94‑95 do exemplo). Porém a referência de hooks não define esse campo para `PostToolUse`.
**Correção sugerida:** inspecionar o payload real com `claude --debug` para confirmar qual chave é enviada (`subagent_name`, `task_name` ou outra) e ajustar o script conforme a versão da ferramenta.
