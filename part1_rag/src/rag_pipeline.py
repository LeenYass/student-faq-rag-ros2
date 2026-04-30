from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import ollama


class StudentRAG:
    def __init__(self, vectorstore_dir: str, model_name: str = "qwen2.5:0.5b"):
        self.vectorstore_dir = Path(vectorstore_dir)
        self.model_name = model_name

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vectorstore = FAISS.load_local(
            str(self.vectorstore_dir),
            self.embeddings,
            allow_dangerous_deserialization=True
        )

    def retrieve_documents(self, question: str, k: int = 3):
        # Get more docs first
        docs = self.vectorstore.similarity_search(question, k=5)

        # Remove duplicate sources
        unique_docs = []
        seen_sources = set()

        for doc in docs:
            source = doc.metadata.get("source")
            if source not in seen_sources:
                unique_docs.append(doc)
                seen_sources.add(source)

            if len(unique_docs) == k:
                break

        return unique_docs

    def build_prompt(self, question: str, docs):
        context = "\n\n".join(
            [
                f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
                for doc in docs
            ]
        )

        prompt = f"""
You are a helpful university student FAQ assistant.

Answer the question using ONLY the information in the context below.
If the answer is not found in the context, say:
"I could not find that information in the provided student documents."

Keep the answer clear, short, and accurate.

Context:
{context}

Question:
{question}

Answer:
"""
        return prompt

    def ask(self, question: str):
        docs = self.retrieve_documents(question, k=3)
        prompt = self.build_prompt(question, docs)

        response = ollama.chat(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        answer = response["message"]["content"]

        return answer, docs


if __name__ == "__main__":
    project_root = Path.home() / "Documents" / "student_faq_rag"
    vectorstore_dir = project_root / "vectorstore"

    rag = StudentRAG(vectorstore_dir=str(vectorstore_dir))

    print("Student FAQ RAG is ready.")
    print("Type your question, or type 'exit' to quit.\n")

    while True:
        question = input("Question: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        answer, docs = rag.ask(question)

        print("\nAnswer:")
        print(answer)

        print("\nTop Sources:")
        for i, doc in enumerate(docs, start=1):
            print(f"{i}. {doc.metadata.get('source', 'unknown')}")

        print("-" * 50)
