import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

load_dotenv()


vector_stores = {}

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def process_document(text: str):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        length_function=len,
    )
    docs = text_splitter.create_documents([text])
    
    # Add chunk index to metadata
    for i, doc in enumerate(docs):
        doc.metadata["chunk_index"] = i + 1
    
    vector_db = FAISS.from_documents(docs, embeddings)
    
    return vector_db, len(docs)

def answer_question(doc_id: str, question: str):
    if doc_id not in vector_stores:
        return "Document not found", []
    
    vector_db = vector_stores[doc_id]
    

    llm = ChatOllama(
        model="llama3.1:latest",
        temperature=0.5,
    )


    template = """Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Answer strictly based on the context provided. Do not use your general knowledge.

    {context}

    Question: {question}
    Helpful Answer:"""
    
    QA_CHAIN_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template=template,
    )

    try:
        # Retrieval QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )

        result = qa_chain({"query": question})
        
        answer = result["result"]
        source_documents = result["source_documents"]
        
        sources = [doc.metadata.get("chunk_index", "unknown") for doc in source_documents]

        return answer, sources
    except Exception as e:
        print(f"DEBUG: LLM Call Error: {str(e)}")
        raise e
