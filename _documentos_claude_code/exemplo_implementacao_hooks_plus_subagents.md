### Visão geral — o que vamos montar

Você terá **duas *sub-agents*** ( `task-creator` e `task-validator` ) e **um *hook* PostToolUse** que dispara automaticamente um *shell script* sempre que o `task-creator` rodar. O script:

1. **Detecta** que o sub-agent que acabou de rodar foi o `task-creator`;
2. **Valida** diretamente se a nova tarefa em `tasks.json` está coerente com `descricao_tarefas.md` (sem invocar outro subagente);
3. **Bloqueia ou libera** o fluxo de trabalho com base no resultado, devolvendo JSON ou exit‐codes conforme a especificação oficial.

> O gatilho 100 % determinístico vem do hook (não de prompts condicionais), pois *hooks* executam antes/depois de cada chamada de ferramenta conforme declarado na doc oficial.

---

## 1. Estrutura de diretórios mínima

```
my-project/
├─ descricao_tarefas.md
├─ tasks.json
└─ .claude/
   ├─ agents/
   │  ├─ task-creator.md
   │  └─ task-validator.md
   ├─ hooks/
   │  └─ validate-task.sh
   └─ settings.json
```

---

## 2. Conteúdo dos arquivos

### 2.1 `descricao_tarefas.md` (exemplo simplificado)

```markdown
# Backlog Nutro App

- [ ] TASK-001: Criar modelo Paciente (campos básicos)
- [ ] TASK-002: Implementar endpoint POST /pacientes
- [ ] TASK-003: Validar CPF e e-mail no cadastro
```

### 2.2 `tasks.json` (esquema inicial vazio)

```json
{
  "tasks": []
}
```

### 2.3 `agents/task-creator.md`

```markdown
---
name: task-creator
description: |
  Gera uma task ou subtask em tasks.json **usando PROATIVAMENTE** a próxima
  linha não marcada de descricao_tarefas.md. Depois de escrever, informe:
  "TASK <id> criada."
tools: Read, Write, Edit
---

Você é um gerador de tarefas. Leia `descricao_tarefas.md`, encontre a
primeira linha começando com "- [ ]", converta-a em objeto JSON compatível
com o esquema de `tasks.json` e grave usando o Write/Edit. Ao terminar,
**sempre** escreva a frase exata: `TASK <ID> criada.` (exemplo: TASK TASK-001 criada.)
```

### 2.4 `agents/task-validator.md`

```markdown
---
name: task-validator
description: |
  Valida que a tarefa recém-adicionada em tasks.json está coerente com a
  linha correspondente em descricao_tarefas.md. Use PROATIVAMENTE quando
  receber "TASK <id> criada." em contexto.
tools: Read
---

Você é um validador. Reabra ambos os arquivos, localize o item <ID> em cada
um e verifique:
1. O campo `title` em JSON coincide com o texto após "TASK-###:" no .md.
2. O status no .md foi alterado para "- [x]".
Devolva **apenas** "OK" ou "FALHA:<motivo>".
```

### 2.5 `.claude/hooks/validate-task.sh`

