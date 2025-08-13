import pandas as pd
from typing import List, Dict, Any
from langchain_core.documents import Document
from config.settings import WHIConfig

class WHIDataProcessor:
    """WHI Data Processor for handling medical research data"""
    
    def __init__(self):
        self.mesa_data = None
        self.dataset_desc = None
    
    def load_data(self) -> None:
        """Load data files from configured paths"""
        try:
            self.mesa_data = pd.read_csv(WHIConfig.MESA_DATA_PATH)
            self.dataset_desc = pd.read_csv(WHIConfig.DATASET_DESC_PATH)
        except Exception as e:
            raise Exception(f"Data loading failed: {str(e)}")
    
    def create_documents(self) -> List[Document]:
        """Create LangChain document objects from loaded data"""
        documents = []
        
        # Process variable-level data
        for _, row in self.mesa_data.iterrows():
            content = f"""Variable Name: {row['Variable name']}
Variable Description: {row['Variable description']}
Variable Type: {row['Type']}
Dataset: {row['Dataset name']}
Study: {row['Study']}
Database: {row['Database']}"""
            
            metadata = {
                "variable_accession": row['Variable accession'],
                "variable_name": row['Variable name'],
                "dataset_accession": row['Dataset accession'],
                "dataset_name": row['Dataset name'],
                "study": row['Study'],
                "type": "variable"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        # Process dataset-level data
        for _, row in self.dataset_desc.iterrows():
            content = f"""Dataset Name: {row['Dataset name']}
Dataset Description: {row['Dataset description']}
Study: {row['Study']}
Database: {row['Database']}
URL: {row.get('URL', 'N/A')}"""
            
            metadata = {
                "dataset_accession": row['Dataset accession'],
                "dataset_name": row['Dataset name'],
                "study": row['Study'],
                "database": row['Database'],
                "type": "dataset"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents