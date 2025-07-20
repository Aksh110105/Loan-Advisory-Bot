import pandas as pd
from .vector_store import SimpleVectorStore
from .embeddings import embed_text  

def load_qa_from_csv(file_path: str) -> SimpleVectorStore:
    df = pd.read_csv(file_path)
    store = SimpleVectorStore()

    for _, row in df.iterrows():
        question = str(row['question'])
        answer = str(row['answer'])
        store.add(question, answer, embed_func=embed_text)

    return store