```bash
#!/usr/bin/env bash
# Hook para PostToolUse matcher=Task
# Valida tasks sem invocar subagentes (conforme documentação)
set -euo pipefail

read -r INPUT_JSON   # lê STDIN enviado pelo hook

# NOTA: O campo exato pode variar. Use 'claude --debug' para verificar.
# Possibilidades: tool_input.subagent_name, tool_input.task_name, etc.
SUBAGENT=$(jq -r '.tool_input.subagent_name // .tool_input.task_name // empty' <<<"$INPUT_JSON")

# Só reage a finalização do task-creator
if [[ "$SUBAGENT" != "task-creator" ]]; then
  exit 0            # nada a fazer para outros sub-agents
fi

# Validação direta dos arquivos (sem invocar outro subagente)
# Busca a última task adicionada em tasks.json
LAST_TASK=$(jq -r '.tasks[-1] // empty' "$CLAUDE_PROJECT_DIR/tasks.json" 2>/dev/null)
if [[ -z "$LAST_TASK" ]]; then
  echo "Nenhuma task encontrada em tasks.json" >&2
  exit 1
fi

# Extrai informações da última task
TASK_ID=$(jq -r '.id // empty' <<<"$LAST_TASK")
TASK_TITLE=$(jq -r '.title // empty' <<<"$LAST_TASK")

if [[ -z "$TASK_ID" ]] || [[ -z "$TASK_TITLE" ]]; then
  # Falha na estrutura → bloqueia com feedback
  jq -n '{ "decision":"block", "reason":"FALHA: Task mal formada - faltam campos id ou title" }'
  exit 0
fi

# Verifica se a task existe em descricao_tarefas.md
if grep -q "^- \[.\] $TASK_ID:" "$CLAUDE_PROJECT_DIR/descricao_tarefas.md"; then
  # Extrai o título do arquivo MD
  MD_LINE=$(grep "^- \[.\] $TASK_ID:" "$CLAUDE_PROJECT_DIR/descricao_tarefas.md")
  MD_TITLE=$(echo "$MD_LINE" | sed "s/^- \[.\] $TASK_ID: //")
  
  # Compara títulos
  if [[ "$TASK_TITLE" != "$MD_TITLE" ]]; then
    jq -n --arg id "$TASK_ID" --arg expected "$MD_TITLE" --arg actual "$TASK_TITLE" \
       '{ "decision":"block", "reason":("FALHA: Título da task " + $id + " não coincide. Esperado: \"" + $expected + "\", Atual: \"" + $actual + "\"") }'
    exit 0
  fi
  
  # Verifica se foi marcada como concluída
  if ! grep -q "^- \[x\] $TASK_ID:" "$CLAUDE_PROJECT_DIR/descricao_tarefas.md"; then
    jq -n --arg id "$TASK_ID" \
       '{ "decision":"block", "reason":("FALHA: Task " + $id + " não foi marcada como concluída em descricao_tarefas.md") }'
    exit 0
  fi
  
  # Tudo OK
  exit 0
else
  # Task não encontrada no MD
  jq -n --arg id "$TASK_ID" \
     '{ "decision":"block", "reason":("FALHA: Task " + $id + " não encontrada em descricao_tarefas.md") }'
  exit 0
fi
```

> Notes
>
> * O script recebe via STDIN o payload `PostToolUse` (estrutura oficial).
> * **IMPORTANTE**: O campo que identifica o subagente pode variar entre versões. Use `claude --debug` para verificar o payload real. Possíveis campos incluem:
>   - `tool_input.subagent_name`
>   - `tool_input.task_name`
>   - Outros campos específicos da versão
> * O script já tenta múltiplos campos como fallback, mas você deve confirmar qual é usado em sua versão.
> * Devolver JSON com `"decision":"block"` em `PostToolUse` faz Claude reconsiderar a saída anterior.

Torne o script executável:

```bash
chmod +x .claude/hooks/validate-task.sh
```

### 2.6 `.claude/settings.json`

```jsonc
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Task",            // cobre todas as chamadas de sub-agent
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/validate-task.sh",
            "timeout": 30             // opcional
          }
        ]
      }
    ]
  }
}
```

A sintaxe segue o esquema de configuração oficial de hooks.
Usamos `Task` como *matcher* porque é o nome do tool invocado por qualquer sub-agent.

---

## 3. Fluxo completo em tempo de execução

```
┌───────────────┐
│  Usuário/LLM  │  →  chama task-creator
└───────────────┘
          │        (gera TASK-001, imprime "TASK TASK-001 criada.")
          ▼
    Claude Code  dispara PostToolUse (tool=Task)
          │
          ▼
     validate-task.sh  ← matcher "Task"
          │
          │-- se subagent ≠ task-creator → exit 0
          │
          ├─ se task-creator:
          │     • valida diretamente os arquivos
          │     • determina "OK" ou "FALHA: …"
          │
          ├─ "OK" → exit 0 (Claude continua)
          │
          └─ "FALHA" → imprime JSON {"decision":"block", …}
                       (Claude vê o motivo, pede ajuste ao task-creator)
```

Quando tudo passa, você simplesmente manda novamente:

```
> Use the task-creator sub agent to continuar criando tarefas
```

e o ciclo prossegue até esgotar o backlog.

---

## 4. Recomendações e boas práticas

1. **Inspecione primeiro o payload real** com `claude --debug` para confirmar o
   campo que identifica o sub-agent (algumas versões usam `task_name`).
2. **Teste o script em modo isolado:**
   `cat sample-posttool.json | .claude/hooks/validate-task.sh`
3. **Logs** – acrescente `echo` para registrar em `~/.claude/task-flow.log`.
4. **Timeouts** – mantenha moderados; hooks bloqueados travam a conversa.
5. **Segurança** – scripts rodam com suas permissões locais; reveja riscos.

---

### Pronto!

Com esses arquivos você possui **uma orquestração real, determinística e repetível** entre dois sub-agents sem precisar de `if` dentro dos prompts. Se quiser aprofundar em filtragem de eventos, consulte a seção **Hook Input/Output** e os exemplos adicionais no guia oficial de hooks.
