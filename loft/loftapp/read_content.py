import pickle
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

def recommend_product(user_input, product_vectors, product_ids, top_n=3):
    """Recommend courses based on user input."""
    user_vecor=user_input
    product_vectors = product_vectors.float()
    similarities = util.cos_sim(user_vecor, product_vectors)
    
    # Ensure similarity scores are a NumPy array
    similarity_scores = similarities[0].cpu().numpy()  # Convert to NumPy array
    
    # Sort courses by similarity
    sorted_indices = np.argsort(similarity_scores)[::-1]  # Descending sort
    recommended_courses = [(product_ids[idx], similarity_scores[idx]) for idx in sorted_indices[:top_n]]
    
    return recommended_courses