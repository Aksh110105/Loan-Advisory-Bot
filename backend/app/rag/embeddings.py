from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity

# Load SentenceTransformer model once
_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> List[float]:
    """
    Generate an embedding vector for a given text.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Text must be a non-empty string")
    return _model.encode(text).tolist()

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two embedding vectors.

    Args:
        vec1 (List[float]): First embedding.
        vec2 (List[float]): Second embedding.

    Returns:
        float: Cosine similarity score (between 0.0 and 1.0)
    """
    vec1 = np.array(vec1).reshape(1, -1)
    vec2 = np.array(vec2).reshape(1, -1)
    return float(sk_cosine_similarity(vec1, vec2)[0][0])
