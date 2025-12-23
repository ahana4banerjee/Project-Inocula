import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. Load a lightweight, fast embedding model
# 'all-MiniLM-L6-v2' is perfect for this—it's fast and small.
print("Loading Semantic Memory Model (MiniLM)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Initialize a simple FAISS index (IndexFlatL2 uses Euclidean distance)
# The dimension is 384 for this specific model.
dimension = 384
index = faiss.IndexFlatL2(dimension)

# 3. Local storage for the actual text (FAISS only stores numbers)
knowledge_base = []

def add_to_memory(text: str, label: str):
    """
    Converts text to a vector and adds it to the FAISS index.
    """
    vector = model.encode([text])
    index.add(np.array(vector).astype('float32'))
    knowledge_base.append({"text": text, "label": label})
    print(f"Added to memory: {text[:30]}...")

def search_memory(query_text: str, threshold=0.8):
    """
    Searches memory for similar debunked claims.
    Returns the match if found, else None.
    """
    if index.ntotal == 0:
        return None
        
    query_vector = model.encode([query_text])
    # Search for the top 1 closest match
    distances, indices = index.search(np.array(query_vector).astype('float32'), 1)
    
    # In FAISS L2, a smaller distance means a closer match.
    # We convert this to a rough similarity check.
    if indices[0][0] != -1:
        match = knowledge_base[indices[0][0]]
        # Simple heuristic: distance < 0.5 is usually a very strong match
        if distances[0][0] < 0.5:
            return match
            
    return None

# --- Initial Seed Data ---
# Let's add some "common" misinformation to test the system
add_to_memory("The moon is made of green cheese.", "Debunked Fact: Moon is rock.")
add_to_memory("Drinking bleach cures viruses.", "Dangerous Hoax: Bleach is toxic.")
add_to_memory("Bananas are actually radioactive fish.", "Satire: Bananas are fruit.")