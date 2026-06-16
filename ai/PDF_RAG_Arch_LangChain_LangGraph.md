Here’s a **production-grade PDF RAG architecture** showing **both LangChain + LangGraph together**, tailored to your style (structured, actionable, architect-level).

***

# 🧠 1. High-Level Architecture

```
                    ┌──────────────────────────┐
                    │      User Question       │
                    └────────────┬─────────────┘
                                 │
                         (LangGraph Orchestration)
                                 │
         ┌───────────────────────┼────────────────────────┐
         │                       │                        │
   Query Rewrite Node     Retrieval Node           Decision Node
         │                       │                        │
         │              (LangChain RAG)                 ↓
         │                       │                Need Tools?
         │                       │               /          \
         │                       │            Yes            No
         │                       │             ↓              ↓
         │                 Context + Docs  Tool Node     Answer Node
         │                       │             │              │
         └──────────────→ Synthesis Node ←────┘──────────────┘
                                │
                        Final Answer + Citations
```

***

# 🏗️ 2. Component Breakdown

## 🔷 A. Ingestion Pipeline (Offline)

**Use LangChain**

```
PDF → Loader → Chunking → Embeddings → Vector DB
```

### Stack

| Component  | Choice (your preference aligned) |
| ---------- | -------------------------------- |
| Loader     | PyPDFLoader                      |
| Chunking   | RecursiveCharacterTextSplitter   |
| Embeddings | OpenAI / open-source             |
| Vector DB  | FAISS (portable ✅)               |
| Metadata   | file\_name, page\_no, chunk\_id  |

***

### Chunking Strategy (Important)

```
Chunk size: 500–800 tokens
Overlap: 50–100
Metadata:
{
  "source": "file1.pdf",
  "page": 3,
  "chunk_id": "file1_p3_c2"
}
```

✅ Aligns with your requirement:

* citations only from chunk used
* source = filename only

***

***

# ⚙️ 3. Retrieval + Generation Layer

## 🔶 LangChain Role (Inside Nodes)

LangChain handles:

* Retriever
* Embeddings
* Prompt templates
* Output parsing

***

### Example LangChain RAG Chain

```python
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

def retrieve_docs(query):
    docs = retriever.get_relevant_documents(query)
    return docs
```

***

### Prompt Template

```text
Answer using ONLY the context provided.
If not found, say "I don't know".

Context:
{context}

Question:
{question}

Answer with citations using format:
[filename - chunk_id]
```

***

***

# 🧠 4. LangGraph Orchestration Layer (Core Value)

This is where **enterprise-grade control comes in**.

***

## 🔷 State Definition

```python
class State(TypedDict):
    question: str
    rewritten_query: str
    retrieved_chunks: list
    answer: str
    citations: list
```

***

## 🔷 Nodes Design

### 1. Query Rewrite Node (Optional but powerful)

```
User query → optimized search query
```

✅ Handles:

* vague queries
* context expansion

***

### 2. Retrieval Node (LangChain inside)

```python
def retrieval_node(state):
    docs = retriever.invoke(state["rewritten_query"])
    return {"retrieved_chunks": docs}
```

***

### 3. Decision Node

Determines:

```
Sufficient context OR need external tool?
```

Example logic:

```python
if len(state["retrieved_chunks"]) == 0:
    → fallback / tool
else:
    → answer
```

***

### 4. Answer Generation Node

Uses LangChain LLM:

```python
def answer_node(state):
    context = format_chunks(state["retrieved_chunks"])
    response = llm.invoke({
        "context": context,
        "question": state["question"]
    })
    return {"answer": response}
```

***

### 5. Citation Extraction Node

✅ Matches your requirement exactly:

* Only chunks used
* Only filename shown

```python
def extract_sources(chunks):
    return list(set([
        f"{c.metadata['source']} - {c.metadata['chunk_id']}"
        for c in chunks
    ]))
```

***

***

# 🔁 5. Graph Flow (LangGraph)

```
START
  ↓
Query Rewrite
  ↓
Retrieval
  ↓
Decision
  ├── Insufficient → (optional retry / tool)
  └── Sufficient
         ↓
     Answer Generation
         ↓
     Citation Node
         ↓
END
```

***

## ✅ Optional Advanced Loop (Agentic RAG)

```
Answer not confident?
   ↓
Refine Query → Retrieve Again → Answer
```

✅ This loop is **native in LangGraph**

***

***

# 🧩 6. Reference Implementation Skeleton

```python
from langgraph.graph import StateGraph

builder = StateGraph(State)

builder.add_node("rewrite", rewrite_node)
builder.add_node("retrieve", retrieval_node)
builder.add_node("answer", answer_node)

builder.set_entry_point("rewrite")

builder.add_edge("rewrite", "retrieve")
builder.add_edge("retrieve", "answer")

graph = builder.compile()
```

***

***

# 📊 7. LangChain vs LangGraph Role (Clear Separation)

| Layer           | Tool      | Responsibility             |
| --------------- | --------- | -------------------------- |
| Orchestration   | LangGraph | Flow, state, control       |
| LLM interaction | LangChain | prompts, LLM calls         |
| Retrieval       | LangChain | embeddings + vector search |
| Storage         | FAISS     | document retrieval         |

***

***

# 🎯 8. Advanced Features (Enterprise-Grade Enhancements)

## 🔷 A. Multi-Document Scaling

* Namespace per document
* Metadata filtering

***

## 🔷 B. Hybrid Retrieval

```
Vector search + keyword (BM25)
```

***

## 🔷 C. Reranking

```
Top 10 → rerank → top 3
```

***

## 🔷 D. Guardrails

* hallucination detection
* "answer only from context" enforcement

***

## 🔷 E. Observability

* LangSmith tracing
* Node-level debugging (LangGraph strength ✅)

***

## 🔷 F. Human-in-loop (LangGraph)

```
Low confidence → escalate to human
```

***

***

# ⚠️ 9. Architect Pitfalls (Based on real systems)

### ❌ Mistake 1: Using only LangChain for complex flows

→ Leads to unmaintainable agent logic

***

### ❌ Mistake 2: No state tracking

→ leads to:

* duplicate retrievals
* inconsistent answers

***

### ❌ Mistake 3: Poor chunking

→ bad citations + hallucination

***

### ❌ Mistake 4: No retry loop

→ low answer quality

***

***

# ✅ 10. Final Architecture Summary

## ✅ Clean Separation

```
LangGraph → Brain (workflow engine)
LangChain → Hands (executes LLM + retrieval)
FAISS → Memory
```

***

## ✅ Your Requirements Mapping

| Requirement        | Solution         |
| ------------------ | ---------------- |
| PDF docs           | PyPDFLoader      |
| Citations          | chunk metadata   |
| Show only filename | metadata filter  |
| Only used chunks   | post-processing  |
| Scalable docs      | FAISS + metadata |

***

***
