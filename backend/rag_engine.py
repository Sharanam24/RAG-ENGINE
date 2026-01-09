import os
import asyncio
from typing import List

# -----------------------------
# LangChain imports (compatible)
# -----------------------------
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_community.llms import Ollama
    from langchain.chains import RetrievalQA
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
except ImportError:
    try:
        from langchain.embeddings import HuggingFaceEmbeddings
        from langchain.vectorstores import Chroma
        from langchain.llms import Ollama
        from langchain.chains import RetrievalQA
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.schema import Document
    except ImportError:
        HuggingFaceEmbeddings = None
        Chroma = None
        Ollama = None
        RetrievalQA = None
        RecursiveCharacterTextSplitter = None
        Document = None


# -----------------------------
# RAG Engine
# -----------------------------
class RAGEngine:
    def __init__(self):
        self.embeddings = None
        self.llm = None
        self.vectorstore = None
        self.qa_chain = None

        self.persist_directory = "./chroma_db"
        self._initialized = False

        try:
            self._initialize()
        except Exception as e:
            print(f"RAG init deferred: {e}")

    # -----------------------------
    # Initialization
    # -----------------------------
    def _initialize(self):
        if self._initialized:
            return

        # Embeddings
        if HuggingFaceEmbeddings:
            try:
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            except Exception as e:
                print(f"Embeddings error: {e}")
                self.embeddings = None

        # LLM (Ollama) - Disabled by default
        # Uncomment and install Ollama if you want full LLM capabilities
        # To use Ollama: 
        #   1. Install from https://ollama.ai
        #   2. Run: ollama pull llama2
        #   3. Uncomment the code below
        self.llm = None
        # if Ollama:
        #     try:
        #         self.llm = Ollama(
        #             model="llama2",
        #             base_url="http://localhost:11434"
        #         )
        #         print("✅ Ollama LLM connected")
        #     except Exception as e:
        #         print(f"⚠️ Ollama not available: {e}")
        #         self.llm = None

        # Vector store
        self._initialize_vectorstore()

        self._initialized = True

    # -----------------------------
    # Vector Store
    # -----------------------------
    def _initialize_vectorstore(self):
        if not (Chroma and HuggingFaceEmbeddings and Document):
            return

        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                return
            except Exception as e:
                print(f"Chroma load error: {e}")

        # Sample documents - expand with your own knowledge base
        docs = [
            "FastAPI is a modern Python web framework for building APIs quickly and efficiently.",
            "RAG (Retrieval-Augmented Generation) combines information retrieval with language generation for more accurate AI responses.",
            "ChromaDB is a vector database that stores embeddings for semantic search and similarity matching.",
            "LangChain is a framework for building applications powered by large language models.",
            "Vector embeddings convert text into numerical representations that capture semantic meaning.",
            "Semantic search allows finding information based on meaning rather than exact keyword matches.",
            "The RAG automation system stores conversation threads in a SQLite database for persistence.",
            "Users can create multiple conversation threads, each maintaining its own message history.",
            "The frontend interface allows real-time chat with the RAG-powered assistant.",
            "Embeddings enable the system to find relevant information even when exact words don't match."
        ]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        documents = splitter.split_documents(
            [Document(page_content=d) for d in docs]
        )

        try:
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
        except Exception as e:
            print(f"Chroma create error: {e}")
            self.vectorstore = None

        # QA Chain
        if self.llm and self.vectorstore and RetrievalQA:
            try:
                self.qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
                    return_source_documents=False
                )
            except Exception as e:
                print(f"QA chain error: {e}")
                self.qa_chain = None

    # -----------------------------
    # Query (ASYNC SAFE)
    # -----------------------------
    async def query(self, question: str) -> str:
        if not self._initialized:
            try:
                self._initialize()
            except Exception as e:
                return f"RAG system is initializing. Please try again in a moment. Error: {str(e)}"

        # Full RAG with LLM (if available)
        if self.qa_chain:
            try:
                result = await asyncio.to_thread(
                    self.qa_chain.invoke,
                    {"query": question}
                )
                return result.get("result", str(result))
            except Exception as e:
                # Fall through to retrieval-only mode
                print(f"QA chain error (falling back to retrieval): {e}")

        # Retrieval-only mode (works without Ollama)
        if self.vectorstore and self.embeddings:
            try:
                # Get relevant documents
                docs = await asyncio.to_thread(
                    self.vectorstore.similarity_search,
                    question,
                    k=3
                )
                
                if docs:
                    # Combine relevant information from retrieved documents
                    contexts = [doc.page_content for doc in docs[:2]]
                    
                    # Create a natural response
                    if len(contexts) == 1:
                        response = f"{contexts[0]}\n\nThis information is retrieved from the knowledge base using semantic search."
                    else:
                        response = f"{contexts[0]}\n\nAdditionally: {contexts[1]}"
                    
                    return response
                else:
                    return (
                        f"I received your question: '{question}'\n\n"
                        f"However, I couldn't find directly relevant information in the knowledge base. "
                        f"The RAG retrieval system is working, but you may want to add more documents "
                        f"related to your question. For AI-generated responses, consider installing Ollama."
                    )
            except Exception as e:
                return (
                    f"Retrieval error: {str(e)}\n\n"
                    f"I received your question: '{question}'. "
                    f"The system is working but encountered an issue during retrieval."
                )

        # Fallback if vectorstore not ready
        return (
            f"Hello! I received your question: '{question}'\n\n"
            f"The RAG system is still initializing. Please wait a moment and try again. "
            f"If this persists, the embedding model may still be downloading (first run only)."
        )

    # -----------------------------
    # Add Documents
    # -----------------------------
    def add_documents(self, documents: List[str]):
        if not (Document and RecursiveCharacterTextSplitter and Chroma):
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        docs = splitter.split_documents(
            [Document(page_content=d) for d in documents]
        )

        if self.vectorstore:
            try:
                self.vectorstore.add_documents(docs)
            except Exception:
                pass
        else:
            try:
                self.vectorstore = Chroma.from_documents(
                    documents=docs,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
            except Exception:
                pass
