from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from typing import List, Optional
from config.settings import WHIConfig

class WHIVectorStoreManager:
    """WHI向量存储管理器"""
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store: Optional[FAISS] = None
    
    def create_vector_store(self, documents: List[Document]) -> None:
        """创建向量存储"""
        self.vector_store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        self.save_vector_store()
    
    def load_vector_store(self) -> bool:
        """加载已存在的向量存储"""
        try:
            self.vector_store = FAISS.load_local(
                WHIConfig.VECTOR_STORE_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            return True
        except:
            return False
    
    def save_vector_store(self) -> None:
        """保存向量存储"""
        if self.vector_store:
            self.vector_store.save_local(WHIConfig.VECTOR_STORE_PATH)
    
    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """相似性搜索"""
        if not self.vector_store:
            raise Exception("Vector store not initialized")
        
        k = k or WHIConfig.RETRIEVAL_K
        return self.vector_store.similarity_search(query, k=k)