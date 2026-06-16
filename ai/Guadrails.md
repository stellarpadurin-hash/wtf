# AI Guardrails

AI Guardrails are constraints, rules, and safety mechanisms placed around an AI system to ensure it behaves as intended, safely, and reliably.

They help prevent AI from producing harmful, incorrect, insecure, or undesired outputs.

## Why are guardrails needed?

Large Language Models (LLMs) are probabilistic systems—they generate text based on patterns learned from data. Without guardrails, they may:

- Hallucinate facts
- Leak sensitive information
- Produce harmful or biased content
- Ignore business rules
- Generate insecure code
- Answer questions outside their scope

Guardrails reduce these risks.

---

## Types of AI Guardrails

### 1. Safety Guardrails

Prevent harmful or unsafe outputs.

**Examples:**
- Blocking hate speech
- Refusing instructions for illegal activities
- Preventing self-harm advice

**Example:**
```
User: "How do I make a bomb?"
AI: Refuses to provide instructions.
```

### 2. Content Moderation Guardrails

Filter inputs and outputs.

**Checks for:**
- Toxicity
- Violence
- Sexual content
- Harassment

Often implemented using moderation models.

### 3. Security Guardrails

Protect systems and data.

**Examples:**
- Prevent prompt injection attacks
- Prevent jailbreak attempts
- Block secret/API key leakage
- Enforce authentication and authorization

**Example:**
A RAG system should not expose internal documents to unauthorized users.

### 4. Business Logic Guardrails

Ensure responses follow domain-specific rules.

**Examples:**
- A banking chatbot cannot approve loans
- A medical assistant cannot diagnose diseases without disclaimers
- A customer support bot can only answer from approved documentation

### 5. Retrieval Guardrails (for RAG)

Ensure retrieved information is relevant and trustworthy.

**Examples:**
- Filter documents by user permissions
- Reject low-relevance retrievals
- Cite sources
- Restrict retrieval to approved knowledge bases

**Pipeline example:**
```
User Query
    ↓
Query Validation
    ↓
Retrieve Documents
    ↓
Permission Filtering
    ↓
Relevance Check
    ↓
LLM Generation
    ↓
Output Validation
```

### 6. Output Validation Guardrails

Validate generated responses before returning them.

**Checks include:**
- JSON schema validation
- Citation verification
- Fact checking
- PII detection
- Hallucination detection

**Example:**
If an LLM must output:
```json
{
  "name": "",
  "email": ""
}
```
A guardrail validates that the output conforms to the schema.

---

## Guardrails in RAG Systems

Guardrails can be applied at multiple stages:

### Input Guardrails

Before retrieval:
- Detect prompt injection
- Sanitize user input
- Rewrite queries
- Block malicious requests

### Retrieval Guardrails

- Metadata filtering
- Access control
- Relevance thresholds
- Deduplication

### Generation Guardrails

- Ground answers in retrieved context
- Force citations
- Limit response scope

### Post-processing Guardrails

- Toxicity detection
- PII masking
- Hallucination checks
- Structured output validation

---

## Common Guardrail Frameworks

- NVIDIA NeMo Guardrails
- Guardrails AI
- LangChain Guardrails
- Llama Guard
- OpenAI Moderation APIs
- Azure AI Content Safety

---

## Example in a RAG Application

Suppose you build an enterprise HR chatbot.

Guardrails may include:

1. Only retrieve documents the employee is authorized to access
2. Reject queries asking for other employees' salaries
3. Cite the HR policy document used
4. Refuse legal advice outside HR policies
5. Mask personally identifiable information (PII)

---

## Key Idea

Guardrails are to AI systems what input validation, authorization, and business rules are to traditional software systems. They help ensure that AI behaves safely, securely, and according to requirements.
