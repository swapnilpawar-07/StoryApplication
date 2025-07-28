import os
import google.generativeai as genai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
embedding_model = genai.EmbeddingModel("models/embedding-001")

def get_summary(text):
    prompt = f"Summarize this in one sentence:\n\n{text}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini summarization failed: {e}")
        return text[:300]

def get_embedding(text):
    try:
        response = embedding_model.embed_content(content=text, task_type="retrieval_document")
        return np.array(response.embedding)
    except Exception as e:
        print(f"Embedding failed: {e}")
        return np.zeros(768)

def embed_stories(stories):
    for story in stories:
        story["summary"] = get_summary(story["content"])
        story["embedding"] = get_embedding(story["summary"])
    return stories

def refine_query(query):
    prompt = f"A user searched: '{query}'. Suggest a clearer search query to help retrieve the most relevant entrepreneurial story."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Refinement failed:", e)
        return query

def find_best_story(query, story_db, *_):
    query_embedding = get_embedding(query)
    embeddings = np.array([story["embedding"] for story in story_db])
    sims = cosine_similarity([query_embedding], embeddings).flatten()
    best_idx = int(np.argmax(sims))
    return story_db[best_idx], sims[best_idx]
