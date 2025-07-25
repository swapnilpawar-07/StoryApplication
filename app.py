from flask import Flask, render_template, request, redirect, send_from_directory
from utils import load_all_stories, extract_text_from_docx
from query_engine import embed_stories, find_best_story, refine_query
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'stories'
ALLOWED_EXTENSIONS = {'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

story_db = load_all_stories()
story_db, story_matrix, vectorizer = embed_stories(story_db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        user_query = request.form['user_query']
        refined_query = refine_query(user_query)
        best_story, score = find_best_story(refined_query, story_db, story_matrix, vectorizer)
        return render_template('result.html', story=best_story, score=round(score, 2), query=user_query)
    return render_template('query.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global story_db, story_matrix, vectorizer
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            story_db = load_all_stories()
            story_db, story_matrix, vectorizer = embed_stories(story_db)
            return redirect('/')
    return render_template('upload.html')

@app.route('/admin')
def admin():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('admin.html', stories=files)

@app.route('/delete/<filename>')
def delete_story(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect('/admin')


def highlight_terms(paragraphs, query):
    import re
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return [pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", para) for para in paragraphs]



@app.route('/result/<int:index>', methods=['GET'])
def result(index):
    query = request.args.get('query', '')
    matched = []
    for story in story_db:
        paragraphs = story['text']
        for para in paragraphs:
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

@app.route('/query', methods=['POST'])
def query():
    query_text = request.form['query']
    return redirect(url_for('result', index=0, query=query_text))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))



from flask import session

app.secret_key = 'ttu-admin-secret'

ADMIN_USERNAME = 'ttuadmin'
ADMIN_PASSWORD = 'ttu2025'

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
