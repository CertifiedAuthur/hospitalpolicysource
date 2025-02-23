from langchain.chains.qa_with_sources.retrieval import RetrievalQAWithSourcesChain
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_community.vectorstores import Pinecone

# Ensure you have initialized Pinecone correctly
embedding = OpenAIEmbeddings()
pinecone_index = Pinecone.from_existing_index("hospitalpolicy", embedding)

# Wrap it as a retriever
retriever = pinecone_index.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# PINECONE_INDEX = "hospitalpolicy"
llm = OpenAI(temperature=0.2)
chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=retriever)


def run_qa_chain(query, llm):
    chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=retriever)
    
    qa_results = chain.invoke({"question": query})
    
    return qa_results


def retrieve_query(query, k=2):
    matching_results = pinecone_index.similarity_search(query, k=k)
    return matching_results


def retrieve_answers(query):
    print(f"Retrieving answers for: {query}")  # Debugging output
    doc_search = retrieve_query(query)
    if not doc_search:
        return {"answer": "⚠️ No relevant documents found.", "sources": "N/A"}

    try:
        response = run_qa_chain(query, llm)
        print(f"Chain Response: {response}")  # Debugging

        if not isinstance(response, dict):
            return {"answer": "⚠️ Unexpected response format.", "sources": "N/A"}

        return response
    except Exception as e:
        return {"answer": f"⚠️ Error: {str(e)}", "sources": "N/A"}