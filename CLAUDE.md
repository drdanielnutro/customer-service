# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## SUBAGENT ORCHESTRATION SYSTEM

You have access to specialized subagents in `.claude/agents/` designed for specific tasks. Use them proactively based on context.

### Available Subagents

#### 1. 📊 **project-data-architect** (Blue)
**Purpose**: Convert unstructured task lists into structured JSON
**Use when**:
- Converting meeting notes to tasks.json
- Structuring chaotic documentation
- Creating task management systems
- Organizing project requirements

**Example invocation**:
```
Use the project-data-architect agent to convert ERROS_MIGRACAO_DETALHADOS.md into tasks.json
```

#### 2. ✅ **tutorial-tasks-validator** (Green)
**Purpose**: Deep consistency verification between tutorials and tasks.json
**Use when**:
- Validating tutorial-to-tasks conversions
- After project-data-architect creates tasks.json
- Verifying no information was lost in conversion
- Need detailed omission analysis
- Require both human-readable and machine-processable reports

**Example invocation**:
```
Use the tutorial-tasks-validator agent to verify tasks.json matches ERROS_MIGRACAO_DETALHADOS.md
```

#### 3. 🔧 **executor-codigo** (Orange)
**Purpose**: Execute precise Python code modifications
**Use when**:
- Need to modify function signatures (make async, change parameters)
- Replace deprecated API calls
- Add/remove specific lines of code
- Create new Python files with exact specifications
- User says "modify function X", "replace API Y", "make async"

**Example invocation**:
```
Use the executor-codigo agent to make the analyze_image function async and replace session.get_artifact with tool_context.load_artifact
```

#### 4. 📚 **adk-docs-expert-projeto** (Green)
**Purpose**: Query official Google ADK documentation
**Use when**:
- Need ADK installation instructions
- Looking for ADK API references
- Troubleshooting ADK-specific errors
- Understanding ADK best practices
- Migration guidance to ADK

**Example invocation**:
```
Use the adk-docs-expert-projeto agent to find how to install ADK on macOS
```

#### 5. 🔍 **adk-tool-compatibility-analyzer** (Purple)
**Purpose**: Verify compatibility between mock and real ADK tool implementations
**Use when**:
- Implemented a real version of an ADK tool
- Need to verify function signatures match
- Checking artifact usage compliance
- Validating Gemini model appropriateness

**Example invocation**:
```
Use the adk-tool-compatibility-analyzer agent to verify compatibility of transcrever_audio_real.py with the mock version
```

#### 6. 🏷️ **validador-tasks-adk** (Yellow)
**Purpose**: Technical validation of tasks for ADK migration
**Use when**:
- Validating proposed implementations against ADK/Gemini APIs
- Checking method signatures and class structures
- Generating conformity reports
- Ensuring ADK compliance before implementation

**Example invocation**:
```
Use the validador-tasks-adk agent to validate if the proposed task implementations conform to ADK APIs
```

#### 7. 🔵 **gemini-api-compliance-auditor** (Blue)
**Purpose**: Verify Gemini API call compliance
**Use when**:
- User implemented Gemini API calls
- Debugging API integration issues
- Need parameter-by-parameter validation
- Verifying response structure compliance

**Example invocation**:
```
Use the gemini-api-compliance-auditor agent to check if my model.generate_content call is correct
```

#### 8. 🌐 **web-researcher**
**Purpose**: Search the web for current information
**Use when**:
- Questions require up-to-date information
- Need to research external documentation
- Looking for recent updates or news
- Any query that benefits from web search

**Example invocation**:
```
Use the web-researcher agent to find the latest Gemini API updates
```

#### 9. 🎭 **sub-agent-architect** (Yellow)
**Purpose**: Design and create new subagents
**Use when**:
- Need to create specialized subagents
- Translating workflow requirements into agent configurations
- Crafting specialized system prompts
- Expanding automation capabilities

**Example invocation**:
```
Use the sub-agent-architect agent to design a code review subagent
```

#### Additional Agents (Available via Task tool)

#### 🪝 **claude-code-hooks-expert**
**Purpose**: Create and configure Claude Code hooks
**Use when**:
- Setting up automation workflows
- Implementing validation rules
- Configuring tool restrictions
- Creating deterministic workflows

**Example invocation**:
```
Use the claude-code-hooks-expert agent to create validation hooks for file edits
```

## ORCHESTRATION PATTERNS

### Pattern 1: Create → Validate
Always validate after creation:
```
1. project-data-architect → creates tasks.json
2. tutorial-tasks-validator → validates completeness
```

### Pattern 2: Design → Implement → Execute
For code modifications:
```
1. validador-tasks-adk → validate implementation plan
2. executor-codigo → execute code modifications
3. adk-tool-compatibility-analyzer → verify compatibility
```

### Pattern 3: Research → Design → Implement
For new workflows:
```
1. web-researcher or adk-docs-expert-projeto → gather information
2. sub-agent-architect → design subagent
3. claude-code-hooks-expert → implement hooks for automation
```

