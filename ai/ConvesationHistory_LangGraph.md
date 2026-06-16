**Short answer:**

> ❌ **No — you do NOT pass full conversation history manually in every request when using LangGraph with persistence.**  
> ✅ **LangGraph automatically restores conversation history from checkpoints based on `thread_id`.**

***

# 🧠 1. How It Actually Works

## ✅ With LangGraph Persistence Enabled

When you use a checkpointer:

```python
graph = builder.compile(checkpointer=checkpointer)
```

and invoke:

```python
graph.invoke(
  {"question": "What is policy A?"},
  config={"configurable": {"thread_id": "user-123"}}
)
```

👉 LangGraph does this internally:

```
1. Load latest checkpoint for thread_id = user-123
2. Rehydrate full graph state (including history)
3. Merge with new input (your new question)
4. Execute nodes
5. Save new checkpoint
```

✅ So:

> **Conversation history is NOT passed manually — it is automatically loaded from persistence.**

This is because LangGraph stores **thread-scoped state in checkpoints** that can be reused across invocations. [\[github.com\]](https://github.com/langchain-ai/langchain/issues/789)

***

# 🔄 2. Compare With Traditional LangChain

## ❌ LangChain (classic pattern)

You manually do:

```python
history = load_history(session_id)

chain.invoke({
  "messages": history + [new_question]
})

save_history(session_id, updated_history)
```

👉 You **pass history every time**

***

## ✅ LangGraph

You just pass:

```python
{"question": "..."}
```

👉 LangGraph **retrieves history automatically**

***

# 🧩 3. What Gets Restored Automatically?

From checkpoint:

* ✅ messages (conversation history)
* ✅ previous answers
* ✅ retrieved documents (if stored in state)
* ✅ tool outputs
* ✅ control flags / intermediate data

Because:

> checkpoints store the **entire graph state snapshot per thread** [\[dev.to\]](https://dev.to/blizzerand/vector-search-code-embeddings-building-a-smart-knowledge-base-with-langchain-and-faiss-m48)

***

# ⚙️ 4. Important: You Must Use thread\_id

This is critical.

```python
config = {
  "configurable": {
    "thread_id": "user-123"
  }
}
```

### Behavior

| thread\_id   | Effect               |
| ------------ | -------------------- |
| same         | resumes conversation |
| different    | new conversation     |
| not provided | stateless execution  |

👉 `thread_id` = **conversation identity**

***

# 🔍 5. When DOES history get passed?

## ✅ Case 1: No persistence (MemorySaver or None)

Then:

* state exists only in memory
* you may need to pass state explicitly if you re-create graph each time

***

## ✅ Case 2: You choose to override

Example:

```python
graph.invoke({
  "messages": [...custom history...]
})
```

👉 This **overrides** checkpoint state

***

## ✅ Case 3: Stateless APIs

If you’re not using checkpointer:

```python
graph = builder.compile()  # no persistence
```

👉 Then:

* no history is retained
* must pass everything every time

***

# 🧠 6. Key Mental Model (Very Important)

## LangChain thinking:

```
You manage history
You pass history
You persist history
```

## LangGraph thinking:

```
State lives in the graph
Graph restores state
You just send incremental input
```

***

# 🏗️ 7. Internal Flow (Step-by-Step)

Let’s trace 2 calls:

***

### 🟢 First Request

```python
question = "What is policy A?"
thread_id = "user-123"
```

Flow:

```
No checkpoint exists
→ Start fresh state
→ Run graph
→ Save checkpoint #1
```

***

### 🟢 Second Request

```python
question = "How does it apply to claims?"
thread_id = "user-123"
```

Flow:

```
Load checkpoint #1
→ state contains previous conversation
→ append new question
→ run graph
→ save checkpoint #2
```

***

✅ You never manually passed history

***

# ⚠️ 8. Common Mistakes

## ❌ Mistake 1: Passing history manually AND using persistence

```python
graph.invoke({
  "messages": history  # unnecessary
})
```

👉 Leads to:

* duplication
* inconsistent state

***

## ❌ Mistake 2: Forgetting thread\_id

```python
graph.invoke({"question": "..."})
```

👉 Result:

* new conversation every call
* no memory

***

## ❌ Mistake 3: Thinking LangGraph stores only messages

👉 It stores **entire state**, not just chat history

***

# 🧩 9. In Your PDF RAG System

## ✅ With LangGraph

Each request:

```python
graph.invoke(
  {"question": "..."},
  config={"thread_id": "user-123"}
)
```

Internally:

```
→ previous Q&A retrieved
→ retrieved docs (if persisted) reused
→ reasoning continues
```

***

## ✅ What you DON'T pass

* chat history ❌
* previous answers ❌
* retrieved chunks ❌

***

## ✅ What you DO pass

* new user input ✅

***

# 🎯 10. Final Answer

> ✅ **No, you do not pass conversation history in every request when using LangGraph with persistence.**  
> ✅ **LangGraph automatically loads and maintains history using checkpoints tied to a `thread_id`.**  
> ⚠️ You only pass incremental input (e.g., the latest question), not the entire conversation.

***

# 🚀 TL;DR

```
LangChain → pass history every time
LangGraph → history auto-loaded via thread_id
```

***
