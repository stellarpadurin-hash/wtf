import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# 1. Load Environment Variables securely
load_dotenv()

# Define the URL you want to summarize
target_url = "https://example.com/some-article"

# 2. Load the Web Content
loader = WebBaseLoader(target_url)
docs = loader.load()

# 3. Define the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# 4. Create a Summarization Prompt
prompt = ChatPromptTemplate.from_template("""
    You are a professional research assistant. 
    Summarize the following web page content into 3 concise bullet points.
    
    Content: {content}
""")

# 5. Build and Run the Chain
chain = prompt | llm | StrOutputParser()
summary = chain.invoke({"content": docs[0].page_content})

print("--- WEB SUMMARY COMPLETED ---")

# =====================================================================
# 6. AUTOMATICALLY SAVE TO FILE
# =====================================================================

# Create a clean filename using the current date and time
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"summary_{timestamp}.txt"

# Open the file in 'write' mode ('w') and save the data
with open(filename, "w", encoding="utf-8") as file:
    file.write(f"SOURCE URL: {target_url}\n")
    file.write(f"PROCESSED ON: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    file.write("-" * 40 + "\n\n")
    file.write(summary)

print(f"Success! Summary saved locally to: {filename}")
