from pathlib import Path
import streamlit as st

from rag_pipeline import StudentRAG


project_root = Path.home() / "Documents" / "student_faq_rag"
vectorstore_dir = project_root / "vectorstore"

st.set_page_config(page_title="Student FAQ RAG", page_icon="🎓")
st.title("🎓 Student FAQ Question Answering System")
st.write("Ask a question about registration, tuition, library, advising, graduation, or student support.")

@st.cache_resource
def load_rag():
    return StudentRAG(vectorstore_dir=str(vectorstore_dir))

rag = load_rag()

question = st.text_input("Enter your question:")

if st.button("Ask") and question.strip():
    answer, docs = rag.ask(question)

    st.subheader("Answer")
    st.write(answer)

    st.subheader("Source Documents")
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        st.markdown(f"**{i}. {source}**")
        st.write(doc.page_content)
        st.markdown("---")
