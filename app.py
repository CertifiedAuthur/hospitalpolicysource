# from pathlib import Path
# import sqlite3
# import time
# from langchain_openai import OpenAIEmbeddings
# import streamlit as st
# from db import delete_file, initialize_database
# from document_processor import handle_file_upload
# from retriever import retrieve_answers  #, run_qa_chain
# from langchain_openai import OpenAI
# from pinecone import ServerlessSpec
# from pinecone import Pinecone
# from langchain_community.vectorstores import Pinecone as LangchainPinecone

# PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
# PINECONE_INDEX = "hospitalpolicy"

# # Initialize Pinecone once
# if "pinecone_client" not in st.session_state:
#     st.session_state.pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    
    
# def initialize_session_state():
#     if "chat_history" not in st.session_state:
#         st.session_state.chat_history = []
#     if "initialized" not in st.session_state:
#         initialize_database()
#         st.session_state.initialized = True


# def configure_pinecone_index():
#     """Ensures the Pinecone index is ready without blocking execution."""
#     pc = st.session_state.pinecone_client  # Use session state for persistence
#     existing_indexes = [index["name"] for index in pc.list_indexes()]

#     if PINECONE_INDEX in existing_indexes:
#         if "pinecone_ready" not in st.session_state:
#             print("VectorDatabase :: Ready!")
#             st.session_state.pinecone_ready = True
#     else:
#         spec = ServerlessSpec(cloud='aws', region='us-east-1')
#         pc.create_index(
#             PINECONE_INDEX,
#             dimension=1536,
#             metric='dotproduct',
#             spec=spec
#         )
#         # Wait for index readiness in a background-friendly way
#         with st.spinner("Initializing vector database... Please wait."):
#             while not pc.describe_index(PINECONE_INDEX).status['ready']:
#                 time.sleep(1)

#         print("VectorDatabase :: Ready!")
#         st.session_state.pinecone_ready = True


# # Run this once
# if "pinecone_ready" not in st.session_state:
#     configure_pinecone_index()

# # Configuration
# st.set_page_config(page_title="Hospital Policy Search", layout="wide")
# admin_password = st.secrets["ADMIN_PASSWORD"]

# # Sidebar: Admin Mode
# st.sidebar.title("Admin Panel")
# admin_mode = st.sidebar.checkbox("Enable Admin Mode")
# admin_authenticated = False

# if admin_mode:
#     password = st.sidebar.text_input("Enter Admin Password", type="password")
#     if password == admin_password:
#         admin_authenticated = True
#         st.sidebar.success("Admin authenticated")
#     else:
#         st.sidebar.error("Incorrect password!")

# # Landing Page Info
# st.title("🏥 Hospital Policy Document Search")
# st.markdown(
#     """
#     **This system helps hospital staff quickly find answers to policy-related questions and ensure compliance with regulations.**
    
#     You can ask about:
#     - 📌 **Patient care policies**  
#     - 🏥 **Workplace safety guidelines**  
#     - 🔐 **HIPAA compliance rules**  
#     - ⚠️ **Risk management procedures**  
    
#     🚀 **Get clear answers with references to official policy documents.**
#     """
# )

# initialize_database()

# DOCUMENTS_DIR = Path('documents')
# DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

# # Track uploaded files to avoid reprocessing
# if "uploaded_files" not in st.session_state:
#     st.session_state.uploaded_files = []

# # File Upload (Admin Only)
# if admin_authenticated:
#     st.sidebar.subheader("Upload New Documents")
#     uploaded_file = st.sidebar.file_uploader("Upload a document", type=["pdf", "txt"])
#     if uploaded_file:
#         with st.spinner("Processing Document..."):
#             document = handle_file_upload(uploaded_file, DOCUMENTS_DIR)
            
#             if document:  # Only proceed if document is not None
#                 embeddings = OpenAIEmbeddings()
#                 vectorindex = LangchainPinecone.from_texts(
#                 texts=[doc.page_content for doc in document],  # Extract text
#                 embedding=OpenAIEmbeddings(),
#                 index_name=PINECONE_INDEX,
#                 metadatas=[{"source": doc.metadata.get("source", "Unknown") if doc.metadata else "Unknown"} for doc in document]
#                 )
#                 placeholder = st.empty()
#                 placeholder.success("Document uploaded and stored successfully.")
#                 time.sleep(5)
#                 placeholder.empty()
#             else:
#                 st.error("Failed to process the document.")
#             st.sidebar.success(f"✅ {uploaded_file.name} uploaded successfully!")
                    
                    
# if "pinecone_ready" in st.session_state and st.session_state.pinecone_ready:
#     # Proceed with answering queries
#     query = st.text_input("🔍 Enter your question about hospital policies:")
#     if query:
#         with st.spinner("Searching for answer..."):
#             answer = retrieve_answers(query)  # Your retrieval function
#             if answer:
#                 st.subheader("📜 Answer")
#                 st.write(answer["answer"])
#                 st.write(answer["sources"])
                
