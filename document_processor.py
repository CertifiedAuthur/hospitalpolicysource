import time
import requests
import streamlit as st
from bs4 import BeautifulSoup
import pdfplumber
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from db import insert_file_metadata, store_document_and_embedding

# Extract text from a PDF
def extract_text_from_pdf(file_path: Path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Extract text from a URL
def extract_text_from_url(url: str):
    documents = []
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content = soup.get_text()
    
    # Create a document with content and metadata
    doc = Document(
        page_content=content,
        metadata={"source": url}
    )
    documents.append(doc)
    return documents

def handle_file_upload(uploaded_files, web_links, documents_dir: Path):
    """Handles processing for both file uploads and web links."""

    placeholder = st.empty()
    
    try:
        processed_documents = []

        # Process uploaded files
        for uploaded_file in uploaded_files:
            file_path = documents_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Process PDF files
            if uploaded_file.type == 'application/pdf':
                text = extract_text_from_pdf(file_path)
                print(f"Extracted text from PDF: {text[:200]}")
                doc = Document(page_content=text, metadata={"source": uploaded_file.name})
                insert_file_metadata(uploaded_file.name, text)

            # Process Text files
            elif uploaded_file.type == 'text/plain':
                text = uploaded_file.getvalue().decode("utf-8")
                print(f"Extracted text from TXT: {text[:200]}")
                doc = Document(page_content=text, metadata={"source": uploaded_file.name})
                insert_file_metadata(uploaded_file.name, text)

            else:
                placeholder.error(f"Unsupported file type: {uploaded_file.type}")
                continue  # Skip this file

            processed_documents.append(doc)

        # Process web links
        for url in web_links:
            url = url.strip()
            if not url:
                continue  # Skip empty lines
            try:
                text = extract_text_from_url(url)
                print(f"Extracted text from URL: {text[:200]}")
                doc = Document(page_content=text, metadata={"source": url})
                insert_file_metadata(url, text)
                processed_documents.append(doc)
            except Exception as e:
                placeholder.error(f"Failed to process {url}: {str(e)}")

        time.sleep(5)
        placeholder.empty()
        
        return processed_documents  # Return all processed documents
    
    except Exception as e:
        placeholder.error(f"An error occurred: {str(e)}")
        time.sleep(5)
        placeholder.empty()
        return None

        
        
def create_vector_index(docs, embeddings):
    return FAISS.from_documents(docs, embeddings)

