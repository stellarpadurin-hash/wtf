import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Load your Google API key securely
load_dotenv()

# 2. INGESTION: Load all text files from the local directory
print("Loading documents...")
loader = DirectoryLoader("./my_documents", glob="*.txt", loader_cls=TextLoader)
raw_documents = loader.load()

# 3. SPLIT: Chop the documents into smaller text chunks
print("Splitting documents into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # Max characters per chunk
    chunk_overlap=50      # Keep a tiny bit of context overlap between chunks
)
chunks = text_splitter.split_documents(raw_documents)

# 4. EMBED & STORE: Turn chunks into numbers and save them to a local DB
print("Creating vector embeddings and saving to local database...")
embeddings = GoogleGenAIEmbeddings(model="models/text-embedding-004")

# This creates a folder called 'chroma_db' locally to save the data index
vector_store = Chroma.from_documents(
    documents=chunks, 
    embedding=embeddings, 
    persist_directory="./chroma_db"
)

# 5. RETRIEVAL: Setup the database to act as a search engine
# 'k=3' means find the top 3 most relevant text chunks matching the question
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# 6. GENERATION: Build the RAG Prompt and Chain
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

rag_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Answer the question based ONLY on the provided context below. 
If you do not know the answer based on the context, say "I cannot find that information in your files."

Context:
{context}

Question: 
{question}
""")

# A helper function to format retrieved documents into one block of text
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 7. ASK A QUESTION
query = "What is the coffee machine code and when can I work remotely?"

print(f"\nSearching database for: '{query}'...")
retrieved_docs = retriever.invoke(query)
formatted_context = format_docs(retrieved_docs)

# Run the chain manually
chain = rag_prompt | llm | StrOutputParser()
response = chain.invoke({"context": formatted_context, "question": query})

print("\n--- AI ANSWER ---")
print(response)
