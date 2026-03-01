---
name: parallel-agents
description: Run multiple subagents in parallel to verify concurrent execution works correctly. Use this skill whenever you need to verify parallel agent execution, test that subagents can run concurrently, benchmark parallel vs sequential performance, or when the user asks "can you run agents in parallel", "test parallel execution", "verify subagent concurrency", or "run multiple agents at once".
---

# Parallel Agents Verification

Verify that the subagent tool can dispatch and run multiple agents concurrently, collecting their independent results.

## How It Works

The `subagent` tool (from the subagent extension) supports three modes:
- **Single**: one agent, one task
- **Parallel**: multiple agents run concurrently (up to 8 tasks, 4 concurrent)
- **Chain**: sequential agents where each gets the previous output

This skill focuses on the **parallel** mode to confirm that:
1. Multiple agents are dispatched simultaneously
2. Each agent completes its task independently
3. Results are collected from all agents
4. The wall-clock time is less than the sum of individual times (proving concurrency)

## Verification Steps

1. **Dispatch parallel tasks** using the `subagent` tool with the `tasks` array parameter. Use lightweight agents (like `scout` or `worker`) with small, fast tasks that each produce a distinct, verifiable output.

2. **Check results**: Confirm that all tasks completed successfully and each returned its expected output.

3. **Report**: Summarize which agents ran, what they produced, and whether parallelism was confirmed.

## Example Usage

Use the subagent tool in parallel mode:

```
subagent({
  tasks: [
    { agent: "worker", task: "Create a file /tmp/parallel-test-1.txt containing exactly 'AGENT_1_DONE'" },
    { agent: "worker", task: "Create a file /tmp/parallel-test-2.txt containing exactly 'AGENT_2_DONE'" },
    { agent: "worker", task: "Create a file /tmp/parallel-test-3.txt containing exactly 'AGENT_3_DONE'" }
  ]
})
```

Then verify the files exist and contain the expected content.

## Success Criteria

- All parallel tasks complete without errors
- Each agent produces the correct, distinct output
- No interference between concurrent agents (each file has only its own content)
