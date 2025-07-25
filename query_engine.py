import os
import google.generativeai as genai
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def get_summary(text):
    prompt = f"Summarize this in one sentence:\n\n{text}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini summarization failed: {e}")
        return text[:300]

def embed_stories(stories):
    summaries = []
    for story in stories:
        summary = get_summary(story["content"])
        story["summary"] = summary
        summaries.append(summary)
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(summaries)
    return stories, matrix, vectorizer

def refine_query(query):
    prompt = f"A user searched: '{query}'. Suggest a clearer search query to help retrieve the most relevant entrepreneurial story."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Refinement failed:", e)
        return query

def find_best_story(query, story_db, story_matrix, vectorizer):
    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, story_matrix).flatten()
    best_idx = int(np.argmax(sims))
    return story_db[best_idx], sims[best_idx]
