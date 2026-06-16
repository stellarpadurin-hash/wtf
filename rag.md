RAG (Retrieval-Augmented Generation) is an AI architecture that combines:

1. Retrieval — finding relevant information from an external knowledge source.


2. Generation — using a language model to produce an answer based on that retrieved information.



Instead of relying only on what the model learned during training, RAG allows the model to consult documents, databases, websites, or company knowledge before answering.

How RAG Works

A typical RAG pipeline looks like this:

User Question
      ↓
Retrieve Relevant Documents
      ↓
Provide Documents to LLM as Context
      ↓
Generate Answer
      ↓
Return Answer (often with citations)

For example:

Question: "What is our company's vacation policy?"

Without RAG:

The model may not know the policy.

It might guess or provide generic information.


With RAG:

The system searches the company's HR documents.

Retrieves the vacation policy.

Supplies the relevant passages to the model.

The model answers based on those documents.


Why Use RAG?

1. Access to Current Information

Models have a knowledge cutoff and cannot automatically know recent updates.

RAG can retrieve:

Latest documents

Current product information

Recent research papers

Live company knowledge


2. Reduced Hallucinations

The model is grounded in actual source material rather than generating solely from memory.

3. Private Knowledge

Organizations can use internal:

Wikis

PDFs

Databases

Support documentation


without retraining the model.

4. Easier Maintenance

Updating a document is often much simpler than retraining a large model.

Key Components

Document Store

The collection of knowledge to search.

Examples:

PDFs

Web pages

Knowledge bases

Databases


Embeddings

Documents are converted into numerical vectors that capture semantic meaning.

Example:

"What is RAG?"
      ↓
[0.12, -0.87, 0.45, ...]

Vector Database

Stores embeddings and enables similarity search.

Popular choices:

Pinecone

Weaviate

Qdrant

Milvus

Chroma


Retriever

Finds the most relevant documents for a query.

Generator (LLM)

Uses the retrieved documents plus the user query to generate the final response.

Example

Suppose a company has three documents:

Employee handbook

Security policy

Benefits guide


User asks:

> "Can I work remotely from another country?"



The retriever finds the relevant section of the employee handbook.

The LLM receives:

Question:
Can I work remotely from another country?

Retrieved Context:
Employees may work remotely outside their home country
for up to 30 days per calendar year with manager approval.

The LLM generates:

> "Yes. According to the employee handbook, employees may work remotely from another country for up to 30 days per calendar year with manager approval."



RAG vs Fine-Tuning

RAG	Fine-Tuning

Adds external knowledge	Changes model behavior
Easy to update	Requires retraining
Good for facts and documents	Good for style and task specialization
Can cite sources	Usually cannot cite sources
Lower cost to maintain	Higher maintenance cost


Many production systems use both:

Fine-tuning for behavior and formatting.

RAG for up-to-date knowledge.


Advanced RAG Techniques

Modern systems often add:

Query rewriting – improving the search query.

Hybrid search – combining keyword and vector search.

Re-ranking – selecting the best retrieved results.

Multi-step retrieval – retrieving information iteratively.

Agentic RAG – allowing an AI agent to decide what information to retrieve and when.


In one sentence: RAG is a method that enhances a language model by retrieving relevant external information and using it as context before generating an answer.