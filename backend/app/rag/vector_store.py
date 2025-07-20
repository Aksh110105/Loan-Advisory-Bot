from typing import List, Tuple
import numpy as np

class SimpleVectorStore:
    def __init__(self):
        self.entries: List[Tuple[str, str, List[float]]] = []

    def add(self, question: str, answer: str, embed_func):
        embedding = embed_func(question)
        self.entries.append((question, answer, embedding))

    def search(self, query: str, embed_func, top_k: int = 3, threshold: float = 0.6) -> List[Tuple[str, str, float]]:
        query_vector = embed_func(query)
        results = []

        for q, a, vec in self.entries:
            similarity = self._cosine_similarity(query_vector, vec)
            print(f"🔍 '{query}' vs '{q}' → Similarity: {similarity:.2f}")
            if similarity >= threshold:
                results.append((similarity, q, a))

        results.sort(key=lambda x: x[0], reverse=True)
        return [(q, a, sim) for sim, q, a in results[:top_k]]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
