# 4. EMBED & STORE: Turn chunks into numbers and save them to a local DB
print("Creating vector embeddings and saving to local database...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Extract raw strings and metadata manually out of the chunk objects
texts = [chunk.page_content for chunk in chunks]
metadatas = [chunk.metadata for chunk in chunks]

# Use from_texts instead of from_documents to completely bypass the internal indexing bug
vector_store = Chroma.from_texts(
    texts=texts,
    embedding=embeddings,
    metadatas=metadatas,
    persist_directory="./chroma_db"
)
print("Database successfully created!")
