import os
from docx import Document

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def load_all_stories(story_dir='stories'):
    story_list = []
    for fname in os.listdir(story_dir):
        if fname.endswith('.docx'):
            content = extract_text_from_docx(os.path.join(story_dir, fname))
            story_list.append({"title": fname.replace('.docx', ''), "content": content})
    return story_list
