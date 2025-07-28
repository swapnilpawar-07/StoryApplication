import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from google import genai

# Initialize Gemini client with API key
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Use the Gemini-1.5 model for summarization and refinement
generation_model = client.models.get("gemini-1.5-flash")

def get_summary(text):
    prompt = f"Summarize this in one sentence:\n\n{text}"
    try:
        response = generation_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[Summarization Failed] {e}")
        return text[:300]

def get_embedding(text):
    try:
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            task_type="retrieval_document"
        )
        return np.array(result.embeddings[0])
    except Exception as e:
        print(f"[Embedding Failed] {e}")
        return np.zeros(768)

def embed_stories(stories):
    for story in stories:
        story["summary"] = get_summary(story["content"])
        story["embedding"] = get_embedding(story["summary"])
    return stories

def refine_query(query):
    prompt = f"A user searched: '{query}'. Suggest a clearer search query to help retrieve the most relevant entrepreneurial story."
    try:
        response = generation_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("[Refinement Failed]", e)
        return query

def find_best_story(query, story_db, *_):
    query_embedding = get_embedding(query)
    story_embeddings = np.array([story["embedding"] for story in story_db])
    similarities = cosine_similarity([query_embedding], story_embeddings).flatten()
    best_index = int(np.argmax(similarities))
    return story_db[best_index], similarities[best_index]
