# from langchain.chains.qa_with_sources.retrieval import RetrievalQAWithSourcesChain
# from langchain_openai import OpenAI, OpenAIEmbeddings
# import streamlit as st
# from pinecone import Pinecone
# from langchain_pinecone import PineconeVectorStore

# # Ensure you have initialized Pinecone correctly
# PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
# index_name = "hospitalpolicy"
# pc = Pinecone(api_key=PINECONE_API_KEY)
# embeddings = OpenAIEmbeddings()
# # pinecone_index = Pinecone.from_existing_index(, embedding)
# pinecone_index = pc.Index(index_name)


# vector_store = PineconeVectorStore(index=pinecone_index, embedding=embeddings)

# # Wrap it as a retriever
# retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# # PINECONE_INDEX = "hospitalpolicy"
# llm = OpenAI(temperature=0.2)
# chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=retriever)


# def run_qa_chain(query, llm):
#     chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=retriever)
    
#     qa_results = chain.invoke({"question": query})
    
#     return qa_results


# def retrieve_query(query, k=2):
#     matching_results = pinecone_index.similarity_search(query, k=k)
#     return matching_results


# def retrieve_answers(query):
#     print(f"Retrieving answers for: {query}")  # Debugging output
#     doc_search = retrieve_query(query)
#     if not doc_search:
#         return {"answer": "⚠️ No relevant documents found.", "sources": "N/A"}

#     try:
#         response = run_qa_chain(query, llm)
#         print(f"Chain Response: {response}")  # Debugging

#         if not isinstance(response, dict):
#             return {"answer": "⚠️ Unexpected response format.", "sources": "N/A"}

#         return response
#     except Exception as e:
#         return {"answer": f"⚠️ Error: {str(e)}", "sources": "N/A"}



from pathlib import Path
from langchain.chains.qa_with_sources.retrieval import RetrievalQAWithSourcesChain
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import streamlit as st
import time

# Define FAISS index storage path
FAISS_INDEX_PATH = Path("faiss_index")

# Load OpenAI Embeddings
embeddings = OpenAIEmbeddings()

# Function to create or load FAISS index
def load_or_create_faiss_index(documents):
    
    # Ensure the directory exists
    FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if FAISS_INDEX_PATH.exists():
        placeholder = st.empty()
        placeholder.write("✅ FAISS index found. Loading...")
        time.sleep(5)
        placeholder.empty()
        return FAISS.load_local(str(FAISS_INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
    st.write("⚠️ FAISS index not found.")
    
    
    if not documents:
        print("⚠️ No documents to index. Skipping FAISS initialization.")
        return None
    
    texts = [doc.page_content for doc in documents]
    metadatas = [{"source": doc.metadata.get("source", "Unknown")} for doc in documents]
    
    if not texts:
        print("⚠️ No valid text found in documents. Skipping FAISS initialization.")
        return None
    
    vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    vector_store.save_local(str(FAISS_INDEX_PATH))
    return vector_store

# Load or initialize FAISS index
documents = []  # Populate this list dynamically\if "vector_store" not in st.session_state:
st.session_state["vector_store"] = load_or_create_faiss_index(documents)

vector_store = st.session_state["vector_store"]
if vector_store:
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
else:
    retriever = None
    print("📢 No vector store created. Waiting for document upload.")

# Load LLM
llm = OpenAI(temperature=0.2)
if retriever:
    chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=retriever)
else:
    print("🚨 No retriever available! Waiting for document upload.")
    chain = None

def run_qa_chain(query):
    qa_results = chain.invoke({"question": query})
    return qa_results

def retrieve_answers(query):
    print(f"Retrieving answers for: {query}")
    try:
        response = run_qa_chain(query)
        print(f"Chain Response: {response}")

        if not isinstance(response, dict):
            return {"answer": "⚠️ Unexpected response format.", "sources": "N/A"}

        return response
    except Exception as e:
        return {"answer": f"⚠️ Error: {str(e)}", "sources": "N/A"}

# Function to add new documents without overwriting
def add_documents_to_faiss(new_documents):
    if new_documents:
        vector_store.add_texts(
            texts=[doc.page_content for doc in new_documents],
            metadatas=[{"source": doc.metadata.get("source", "Unknown")} for doc in new_documents]
        )
        vector_store.save_local(str(FAISS_INDEX_PATH))  # Save FAISS index persistently
        st.success("New documents added successfully! ✅")

# Function to clear FAISS index
def clear_faiss_index():
    global vector_store
    if FAISS_INDEX_PATH.exists():
        import shutil
        shutil.rmtree(FAISS_INDEX_PATH)
    vector_store = FAISS(embeddings)
    st.session_state["vector_store"] = vector_store
    st.success("FAISS index cleared successfully!")



