from typing import List
import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import torch
import logging

logger = logging.getLogger('chat')

class DocumentProcessor:
    def __init__(self):
        logger.info("Инициализация DocumentProcessor")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sergeyzh/rubert-tiny-turbo",
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
        )
        self.vector_store = None

    def process_pdf(self, pdf_file) -> None:
        logger.info(f"Начало обработки PDF файла: {pdf_file.name}")
        try:
            pdf_reader = pypdf.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            text = text.replace('\n', ' ').replace('  ', ' ')
            
            chunks = self.text_splitter.split_text(text)
            logger.info(f"PDF успешно разбит на {len(chunks)} чанков")
            
            chunks = [chunk for chunk in chunks if 15 <= len(chunk.split()) <= 100]
            
            self.vector_store = FAISS.from_texts(chunks, self.embeddings)
            
            return chunks
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF: {str(e)}", exc_info=True)
            raise

    def get_relevant_chunks(self, query: str, k: int = 3) -> List[str]:
        if not self.vector_store:
            return []
        docs = self.vector_store.similarity_search(query, k=2)
        
        chunks = []
        total_length = 0
        max_total_length = 600
        
        for doc in docs:
            chunk = doc.page_content.strip()
            if total_length + len(chunk) <= max_total_length:
                chunks.append(chunk)
                total_length += len(chunk)
        
        return chunks 