### Pattern 4: Document → Structure → Verify
For project organization:
```
1. Analyze unstructured documentation
2. project-data-architect → create structured data
3. tutorial-tasks-validator → ensure accuracy
```

## DECISION MATRIX

| User Intent                      | Primary Agent                   | Follow-up Agent                 |
| -------------------------------- | ------------------------------- | ------------------------------- |
| "Convert this document to tasks" | project-data-architect          | tutorial-tasks-validator        |
| "Validate tutorial conversion"   | tutorial-tasks-validator        | -                               |
| "Modify Python function"         | executor-codigo                 | adk-tool-compatibility-analyzer |
| "Make function async"            | executor-codigo                 | -                               |
| "Replace deprecated API"         | executor-codigo                 | gemini-api-compliance-auditor   |
| "How to install ADK?"            | adk-docs-expert-projeto         | -                               |
| "Check ADK tool compatibility"   | adk-tool-compatibility-analyzer | -                               |
| "Validate ADK migration tasks"   | validador-tasks-adk             | executor-codigo                 |
| "Verify Gemini API call"         | gemini-api-compliance-auditor   | -                               |
| "Find latest API updates"        | web-researcher                  | -                               |
| "Create a workflow for X"        | sub-agent-architect             | claude-code-hooks-expert        |
| "Automate this process"          | claude-code-hooks-expert        | -                               |
| "Design a new agent"             | sub-agent-architect             | -                               |

## VALIDATION PROTOCOLS

### After project-data-architect:
1. **Always** run tutorial-tasks-validator
2. Check for 100% coverage
3. Verify technical details preserved
4. Ensure schema compliance

### After executor-codigo:
1. Run adk-tool-compatibility-analyzer if ADK tools involved
2. Run gemini-api-compliance-auditor if Gemini API calls modified
3. Verify code still runs without errors
4. Check that only requested changes were made

### After creating hooks/subagents:
1. Test in isolated environment
2. Verify expected behavior
3. Document usage
4. Check for edge cases

## CONTEXT PASSING

When chaining subagents, provide clear context:

```
First, I'll use project-data-architect to structure your tasks.
[Run project-data-architect]

Now I'll validate the output using tutorial-tasks-validator to ensure completeness.
[Run tutorial-tasks-validator with reference to source document]

Finally, I'll use executor-codigo to implement the first task.
[Run executor-codigo with specific task details]
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
- User mentions "make async" or "modify function" → Suggest executor-codigo
- User asks about ADK → Suggest adk-docs-expert-projeto
- User implements ADK tools → Suggest adk-tool-compatibility-analyzer
- User wants automation → Suggest claude-code-hooks-expert
- Tasks.json was created → Automatically use tutorial-tasks-validator
- User needs custom workflow → Suggest sub-agent-architect

## HOOK INTEGRATION

For deterministic workflows, combine hooks with subagents:

1. Configure PostToolUse hooks to trigger after specific subagents
2. Use exit codes and JSON output for flow control
3. Remember: hooks cannot invoke other subagents directly
4. Use hooks for validation and automation

## BEST PRACTICES

1. **Always validate outputs** - Never trust subagent output without verification
2. **Chain intelligently** - Use subagents in logical sequences
3. **Document workflows** - Explain which subagents you're using and why
4. **Handle errors gracefully** - Have fallback plans
5. **Preserve context** - Pass relevant information between subagents
6. **Use executor-codigo for precision** - When exact code modifications are needed
7. **Research before implementing** - Use web-researcher or adk-docs-expert first

## QUICK REFERENCE

```bash
# Convert document to tasks
"Use project-data-architect to analyze [document] and create tasks.json"

# Validate tasks
"Use tutorial-tasks-validator to verify tasks.json against [source]"

# Execute code modifications
"Use executor-codigo to [make function async|replace API|add lines|create file]"

# Research ADK
"Use adk-docs-expert-projeto to find [ADK topic]"

# Check compatibility
"Use adk-tool-compatibility-analyzer to verify [implementation] compatibility"

# Validate ADK tasks
"Use validador-tasks-adk to validate tasks against ADK APIs"

# Audit API calls
"Use gemini-api-compliance-auditor to verify [API call]"

# Web research
"Use web-researcher to find [current information]"

# Create subagent
"Use sub-agent-architect to design an agent for [purpose]"

# Setup hooks
"Use claude-code-hooks-expert to create hooks for [automation need]"
```

Remember: Subagents are tools for specific jobs. Use them proactively when their purpose matches the user's needs.

---

## SPECIALIZED WORKFLOWS

### ADK Migration Tasks
For managing ADK migration tasks with state tracking and dependencies:
- See: **ADK_TASK_ORCHESTRATION.md**
- Primary agent: executor-codigo
- Use when: Executing tasks from tasks.json with status management

### Quick Reference
```bash
# Start ADK migration
"Execute ADK migration tasks from tasks.json"
# Follow ADK_TASK_ORCHESTRATION.md protocol

# Check migration status  
"Show ADK migration progress"
# Reports based on task states
```

---
---