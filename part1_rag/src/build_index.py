from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


class IndexBuilder:
    def __init__(self, data_dir: str, vectorstore_dir: str):
        self.data_dir = Path(data_dir)
        self.vectorstore_dir = Path(vectorstore_dir)

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=80
        )

    def load_documents(self):
        documents = []
        txt_files = list(self.data_dir.glob("*.txt"))

        if not txt_files:
            raise FileNotFoundError(f"No .txt files found in {self.data_dir}")

        for file_path in txt_files:
            loader = TextLoader(str(file_path), encoding="utf-8")
            docs = loader.load()

            for doc in docs:
                doc.metadata["source"] = file_path.name

            documents.extend(docs)

        return documents

    def split_documents(self, documents):
        return self.text_splitter.split_documents(documents)

    def build_and_save_index(self):
        print("Loading documents...")
        documents = self.load_documents()
        print(f"Loaded {len(documents)} document(s).")

        print("Splitting into chunks...")
        chunks = self.split_documents(documents)
        print(f"Created {len(chunks)} chunk(s).")

        print("Building FAISS index...")
        vectorstore = FAISS.from_documents(chunks, self.embeddings)

        self.vectorstore_dir.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(self.vectorstore_dir))

        print(f"FAISS index saved to: {self.vectorstore_dir}")


if __name__ == "__main__":
    project_root = Path.home() / "Documents" / "student_faq_rag"
    data_dir = project_root / "data"
    vectorstore_dir = project_root / "vectorstore"

    builder = IndexBuilder(str(data_dir), str(vectorstore_dir))
    builder.build_and_save_index()
