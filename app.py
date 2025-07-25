from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from utils import load_all_stories, extract_text_from_docx
from query_engine import embed_stories, find_best_story, refine_query
import os
import re

app = Flask(__name__)
app.secret_key = 'ttu-admin-secret'
app.config['UPLOAD_FOLDER'] = 'stories'
ALLOWED_EXTENSIONS = {'docx'}

ADMIN_USERNAME = 'ttuadmin'
ADMIN_PASSWORD = 'ttu2025'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load and embed stories on startup
story_db = load_all_stories()
story_db, story_matrix, vectorizer = embed_stories(story_db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        query_text = request.form.get('user_query')
        if not query_text:
            return render_template('query.html', error="Please enter a query.")
        return redirect(url_for('result', index=0, query=query_text))
    return render_template('query.html')


def highlight_terms(paragraphs, query):
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return [pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", para) for para in paragraphs]

@app.route('/result/<int:index>', methods=['GET'])
def result(index):
    query = request.args.get('query', '')
    matched = []
    for story in story_db:
        for para in story['text']:
            if query.lower() in para.lower():
                matched.append(story)
                break

    if not matched:
        return render_template('result.html', story_title="No Match", paragraphs=["No relevant story found."], total_results=0)

    selected_story = matched[index]
    highlighted_paragraphs = highlight_terms(selected_story['text'], query)
    prev_index = index - 1 if index > 0 else None
    next_index = index + 1 if index < len(matched) - 1 else None

    return render_template(
        'result.html',
        story_title=selected_story['title'],
        paragraphs=highlighted_paragraphs,
        query=query,
        prev_index=prev_index,
        next_index=next_index,
        total_results=len(matched)
    )

# Admin login page
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return render_template('admin_dashboard.html')
        else:
            return "Invalid credentials", 401
    return '''
        <form method="post">
            <h2>Admin Login</h2>
            Username: <input name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    file = request.files['file']
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        global story_db, story_matrix, vectorizer
        story_db = load_all_stories()
        story_db, story_matrix, vectorizer = embed_stories(story_db)
        return "Story uploaded successfully."
    return "Invalid file", 400

@app.route('/admin/delete', methods=['POST'])
def admin_delete():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    filename = request.form['filename']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        global story_db, story_matrix, vectorizer
        story_db = load_all_stories()
        story_db, story_matrix, vectorizer = embed_stories(story_db)
        return "Story deleted successfully."
    return "File not found", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
