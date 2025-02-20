from pathlib import Path
import sqlite3
import time
from langchain_openai import OpenAIEmbeddings
import streamlit as st
from db import delete_file, initialize_database
from document_processor import handle_file_upload
from retriever import retrieve_answers
from langchain_openai import OpenAI
from pinecone import ServerlessSpec, Pinecone
from langchain_community.vectorstores import Pinecone as LangchainPinecone

PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX = "hospitalpolicy"

def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "pinecone_client" not in st.session_state:
        st.session_state.pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    if "pinecone_ready" not in st.session_state:
        st.session_state.pinecone_ready = False
        configure_pinecone_index()
    if "initialized" not in st.session_state:
        initialize_database()
        st.session_state.initialized = True

def configure_pinecone_index():
    pc = st.session_state.pinecone_client
    existing_indexes = [index["name"] for index in pc.list_indexes()]

    if PINECONE_INDEX in existing_indexes:
        st.session_state.pinecone_ready = True
    else:
        spec = ServerlessSpec(cloud='aws', region='us-east-1')
        pc.create_index(
            PINECONE_INDEX, dimension=1536, metric='dotproduct', spec=spec
        )
        with st.spinner("Initializing vector database... Please wait."):
            while not pc.describe_index(PINECONE_INDEX).status['ready']:
                time.sleep(1)
        st.session_state.pinecone_ready = True

# Ensure session state is initialized
initialize_session_state()

st.set_page_config(page_title="Hospital Policy Search", layout="wide")
admin_password = st.secrets["ADMIN_PASSWORD"]

st.sidebar.title("Admin Panel")
admin_mode = st.sidebar.checkbox("Enable Admin Mode")
admin_authenticated = False

if admin_mode:
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password == admin_password:
        admin_authenticated = True
        st.sidebar.success("Admin authenticated")
    else:
        st.sidebar.error("Incorrect password!")

st.title("\U0001F3E5 Hospital Policy Document Search")
st.markdown("""
    **Find answers to hospital policies efficiently.**

    **You can ask about:**
    - \U0001F4CC **Patient care policies**  
    - \U0001F3E5 **Workplace safety guidelines**  
    - \U0001F510 **HIPAA compliance rules**  
    - ⚠️ **Risk management procedures**  

    🚀 **Get clear answers with references.**
""")

DOCUMENTS_DIR = Path('documents')
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if admin_authenticated:
    st.sidebar.subheader("Upload New Documents")
    uploaded_file = st.sidebar.file_uploader("Upload a document", type=["pdf", "txt"])
    if uploaded_file:
        with st.spinner("Processing Document..."):
            document = handle_file_upload(uploaded_file, DOCUMENTS_DIR)
            if document:
                embeddings = OpenAIEmbeddings()
                LangchainPinecone.from_texts(
                    texts=[doc.page_content for doc in document],
                    embedding=embeddings,
                    index_name=PINECONE_INDEX,
                    metadatas=[{"source": doc.metadata.get("source", "Unknown")} for doc in document]
                )
                st.sidebar.success(f"✅ {uploaded_file.name} uploaded successfully!")
            else:
                st.sidebar.error("Failed to process the document.")


if st.session_state.pinecone_ready:
    query = st.text_input("🔍 Enter your question about hospital policies:")
    if query:
        with st.spinner("Searching for answer..."):
            try:
                answer = retrieve_answers(query)
                if answer:
                    
                    response = answer["answer"]
                    source = answer["sources"]
                    st.session_state.chat_history.append(("You", query))
                    st.session_state.chat_history.append(("Bot", response))
                    st.session_state.chat_history.append(("Soruce", source))
                    
            except Exception as e:
                st.error(f"Error retrieving response: {e}")
                    
        st.session_state.query = ""
        
    for role, message in st.session_state.chat_history:
        with st.chat_message("user" if role == "You" else "assistant"):
            st.write(message)

st.sidebar.write("### Uploaded Files")
try:
    conn = sqlite3.connect("hospital_policy.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT file_name FROM documents;")
    uploaded_files_list = [file[0] for file in cursor.fetchall()]

    if uploaded_files_list:
        for file_name in uploaded_files_list:
            delete_key = f"delete_{file_name}"
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.sidebar.write(file_name)
            with col2:
                if st.sidebar.button("Delete", key=delete_key):
                    try:
                        delete_file(file_name)
                        st.sidebar.success(f"✅ File '{file_name}' deleted successfully!")
                    except Exception as e:
                        st.sidebar.error(f"❌ Failed to delete file '{file_name}': {e}")
    else:
        st.sidebar.info("ℹ️ No files uploaded.")
except Exception as e:
    st.sidebar.error(f"❌ Failed to retrieve files: {e}")