#     # Clear query after execution
#     st.session_state.query = ""
        
#     # Display chat history
#     for role, message in st.session_state.chat_history:
#         with st.chat_message("user" if role == "You" else "assistant"):
#             st.write(message)
                
                
#     # Sidebar: Uploaded files display
#     st.sidebar.write("### Uploaded Files")
#     try:
#         conn = sqlite3.connect("hospital_policy.db", check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("SELECT file_name FROM documents;")  # Uses a single `documents` table
#         uploaded_files_list = [file[0] for file in cursor.fetchall()]

#         if uploaded_files_list:
#             for file_name in uploaded_files_list:
#                 delete_key = f"delete_{file_name}"
#                 col1, col2 = st.sidebar.columns([3, 1])
#                 with col1:
#                     st.sidebar.write(file_name)
#                 with col2:
#                     if st.sidebar.button("Delete", key=delete_key):
#                         try:
#                             delete_file(file_name)
#                             st.sidebar.success(f"✅ File '{file_name}' deleted successfully!")
#                         except Exception as e:
#                             st.error(f"❌ Failed to delete file '{file_name}': {e}")
#         else:
#             st.sidebar.info("ℹ️ No files uploaded.")
#     except Exception as e:
#         st.sidebar.error(f"❌ Failed to retrieve files: {e}")


from pathlib import Path
import sqlite3
import time
import streamlit as st
from langchain_openai import OpenAIEmbeddings
from db import delete_file, initialize_database
from document_processor import handle_file_upload
from retriever import retrieve_answers
from pinecone import ServerlessSpec, Pinecone
from langchain_community.vectorstores import Pinecone as LangchainPinecone

PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX = "hospitalpolicy"

# Initialize Pinecone once
if "pinecone_client" not in st.session_state:
    st.session_state.pinecone_client = Pinecone(api_key=PINECONE_API_KEY)


def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "initialized" not in st.session_state:
        initialize_database()
        st.session_state.initialized = True
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []



def configure_pinecone_index():
    """Ensures the Pinecone index is ready without blocking execution."""
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
        
def process_web_links():
    """Trigger processing when web links are entered."""
    web_links = st.session_state.get("web_links", "").strip().split("\n")
    if any(web_links):  # Ensure input is not empty
        placeholder = st.empty()
        placeholder.write("🔄 Processing web links...")
        time.sleep(5)
        placeholder.empty()

        handle_file_upload([], web_links)  # Call function with empty file list and web links
        st.session_state["files_processed"] = True
        placeholder.success("✅ Web links processed successfully!")
        time.sleep(5)
        placeholder.empty()


if "pinecone_ready" not in st.session_state:
    configure_pinecone_index()

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
st.markdown(
    """
    **Find answers to hospital policies with references to official documents.**
    
    **Topics Covered:**
    - 📌 **Patient care policies**  
    - 🏥 **Workplace safety guidelines**  
    - 🔐 **HIPAA compliance rules**  
    - ⚠️ **Risk management procedures**  
    """
)

initialize_session_state()
DOCUMENTS_DIR = Path('documents')
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

uploaded_file = None
web_links = None

if admin_authenticated:
    st.sidebar.subheader("Upload New Documents")
    uploaded_file = st.sidebar.file_uploader("Upload a document", accept_multiple_files=True, type=["pdf", "txt"])
    # Store uploaded file name in session state
    if uploaded_file:
        for file in uploaded_file:
            st.session_state["file_name"] = file.name
            
    # Web links input
    web_links = st.sidebar.text_area("Enter web links (one per line)", key="web_links", on_change=process_web_links)
    if (uploaded_file or web_links) and not st.session_state["files_processed"]:
        with st.spinner("Processing Document..."):
            document = handle_file_upload(uploaded_file, DOCUMENTS_DIR)
            if document:
                embeddings = OpenAIEmbeddings()
                LangchainPinecone.from_texts(
                    texts=[doc.page_content for doc in document],
                    embedding=embeddings,
                    index_name=PINECONE_INDEX,
                    metadatas=[{"source": doc.metadata.get("source", "Unknown") if doc.metadata else "Unknown"} for doc in document]
                )
                st.sidebar.success(f"✅ {uploaded_file.name} uploaded successfully!")
            else:
                st.error("Failed to process the document.")

query = st.text_input("\U0001F50D Enter your question about hospital policies:", key="query")

if query:
    with st.spinner("Searching for answer..."):
        try:
            answer = retrieve_answers(query)
            if answer:
                response = answer["answer"]
                source = answer["sources"]
                
                st.session_state.chat_history.append(("You", query))
                st.session_state.chat_history.append(("Bot", response))
                st.session_state.chat_history.append(("Source", source))
            
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
                        st.error(f"❌ Failed to delete file '{file_name}': {e}")
    else:
        st.sidebar.info("ℹ️ No files uploaded.")
except Exception as e:
    st.sidebar.error(f"❌ Failed to retrieve files: {e}")
