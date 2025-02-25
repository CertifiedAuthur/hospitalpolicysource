# from pathlib import Path
# import sqlite3
# import time
# import streamlit as st
# from langchain_openai import OpenAIEmbeddings
# from db import delete_file, initialize_database
# from document_processor import handle_file_upload
# from retriever import retrieve_answers
# from pinecone import ServerlessSpec, Pinecone
# from langchain_pinecone import Pinecone as LangchainPinecone
# from langchain_community.vectorstores import Chroma


# PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
# # Initialize Pinecone
# pc = Pinecone(api_key=PINECONE_API_KEY)

# host = st.secrets["HOST"]

# PINECONE_INDEX = "hospitalpolicy"
# print(type(PINECONE_INDEX))



# # Initialize Pinecone once
# if "pinecone" not in st.session_state:
#     st.session_state.pinecone = Pinecone(api_key=PINECONE_API_KEY)


# def initialize_session_state():
#     if "chat_history" not in st.session_state:
#         st.session_state.chat_history = []
#     if "initialized" not in st.session_state:
#         initialize_database()
#         st.session_state.initialized = True
#     if "uploaded_files" not in st.session_state:
#         st.session_state.uploaded_files = []
#     # Ensure session state variable exists
#     if "files_processed" not in st.session_state:
#         st.session_state["files_processed"] = False



# def configure_pinecone_index():
#     # configure client
#     pc = Pinecone(api_key=PINECONE_API_KEY)

#     if PINECONE_INDEX == pc.list_indexes()[0]["name"]:
#         print("VectorDatabase :: Ready!")
#     else:
        
#         spec = ServerlessSpec(cloud='aws', region='us-east-1')
#         # create a new index
#         pc.create_index(
#             PINECONE_INDEX,
#             dimension=1536,  # dimensionality of mixedbread large
#             metric='dotproduct',
#             spec=spec
#         )

#         # wait for index to be initialized
#         while not pc.describe_index(PINECONE_INDEX).status['ready']:
#             time.sleep(1)
        
# def process_web_links():
#     """Trigger processing when web links are entered."""
#     web_links = st.session_state.get("web_links", "").strip().split("\n")
#     if any(web_links):  # Ensure input is not empty
#         placeholder = st.empty()
#         placeholder.write("🔄 Processing web links...")
#         time.sleep(5)
#         placeholder.empty()

#         handle_file_upload([], web_links)  # Call function with empty file list and web links
#         st.session_state["files_processed"] = True
#         placeholder.success("✅ Web links processed successfully!")
#         time.sleep(5)
#         placeholder.empty()


# if "pinecone_ready" not in st.session_state:
#     configure_pinecone_index()

# st.set_page_config(page_title="Hospital Policy Search", layout="wide")
# admin_password = st.secrets["ADMIN_PASSWORD"]

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

# st.title("\U0001F3E5 Hospital Policy Document Search")
# st.markdown(
#     """
#     **Find answers to hospital policies with references to official documents.**
    
#     **Topics Covered:**
#     - 📌 **Patient care policies**  
#     - 🏥 **Workplace safety guidelines**  
#     - 🔐 **HIPAA compliance rules**  
#     - ⚠️ **Risk management procedures**  
#     """
# )

# initialize_session_state()
# DOCUMENTS_DIR = Path('documents')
# DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

# uploaded_file = None
# web_links = None

# if admin_authenticated:
#     st.sidebar.subheader("Upload New Documents")
#     if st.sidebar.button("Delete Vector"):
#         PINECONE_INDEX.delete(delete_all=True)
#     uploaded_file = st.sidebar.file_uploader("Upload a document", accept_multiple_files=True, type=["pdf", "txt"])
#     # Store uploaded file name in session state
#     if uploaded_file:
#         st.session_state["files_processed"] = False
#         for file in uploaded_file:
#             st.session_state["file_name"] = file.name
            
#     # Web links input
#     web_links = st.sidebar.text_area("Enter web links (one per line)", key="web_links", on_change=process_web_links)
#     if web_links:
#         st.session_state["files_processed"] = False
#     if (uploaded_file or web_links) and not st.session_state["files_processed"]:
#         if not st.session_state["files_processed"]:
#             with st.spinner("Processing Document..."):
#                 document = handle_file_upload(uploaded_file, web_links, DOCUMENTS_DIR)
#                 if document:
#                     embeddings = OpenAIEmbeddings()
#                     LangchainPinecone.from_texts(
#                         texts=[doc.page_content for doc in document],
#                         embedding=embeddings,
#                         index_name=PINECONE_INDEX,
#                         # index_name=PINECONE_INDEX,
#                         metadatas=[{"source": doc.metadata.get("source", "Unknown") if doc.metadata else "Unknown"} for doc in document]
#                     )
#                     st.sidebar.success(f"✅ {uploaded_file} uploaded successfully!")
#                 else:
#                     st.error("Failed to process the document.")

