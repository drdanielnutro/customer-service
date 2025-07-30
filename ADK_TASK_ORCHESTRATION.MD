# ADK_TASK_ORCHESTRATION.md

## ADK Migration Task Management System

This document provides specific guidance for Claude Code when orchestrating ADK migration tasks from `tasks.json`.

### 📋 Also See
- **CLAUDE.md**: General subagent orchestration guide
- **executor-codigo instructions**: Subagent execution details

## Overview

You are responsible for:
1. **Managing task state** (pending → in_progress → done/failed)
2. **Orchestrating the executor-codigo** subagent
3. **Tracking progress** and dependencies
4. **Reporting overall status**

## Task State Management

### States
- `pending`: Not started
- `in_progress`: Currently being executed by executor-codigo
- `done`: Successfully completed
- `failed`: Execution failed (may retry)
- `blocked`: Dependencies not met

### State Transition Rules
```
pending → in_progress → done
                     ↘ failed → pending (retry)
                     
pending → blocked (if dependencies not met)
blocked → pending (when dependencies complete)
```

## Orchestration Workflow

### 1. Initialize Task Tracking
```python
# Pseudo-code for your mental model
task_states = {
    1: {"status": "pending", "attempts": 0, "last_error": None},
    2: {"status": "pending", "attempts": 0, "last_error": None},
    # ... for all tasks in tasks.json
}
```

### 2. Task Selection Algorithm
1. **Check dependencies first**
   - Only select tasks where all dependencies have status "done"
   - Mark tasks with unmet dependencies as "blocked"

2. **Priority order**
   - High priority tasks first
   - Within same priority, use task ID order

3. **Skip conditions**
   - Status is "done"
   - Status is "in_progress" 
   - Status is "blocked"
   - Attempts >= 3 (mark as "failed" permanently)

### 3. Execution Protocol

```markdown
## For each selected task:

1. **Update state to "in_progress"**
   - Record timestamp
   - Increment attempt counter

2. **Prepare executor-codigo invocation**
   ```
   Use the executor-codigo agent to execute task {id}: {title}
   
   Task details:
   {full task JSON from tasks.json}
   ```

3. **Process executor response**
   - Parse the JSON response
   - Update task state based on response.status:
     - "success" → "done"
     - "failed" → "failed" (may retry if attempts < 3)
     - "partial" → "failed" (requires investigation)

4. **Record execution details**
   - Files modified
   - Issues found
   - Verification steps
```

## Progress Reporting

After each task execution, provide a status update:

```markdown
## ADK Migration Progress

**Overall**: {completed}/{total} tasks completed

### Recent Activity
✅ Task {id}: {title} - COMPLETED
   - Files modified: {list}
   - Verification: {method}

### Current Status
🔄 In Progress: {count}
✅ Completed: {count}
❌ Failed: {count}
🔒 Blocked: {count}
⏳ Pending: {count}

### Next Tasks
1. Task {id}: {title} (Priority: {priority})
2. Task {id}: {title} (Priority: {priority})
```

## Dependency Management

### Checking Dependencies
```python
def can_execute_task(task_id, task_states, tasks):
    task = tasks[task_id]
    dependencies = task.get("dependencies", [])
    
    for dep_id in dependencies:
        if task_states[dep_id]["status"] != "done":
            return False, f"Blocked by task {dep_id}"
    
    return True, "Ready"
```

### Common Dependency Patterns
- Task 1 (config.py) → Tasks 2-5 depend on it
- Task 2 (agent.py) → Most tool updates depend on it
- Task 6 (artifact_handler) → Task 7 documentation depends on it

## Error Handling

### When executor-codigo reports failure:

1. **Analyze the error**
   - File not found → Check if previous tasks created it
   - Content mismatch → May need manual inspection
   - Syntax error → Task instructions may be incomplete

2. **Retry logic**
   - Attempts < 3: Mark as "failed", will retry
   - Attempts >= 3: Mark as "failed" permanently, skip

3. **Report to user**
   ```markdown
   ⚠️ Task {id} failed: {error_summary}
   - Attempt: {current}/{max}
   - Issue: {specific_issue}
   - Suggestion: {what_user_should_do}
   ```

## Best Practices

### DO:
- ✅ Always update task state before and after execution
- ✅ Check dependencies before attempting execution
- ✅ Provide clear progress updates
- ✅ Include verification steps in reports
- ✅ Track which files were modified by each task

### DON'T:
- ❌ Execute tasks with unmet dependencies
- ❌ Retry more than 3 times
- ❌ Execute multiple tasks simultaneously
- ❌ Skip progress reporting
- ❌ Ignore executor-codigo error messages

## Quick Commands

### Start migration
```
"Execute ADK migration tasks from tasks.json"
```

### Check status
```
"Show ADK migration progress"
```

### Retry failed tasks
```
"Retry failed ADK tasks"
```

### Execute specific task
```
"Execute ADK task {id}"
```

## Integration with CLAUDE.md

This workflow integrates with the general orchestration patterns:

1. **You** (Claude Code) manage the overall workflow
2. **executor-codigo** executes individual tasks
3. **Other subagents** can be called for validation:
   - Use `adk-tool-compatibility-analyzer` after tool modifications
   - Use `gemini-api-compliance-auditor` after API changes
   - Use `validador-tasks-adk` before starting to validate feasibility

## State Persistence Note

Remember: You don't have persistent memory between conversations. When resuming:
1. Read tasks.json to see the task list
2. Check modified files to infer completed tasks
3. Ask user about current state if unclear
4. Resume from appropriate point

---

**Priority**: When user mentions "ADK migration tasks", "execute tasks from tasks.json", or similar, follow this orchestration protocol.