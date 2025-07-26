# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## SUBAGENT ORCHESTRATION SYSTEM

You have access to specialized subagents in `.claude/agents/` designed for specific tasks. Use them proactively based on context.

### Available Subagents

#### 1. 🏗️ **adk-migration-executor** (Yellow)
**Purpose**: Systematic migration of ADK project structures
**Use when**:
- Migrating code between ADK projects
- Creating new projects based on existing structures
- Transplanting business logic while maintaining patterns

**Example invocation**:
```
Use the adk-migration-executor agent to migrate customer-service to professor-virtual
```

#### 2. 📊 **project-data-architect** (Blue)
**Purpose**: Convert unstructured task lists into structured JSON
**Use when**:
- Converting meeting notes to tasks.json
- Structuring chaotic documentation
- Creating task management systems

**Example invocation**:
```
Use the project-data-architect agent to convert ERROS_MIGRACAO_DETALHADOS.md into tasks.json
```

#### 3. ✅ **tutorial-tasks-validator** (Red)
**Purpose**: Validate completeness of tasks.json against source documents
**Use when**:
- After project-data-architect creates tasks.json
- Verifying no information was lost in conversion
- Quality assurance of task lists

**Example invocation**:
```
Use the tutorial-tasks-validator agent to verify tasks.json matches ERROS_MIGRACAO_DETALHADOS.md
```

#### 4. 🪝 **claude-code-hooks-expert** (Available via Task tool)
**Purpose**: Create and configure Claude Code hooks
**Use when**:
- Setting up automation workflows
- Implementing validation rules
- Configuring tool restrictions

#### 5. 🎭 **claude-subagent-architect** (Available via Task tool)
**Purpose**: Design and create new subagents
**Use when**:
- Need to create specialized subagents
- Translating workflow requirements into agent configurations
- Crafting specialized system prompts

## ORCHESTRATION PATTERNS

### Pattern 1: Create → Validate
Always validate after creation:
```
1. project-data-architect → creates tasks.json
2. tutorial-tasks-validator → validates completeness
```

### Pattern 2: Migrate → Verify
For code migrations:
```
1. adk-migration-executor → performs migration
2. Manual verification of migrated files
3. Create tasks.json for any issues found
```

### Pattern 3: Design → Implement
For new workflows:
```
1. claude-subagent-architect → design subagent
2. claude-code-hooks-expert → implement hooks for automation
```

## DECISION MATRIX

| User Intent                      | Primary Agent             | Follow-up Agent          |
| -------------------------------- | ------------------------- | ------------------------ |
| "Convert this document to tasks" | project-data-architect    | tutorial-tasks-validator |
| "Migrate this project"           | adk-migration-executor    | -                        |
| "Create a workflow for X"        | claude-subagent-architect | claude-code-hooks-expert |
| "Validate this tasks.json"       | tutorial-tasks-validator  | -                        |
| "Automate this process"          | claude-code-hooks-expert  | -                        |

## VALIDATION PROTOCOLS

### After project-data-architect:
1. **Always** run tutorial-tasks-validator
2. Check for 100% coverage
3. Verify technical details preserved

### After adk-migration-executor:
1. List created files
2. Spot-check migrated content
3. Run tests if available

### After creating hooks/subagents:
1. Test in isolated environment
2. Verify expected behavior
3. Document usage

## CONTEXT PASSING

When chaining subagents, provide clear context:

```
First, I'll use project-data-architect to structure your tasks.
[Run project-data-architect]

Now I'll validate the output using tutorial-tasks-validator to ensure completeness.
[Run tutorial-tasks-validator with reference to source document]
```

## ERROR HANDLING

If a subagent fails:
1. Capture the error message
2. Determine if it's a data issue or agent issue
3. Fix data issues, then retry
4. For agent issues, fall back to manual approach

## PROACTIVE SUGGESTIONS

Based on user actions, suggest appropriate subagents:

- User provides error document → Suggest project-data-architect
- User mentions migration → Suggest adk-migration-executor
- User wants automation → Suggest claude-code-hooks-expert
- Tasks.json was created → Automatically use tutorial-tasks-validator

## HOOK INTEGRATION

For deterministic workflows, combine hooks with subagents:

1. Configure PostToolUse hooks to trigger after specific subagents
2. Use exit codes and JSON output for flow control
3. Remember: hooks cannot invoke other subagents directly

## BEST PRACTICES

1. **Always validate outputs** - Never trust subagent output without verification
2. **Chain intelligently** - Use subagents in logical sequences
3. **Document workflows** - Explain which subagents you're using and why
4. **Handle errors gracefully** - Have fallback plans
5. **Preserve context** - Pass relevant information between subagents

## QUICK REFERENCE

```bash
# Convert document to tasks
"Use project-data-architect to analyze [document] and create tasks.json"

# Validate tasks
"Use tutorial-tasks-validator to verify tasks.json against [source]"

# Migrate project
"Use adk-migration-executor to migrate [source] to [target]"

# Create subagent
"Use claude-subagent-architect to design an agent for [purpose]"

# Setup hooks
"Use claude-code-hooks-expert to create hooks for [automation need]"
```

Remember: Subagents are tools for specific jobs. Use them proactively when their purpose matches the user's needs.