# query = st.text_input("\U0001F50D Enter your question about hospital policies:")

# if query:
#     with st.spinner("Searching for answer..."):
#         try:
#             answer = retrieve_answers(query)
#             if answer:
#                 response = answer["answer"]
#                 source = answer["sources"]
                
#                 st.session_state.chat_history.append(("You", query))
#                 st.session_state.chat_history.append(("Bot", response))
#                 st.session_state.chat_history.append(("Source", source))
            
#         except Exception as e:
#             st.error(f"Error retrieving response: {e}")
#     st.session_state.query = ""
        

# for role, message in st.session_state.chat_history:
#     with st.chat_message("user" if role == "You" else "assistant"):
#         st.write(message)

# st.sidebar.write("### Uploaded Files")
# try:
#     conn = sqlite3.connect("hospital_policy.db", check_same_thread=False)
#     cursor = conn.cursor()
#     cursor.execute("SELECT file_name FROM documents;")
#     uploaded_files_list = [file[0] for file in cursor.fetchall()]

#     if uploaded_files_list:
#         for file_name in uploaded_files_list:
#             delete_key = f"delete_{file_name}"
#             col1, col2 = st.sidebar.columns([3, 1])
#             with col1:
#                 st.sidebar.write(file_name)
#             with col2:
#                 if st.sidebar.button("Delete", key=delete_key):
#                     try:
#                         delete_file(file_name)
#                         st.sidebar.success(f"✅ File '{file_name}' deleted successfully!")
#                     except Exception as e:
#                         st.error(f"❌ Failed to delete file '{file_name}': {e}")
#     else:
#         st.sidebar.info("ℹ️ No files uploaded.")
# except Exception as e:
#     st.sidebar.error(f"❌ Failed to retrieve files: {e}")




from pathlib import Path
import sqlite3
import time
import streamlit as st
from langchain_openai import OpenAIEmbeddings
from db import delete_file, initialize_database
from document_processor import handle_file_upload
from retriever import clear_faiss_index, load_or_create_faiss_index, retrieve_answers
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

# Initialize FAISS in-memory
embeddings = OpenAIEmbeddings()
FAISS_INDEX_PATH = Path("faiss_index")

def load_faiss_index():
    if FAISS_INDEX_PATH.exists():
        return FAISS.load_local(
            str(FAISS_INDEX_PATH), 
            embeddings, 
            allow_dangerous_deserialization=True  # Enable safe loading
        )
    return None


def save_faiss_index(vector_store):
    vector_store.save_local(str(FAISS_INDEX_PATH))

def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "initialized" not in st.session_state:
        initialize_database()
        st.session_state.initialized = True
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "files_processed" not in st.session_state:
        st.session_state["files_processed"] = False

def process_web_links():
    """Trigger processing when web links are entered."""
    web_links = st.session_state.get("web_links", "").strip().split("\n")
    if any(web_links):
        placeholder = st.empty()
        placeholder.write("🔄 Processing web links...")
        time.sleep(5)
        placeholder.empty()
        handle_file_upload([], web_links)
        st.session_state["files_processed"] = True
        placeholder.success("✅ Web links processed successfully!")
        time.sleep(5)
        placeholder.empty()

# st.set_page_config(page_title="Hospital Policy Search", layout="wide")
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

st.title("🏥 Hospital Policy Document Search")
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
vector_store = load_faiss_index()

if admin_authenticated:
    st.sidebar.subheader("Upload New Documents")
    if st.sidebar.button("Reset FAISS Index"):
        clear_faiss_index()
    
    uploaded_file = st.sidebar.file_uploader("Upload a document", accept_multiple_files=True, type=["pdf", "txt"])
    if uploaded_file:
        st.session_state["files_processed"] = False
        for file in uploaded_file:
            st.session_state["file_name"] = file.name
    
    web_links = st.sidebar.text_area("Enter web links (one per line)", key="web_links", on_change=process_web_links)
    if web_links:
        st.session_state["files_processed"] = False
    
    if (uploaded_file or web_links) and not st.session_state["files_processed"]:
        with st.spinner("Processing Document..."):
            document = handle_file_upload(uploaded_file, web_links, DOCUMENTS_DIR)
            
            if document:
                if vector_store is None:
                    vector_store = load_or_create_faiss_index(document)
                else:
                    vector_store.add_texts(
                        texts=[doc.page_content for doc in document],
                        metadatas=[{"source": doc.metadata.get("source", "Unknown")} for doc in document]
                    )
                save_faiss_index(vector_store)
                st.sidebar.success(f"✅ {uploaded_file} uploaded successfully!")
            else:
                st.error("❌ Failed to process the document.")

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
