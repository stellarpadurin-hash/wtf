Chunking is one of the most important parts of a RAG system because retrieval quality depends heavily on how documents are split.

Why chunk at all?

Large language models have context limits, and retrieval works best on smaller pieces of text.

Consider this document:

Employee Handbook (100 pages)

Chapter 1: Company Overview
Chapter 2: Vacation Policy
Chapter 3: Remote Work Policy
Chapter 4: Benefits
...

If you embed the entire handbook as one vector, a question about remote work gets diluted by all the unrelated content.

Instead, you split the document into smaller chunks and embed each chunk separately.


---

Simple Fixed-Size Chunking

The most basic approach is to split text every N characters or tokens.

Example:

Chunk 1: Tokens 1-500
Chunk 2: Tokens 501-1000
Chunk 3: Tokens 1001-1500

Python example:

chunk_size = 500

chunks = [
    text[i:i+chunk_size]
    for i in range(0, len(text), chunk_size)
]

Pros

Easy

Fast


Cons

Can cut sentences in half

Loses context


Example:

Chunk 1:
Employees may work remotely...

Chunk 2:
...outside their home country for 30 days.

The meaning is split across chunks.


---

Chunking with Overlap

A common improvement is overlapping chunks.

Instead of:

1-500
501-1000

Use:

1-500
401-900
801-1300

Notice the overlap.

Example:

Chunk 1:
Employees may work remotely from another country

Chunk 2:
work remotely from another country for up to 30 days

Now important information isn't lost at boundaries.

Typical settings:

Chunk size: 500 tokens
Overlap: 50-100 tokens


---

Sentence-Based Chunking

Split by sentences while respecting a size limit.

Example:

Document:

Employees may work remotely.
Manager approval is required.
The limit is 30 days annually.

Chunk:

Employees may work remotely.
Manager approval is required.
The limit is 30 days annually.

instead of cutting in the middle of a sentence.

This usually performs better than fixed character splitting.


---

Paragraph-Based Chunking

For structured documents:

Heading
Paragraph 1

Paragraph 2

Heading
Paragraph 3

You can keep paragraphs together.

Example:

Remote Work Policy

Employees may work remotely outside their
home country for up to 30 days...

This preserves semantic meaning.


---

Semantic Chunking

More advanced systems use AI to identify topic changes.

Example:

Remote Work Policy
...
...
Benefits Policy
...
...
Security Requirements
...
...

The chunker detects topic boundaries and creates chunks accordingly.

Result:

Chunk A = Remote Work section
Chunk B = Benefits section
Chunk C = Security section

This often gives better retrieval because each chunk contains a single topic.


---

Structure-Aware Chunking

For PDFs, Word docs, HTML, Markdown, etc., you can use document structure.

Example Markdown:

# Employee Handbook

## Vacation Policy
...

## Remote Work Policy
...

## Benefits
...

Chunking can follow headers:

Chunk 1 = Vacation Policy section
Chunk 2 = Remote Work Policy section
Chunk 3 = Benefits section

Many modern RAG systems prefer this approach because it preserves meaning and hierarchy.


---

What Gets Stored?

Suppose this chunk is created:

Remote Work Policy

Employees may work remotely outside
their home country for up to 30 days
per year with manager approval.

The vector database stores something like:

{
  "chunk_id": "123",
  "text": "Employees may work remotely...",
  "embedding": [0.12, -0.33, ...],
  "metadata": {
      "document": "Employee Handbook",
      "section": "Remote Work Policy",
      "page": 27
  }
}

The embedding is used for search, while the text and metadata are returned when a match is found.


---

Common Chunk Sizes

There is no universal best size, but typical ranges are:

Content Type	Chunk Size

FAQs	100–300 tokens
Policies	300–800 tokens
Technical docs	500–1,000 tokens
Books	800–1,500 tokens


A common starting point is:

Chunk Size: 500 tokens
Overlap: 50 tokens


---

What do production RAG systems use?

Many modern systems use a combination of:

1. Structure-aware chunking (headers, sections)


2. Semantic chunking (topic boundaries)


3. Overlap between chunks


4. Metadata preservation



This usually outperforms simple fixed-size chunking because the retriever gets chunks that represent complete ideas rather than arbitrary slices of text.