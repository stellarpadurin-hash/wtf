Absolutely — below is a **full runnable Python example** for a **PDF RAG system using both LangGraph and LangChain**.

This design uses:

* **LangChain** for **PDF loading, chunking, embeddings, FAISS vector storage, and LLM calls** — which matches LangChain’s modular retrieval building blocks (loaders → splitters → embeddings → vector store → retrieval). [\[reference....gchain.com\]](https://reference.langchain.com/python/langchain-community/document_loaders/pdf/PyPDFLoader), [\[docs.langchain.com\]](https://docs.langchain.com/oss/python/langchain/retrieval)
* **LangGraph** for **workflow orchestration** using a **state graph with nodes, edges, and compiled execution**. [\[reference....gchain.com\]](https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_node), [\[pypi.org\]](https://pypi.org/project/langgraph/)

I’m also aligning this with your earlier preference:

* **PDF input**
* **FAISS/local storage**
* **citations / sources**
* **show only file names in Sources**
* **sources derived from chunks actually passed into answer generation**

***

# What this example does

## Offline / indexing flow

1. Read all PDFs from `./pdfs`
2. Split into chunks
3. Add metadata:
   * `file_name`
   * `page`
   * `chunk_id`
4. Create embeddings
5. Store in local **FAISS**

## Runtime / question-answer flow

1. Rewrite query (optional but useful)
2. Retrieve top chunks
3. Decide whether enough context exists
4. Generate grounded answer
5. Return:
   * answer
   * sources section with **file names only**

***

# Install packages

```bash
pip install -U \
  langgraph \
  langchain-openai \
  langchain-community \
  langchain-text-splitters \
  faiss-cpu \
  pypdf \
  python-dotenv \
  pydantic
```

> `PyPDFLoader` is the standard LangChain loader for PDF files and supports page-based extraction with metadata. [\[reference....gchain.com\]](https://reference.langchain.com/python/langchain-community/document_loaders/pdf/PyPDFLoader)

***

# Expected folder structure

```text
your-project/
├─ pdfs/
│  ├─ doc1.pdf
│  ├─ doc2.pdf
│  └─ ...
├─ faiss_index/              # created automatically
├─ .env
└─ pdf_rag_langgraph.py
```

***

# `.env` file

```env
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

***

# Full code: `pdf_rag_langgraph.py`

```python
import os
import argparse
from pathlib import Path
from typing import List, TypedDict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


# ============================================================
# Configuration
# ============================================================

load_dotenv()

PDF_DIR = Path("./pdfs")
INDEX_DIR = Path("./faiss_index")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
TOP_K = 6
MAX_CONTEXT_DOCS = 4


# ============================================================
# LLM + Embeddings
# ============================================================

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0
    )


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=OPENAI_EMBEDDING_MODEL
    )


# ============================================================
# Indexing / Ingestion
# ============================================================

def load_pdf_pages(pdf_path: Path) -> List"""
    Load a single PDF as page-level Documents.
    """
    loader = PyPDFLoader(str(pdf_path), mode="page")
    pages = loader.load()

    normalized_pages = []
    for page_doc in pages:
        metadata = dict(page_doc.metadata or {})
        page_no = metadata.get("page", 0)

        page_doc.metadata = {
            **metadata,
            "source": str(pdf_path),
            "file_name": pdf_path.name,
            "page": int(page_no) + 1,  # convert to 1-based page numbering
        }
        normalized_pages.append(page_doc)

    return normalized_pages


def split_pages_into_chunks(pages: List[Document]) -> List"""
    Split page-level docs into chunks and preserve metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    all_chunks: List[Document] = []

    for page_doc in pages:
        page_chunks = splitter.split_documents([page_doc])

        for i, chunk in enumerate(page_chunks, start=1):
            file_name = chunk.metadata.get("file_name", "unknown.pdf")
            page = chunk.metadata.get("page", 0)
            stem = Path(file_name).stem

            chunk.metadata["chunk_id"] = f"{stem}_p{page}_c{i}"
            all_chunks.append(chunk)

    return all_chunks


def ingest_pdfs(pdf_dir: Path) -> List"""
    Read all PDFs from a folder and return chunked documents.
    """
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {pdf_dir.resolve()}. "
            f"Please place one or more PDFs in the folder."
        )

    all_chunks: List[Document] = []

    for pdf_file in pdf_files:
        pages = load_pdf_pages(pdf_file)
        chunks = split_pages_into_chunks(pages)
        all_chunks.extend(chunks)

    return all_chunks


def build_faiss_index(force_rebuild: bool = False) -> FAISS:
    """
    Build or load a FAISS index locally.
    """
    embeddings = get_embeddings()

    index_exists = (INDEX_DIR / "index.faiss").exists() and (INDEX_DIR / "index.pkl").exists()

    if index_exists and not force_rebuild:
        print(f"[INFO] Loading existing FAISS index from {INDEX_DIR.resolve()}")
        vectorstore = FAISS.load_local(
            str(INDEX_DIR),
            embeddings,
            allow_dangerous_deserialization=True
        )
        return vectorstore

    print(f"[INFO] Building FAISS index from PDFs in {PDF_DIR.resolve()}")
    chunks = ingest_pdfs(PDF_DIR)

    print(f"[INFO] Total chunks created: {len(chunks)}")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))

    print(f"[INFO] FAISS index saved to {INDEX_DIR.resolve()}")
    return vectorstore


# ============================================================
# Graph State
# ============================================================

class GraphState(TypedDict, total=False):
    question: str
    rewritten_query: str
    retrieved_docs: List[Document]
    selected_docs: List[Document]
    answer: str
    sources: List[str]
    final_response: str


# ============================================================
# Structured output model
# ============================================================

class AnswerPayload(BaseModel):
    answer: str = Field(
        description="Final grounded answer to the user's question."
    )
    used_chunk_ids: List[str] = Field(
        default_factory=list,
        description="List of chunk_ids actually used in the answer."
    )


# ============================================================
# Prompt helpers
# ============================================================

def build_context(docs: List[Document]) -> str:
    """
    Build the context string supplied to the answering model.
    Each chunk contains metadata so the model can refer to chunk IDs.
    """
    parts = []

    for doc in docs:
        chunk_id = doc.metadata.get("chunk_id", "unknown_chunk")
        file_name = doc.metadata.get("file_name", "unknown.pdf")
        page = doc.metadata.get("page", "?")
        text = doc.page_content.strip()

        part = (
            f"[CHUNK_ID: {chunk_id}]\n"
            f"[FILE_NAME: {file_name}]\n"
            f"[PAGE: {page}]\n"
            f"{text}"
        )
        parts.append(part)

    return "\n\n--------------------\n\n".join(parts)


# ============================================================
# Graph Nodes
# ============================================================

def make_rewrite_node(llm: ChatOpenAI):
    rewrite_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You rewrite user questions into concise search-friendly queries for document retrieval. "
                "Preserve the original meaning. Return only the rewritten query."
            ),
            ("human", "{question}")
        ]
    )

    def rewrite_query(state: GraphState) -> dict:
        question = state["question"].strip()

        # If the question is already simple, you could skip rewriting.
        # Here we always rewrite for consistency.
        response = llm.invoke(rewrite_prompt.format_messages(question=question))
        rewritten = (response.content or "").strip()

        if not rewritten:
            rewritten = question

        return {"rewritten_query": rewritten}

    return rewrite_query


def make_retrieve_node(vectorstore: FAISS):
    def retrieve(state: GraphState) -> dict:
        query = state.get("rewritten_query") or state["question"]

        # FAISS can return documents with scores.
        # Lower score generally means closer match for similarity distance.
        docs_and_scores = vectorstore.similarity_search_with_score(query, k=TOP_K)

        retrieved_docs: List[Document] = []
        for doc, score in docs_and_scores:
            doc.metadata["retrieval_score"] = float(score)
            retrieved_docs.append(doc)

        return {"retrieved_docs": retrieved_docs}

    return retrieve


def select_context(state: GraphState) -> dict:
    """
    Select a smaller number of chunks to pass into the LLM.
    These are the chunks considered 'used by the system' for answer generation.
    """
    docs = state.get("retrieved_docs", [])

    # Basic top-N selection.
    # You can replace this with reranking later.
    selected_docs = docs[:MAX_CONTEXT_DOCS]

    return {"selected_docs": selected_docs}


def route_after_selection(state: GraphState) -> str:
    docs = state.get("selected_docs", [])
    if docs:
        return "answer"
    return "no_answer"


def make_answer_node(llm: ChatOpenAI):
    structured_llm = llm.with_structured_output(AnswerPayload)

    answer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a grounded PDF question-answering assistant.\n"
                "Use ONLY the provided context.\n"
                "If the answer is not present in the context, say exactly: I don't know.\n\n"
                "You must also identify which CHUNK_ID values were used in your answer.\n"
                "Return a structured response with:\n"
                "- answer\n"
                "- used_chunk_ids\n\n"
                "Important rules:\n"
                "1. Do not use outside knowledge.\n"
                "2. Prefer concise, accurate answers.\n"
                "3. If multiple chunks support the answer, include all corresponding chunk IDs.\n"
                "4. If no answer is found, answer 'I don't know.' and return an empty used_chunk_ids list."
            ),
            (
                "human",
                "Question:\n{question}\n\n"
                "Context:\n{context}"
            )
        ]
    )

    def answer(state: GraphState) -> dict:
        docs = state.get("selected_docs", [])
        if not docs:
            return {
                "answer": "I don't know.",
                "sources": []
            }

        context = build_context(docs)
        question = state["question"]

        payload: AnswerPayload = structured_llm.invoke(
            answer_prompt.format_messages(question=question, context=context)
        )

        used_chunk_ids = set(payload.used_chunk_ids or [])

        # If the model doesn't return chunk IDs, fall back to all selected docs
        if not used_chunk_ids:
            used_docs = docs
        else:
            used_docs = [
                d for d in docs
                if d.metadata.get("chunk_id") in used_chunk_ids
            ]
            if not used_docs:
                used_docs = docs

        # Show only file names in Sources
        sources = sorted({
            d.metadata.get("file_name", "unknown.pdf")
            for d in used_docs
        })

        return {
            "answer": payload.answer.strip(),
            "sources": sources
        }

    return answer


def no_answer_node(state: GraphState) -> dict:
    return {
        "answer": "I don't know.",
        "sources": []
    }


def finalize(state: GraphState) -> dict:
    answer = state.get("answer", "").strip()
    sources = state.get("sources", [])

    final_response = answer

    if sources:
        final_response += "\n\nSources:\n"
        for src in sources:
            final_response += f"- {src}\n"

    return {"final_response": final_response.strip()}


# ============================================================
# Graph Builder
# ============================================================

def build_graph(vectorstore: FAISS):
    llm = get_llm()

    builder = StateGraph(GraphState)

    builder.add_node("rewrite_query", make_rewrite_node(llm))
    builder.add_node("retrieve", make_retrieve_node(vectorstore))
    builder.add_node("select_context", select_context)
    builder.add_node("answer", make_answer_node(llm))
    builder.add_node("no_answer", no_answer_node)
    builder.add_node("finalize", finalize)

    builder.add_edge(START, "rewrite_query")
    builder.add_edge("rewrite_query", "retrieve")
    builder.add_edge("retrieve", "select_context")

    builder.add_conditional_edges(
        "select_context",
        route_after_selection,
        {
            "answer": "answer",
            "no_answer": "no_answer"
        }
    )

    builder.add_edge("answer", "finalize")
    builder.add_edge("no_answer", "finalize")
    builder.add_edge("finalize", END)

    # In-memory checkpointing for demo purposes.
    # Replace with persistent checkpointing for production.
    graph = builder.compile(checkpointer=MemorySaver())
    return graph


# ============================================================
# CLI
# ============================================================

def run_index(force_rebuild: bool):
    build_faiss_index(force_rebuild=force_rebuild)


def run_ask(question: str):
    vectorstore = build_faiss_index(force_rebuild=False)
    graph = build_graph(vectorstore)

    result = graph.invoke(
        {"question": question},
        config={"configurable": {"thread_id": "pdf-rag-demo"}}
    )

    print("\n" + "=" * 80)
    print(result["final_response"])
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="PDF RAG using LangGraph + LangChain")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Build or rebuild the FAISS index")
    index_parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild the index even if it already exists"
    )

    ask_parser = subparsers.add_parser("ask", help="Ask a question against indexed PDFs")
    ask_parser.add_argument(
        "--question",
        required=True,
        help="Question to ask"
    )

    args = parser.parse_args()

    if args.command == "index":
        run_index(force_rebuild=args.force)
    elif args.command == "ask":
        run_ask(args.question)


if __name__ == "__main__":
    main()
```

***

# How to run

## 1) Put PDFs into `./pdfs`

Example:

```text
pdfs/
├─ architecture-guide.pdf
├─ claims-policy.pdf
└─ onboarding-manual.pdf
```

## 2) Build the index

```bash
python pdf_rag_langgraph.py index --force
```

## 3) Ask a question

```bash
python pdf_rag_langgraph.py ask --question "What is the claims approval workflow?"
```

***

# Example output

```text
The claims approval workflow begins with intake validation, followed by eligibility checks and policy rule evaluation. If the request passes all checks, it is routed for adjudication and final approval. Exceptions are escalated to manual review.

Sources:
- claims-policy.pdf
- architecture-guide.pdf
```

***

# Why this code is architecturally clean

## LangChain responsibilities

This example uses LangChain for the retrieval pipeline building blocks:

* `PyPDFLoader`
* `RecursiveCharacterTextSplitter`
* `OpenAIEmbeddings`
* `FAISS`
* `ChatOpenAI` [\[reference....gchain.com\]](https://reference.langchain.com/python/langchain-community/document_loaders/pdf/PyPDFLoader), [\[docs.langchain.com\]](https://docs.langchain.com/oss/python/langchain/retrieval)

## LangGraph responsibilities

This example uses LangGraph for:

* explicit workflow nodes
* state propagation
* conditional routing
* compiled execution/checkpointing [\[reference....gchain.com\]](https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_node), [\[pypi.org\]](https://pypi.org/project/langgraph/)

That separation is usually the **cleanest production mental model**:

* **LangChain = components**
* **LangGraph = orchestration**

***

# Important implementation notes

## 1) “Sources show only file names”

Done here:

```python
sources = sorted({
    d.metadata.get("file_name", "unknown.pdf")
    for d in used_docs
})
```

So the final `Sources:` section shows **only** file names.

***

## 2) “Sources should come from chunks actually used”

This code gets closer to that than a basic RAG implementation by asking the model to return the `used_chunk_ids`, then mapping those chunk IDs back to source file names.

That means:

* the model sees chunk IDs in context
* it returns which chunk IDs it used
* the app converts that to **file names only**

This is stronger than simply listing all retrieved documents.

***

## 3) Why I used explicit retrieval code instead of helper chains

LangChain’s retrieval stack is modular and the ecosystem has evolved quickly; using explicit Python with retriever/vector store + prompt + model is usually the most maintainable approach for production examples, while the retrieval documentation still presents the modular loader/splitter/embedding/vector-store pattern as the foundation. [\[docs.langchain.com\]](https://docs.langchain.com/oss/python/langchain/retrieval), [\[reference....gchain.com\]](https://reference.langchain.com/python/langchain-classic/chains/combine_documents/stuff/create_stuff_documents_chain)

***

# Production upgrades I’d recommend next

Given your architect preference, here’s the practical upgrade path:

## A. Add reranking

Right now it uses top-N vector similarity.  
Upgrade:

* retrieve top 10
* rerank to top 3 or 4
* answer only from reranked chunks

## B. Add metadata filters

Useful when PDFs grow:

* by document type
* by business domain
* by date/version

## C. Add citations inline

You asked earlier for file-name-only sources, but if you later want **inline references**, you could render:

```text
The claim flow starts with intake validation [claims-policy.pdf].
```

## D. Replace `MemorySaver` with persistent checkpoints

For long-running enterprise workflows, use persistent checkpointing instead of in-memory.

## E. Add a fallback “I don’t know” threshold

You can reject low-quality retrieval if similarity distance is too weak.

***

# Minimal variant if you want less complexity

If you want, I can also give you one of these next:

1. **Simpler version**
   * no query rewrite
   * no structured output
   * 80 lines shorter

2. **Production version**
   * reranker
   * streaming
   * FastAPI endpoint
   * citations in JSON response
   * observability hooks

3. **UI version**
   * Streamlit / React frontend
   * upload PDFs
   * ask questions interactively

***

