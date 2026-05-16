# 3. SPLIT: Chop the documents into smaller text chunks
print("Splitting documents into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       
    chunk_overlap=50      
)
raw_chunks = text_splitter.split_documents(raw_documents)

# --- ADD THIS FILTERING STEP TO FIX THE ERROR ---
# This ensures we only keep chunks that actually contain readable text
chunks = [chunk for chunk in raw_chunks if chunk.page_content.strip()]
print(f"Filtered out empty chunks. Going from {len(raw_chunks)} to {len(chunks)} valid chunks.")
# ------------------------------------------------

# 4. EMBED & STORE: Turn chunks into numbers and save them to a local DB
print("Creating vector embeddings and saving to local database...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

vector_store = Chroma.from_documents(
    documents=chunks, # This now points to our clean, filtered list
    embedding=embeddings, 
    persist_directory="./chroma_db"
)
