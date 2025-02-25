import time
import requests
import streamlit as st
from bs4 import BeautifulSoup
import pdfplumber
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from db import insert_file_metadata
from langchain.text_splitter import RecursiveCharacterTextSplitter


def extract_text_from_pdf(file_path: Path):
    """Extracts text from a PDF file and splits it into chunks of max 512 characters with 200 overlap."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    
    return [Document(page_content=chunk, metadata={"source": str(file_path)}) for chunk in chunks]

def extract_text_from_url(url: str):
    """Extracts text from a URL and splits it into chunks of max 512 characters with 200 overlap."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content = soup.get_text()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(content)
    
    return [Document(page_content=chunk, metadata={"source": url}) for chunk in chunks]


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

            documents = []  # List to store chunked documents

            # Process PDF files
            if uploaded_file.type == 'application/pdf':
                documents = extract_text_from_pdf(file_path)  # Returns a list of Document objects

            # Process Text files
            elif uploaded_file.type == 'text/plain':
                text = uploaded_file.getvalue().decode("utf-8")
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                chunks = text_splitter.split_text(text)
                documents = [Document(page_content=chunk, metadata={"source": uploaded_file.name}) for chunk in chunks]

            else:
                placeholder.error(f"Unsupported file type: {uploaded_file.type}")
                continue  # Skip this file
            
            # Iterate over chunked documents
            for doc in documents:
                print(f"Extracted text: {doc.page_content[:200]}")
                insert_file_metadata(doc.metadata["source"], doc.page_content)
                processed_documents.append(doc)  # Append each chunk separately

        # Process web links
        for url in web_links:
            url = url.strip()
            if not url:
                continue  # Skip empty lines
            try:
                documents = extract_text_from_url(url)  # Returns a list of Document objects

                for doc in documents:  # Iterate over the list
                    print(f"Extracted text from URL: {doc.page_content[:200]}")
                    insert_file_metadata(url, doc.page_content)  
                    processed_documents.append(doc)  # Append each document separately

            except Exception as e:
                placeholder.error(f"Failed to process {url}: {str(e)}")

        time.sleep(5)
        placeholder.empty()
        
        return processed_documents  # Return all processed documents
    
    except Exception as e:
        placeholder.error(f"An error occurred: {str(e)}")
        return None


        
def create_vector_index(docs, embeddings):
    return FAISS.from_documents(docs, embeddings)

