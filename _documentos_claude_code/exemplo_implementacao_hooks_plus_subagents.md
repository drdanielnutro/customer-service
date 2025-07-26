### Visão geral — o que vamos montar

Você terá **duas *sub-agents*** ( `task_creator` e `task_validator` ) e **um *hook* PostToolUse** que dispara automaticamente um *shell script* sempre que o `task_creator` rodar. O script:

1. **Detecta** que o sub-agent que acabou de rodar foi o `task_creator`;
2. **Invoca** o `task_validator` via CLI para conferir se a nova tarefa em `tasks.json` está coerente com `descricao_tarefas.md`;
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
   │  ├─ task_creator.md
   │  └─ task_validator.md
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

### 2.3 `agents/task_creator.md`

```markdown
---
name: task_creator
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

### 2.4 `agents/task_validator.md`

```markdown
---
name: task_validator
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
set -euo pipefail

read -r INPUT_JSON   # lê STDIN enviado pelo hook
SUBAGENT=$(jq -r '.tool_input.subagent_name // empty' <<<"$INPUT_JSON")

# Só reage a finalização do task_creator
if [[ "$SUBAGENT" != "task_creator" ]]; then
  exit 0            # nada a fazer para outros sub-agents
fi

# Invoca o validador e captura stdout
VALIDATION=$(claude "Use the task_validator sub agent to validar última tarefa")

if [[ "$VALIDATION" =~ ^OK ]]; then
  # Tudo certo – permite sequência normal
  exit 0
else
  # Algo falhou → bloqueia e devolve feedback automatizado p/ Claude
  jq -n --arg msg "$VALIDATION" \
     '{ "decision":"block", "reason":$msg }'
  exit 0            # JSON já foi impresso; Claude recebe e tenta corrigir
fi
```

> Notes
>
> * O script recebe via STDIN o payload `PostToolUse` (estrutura oficial).
> * A chave `subagent_name` costuma aparecer em `tool_input` dos *Task* calls (use `claude --debug` num teste para confirmar o campo exato).
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
│  Usuário/LLM  │  →  chama task_creator
└───────────────┘
          │        (gera TASK-001, imprime "TASK TASK-001 criada.")
          ▼
    Claude Code  dispara PostToolUse (tool=Task)
          │
          ▼
     validate-task.sh  ← matcher "Task"
          │
          │-- se subagent ≠ task_creator → exit 0
          │
          ├─ se task_creator:
          │     • chama task_validator
          │     • recebe "OK" ou "FALHA: …"
          │
          ├─ "OK" → exit 0 (Claude continua)
          │
          └─ "FALHA" → imprime JSON {"decision":"block", …}
                       (Claude vê o motivo, pede ajuste ao task_creator)
```

Quando tudo passa, você simplesmente manda novamente:

```
> Use the task_creator sub agent to continuar criando tarefas
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
