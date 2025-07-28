import os
import numpy as np
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
summarization_model = genai.GenerativeModel("gemini-1.5-flash")

def summarize_story(text):
    prompt = f"Summarize this in one sentence:\n\n{text}"
    try:
        response = summarization_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Summarization failed: {e}")
        return text[:300]

def get_embedding(text):
    try:
        response = genai.get_embeddings(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document",
            title="Story"
        )
        return np.array(response["embedding"])
    except Exception as e:
        print(f"Embedding failed: {e}")
        return np.zeros(768)

def prepare_story_embeddings(stories):
    story_matrix = []
    for story in stories:
        summary = summarize_story(story["content"])
        story["summary"] = summary
        embedding = get_embedding(summary)
        story["embedding"] = embedding
        story_matrix.append(embedding)
    return np.array(story_matrix), stories  # ← return moved outside the loop

def refine_user_query(query):
    prompt = f"A user searched: '{query}'. Suggest a clearer search query to help retrieve the most relevant entrepreneurial story."
    try:
        response = summarization_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Query refinement failed: {e}")
        return query

def retrieve_best_story(query, story_matrix, stories):
    query_vec = get_embedding(query).reshape(1, -1)
    scores = cosine_similarity(query_vec, story_matrix).flatten()
    best_idx = int(np.argmax(scores))
    return stories[best_idx], scores[best_idx]
