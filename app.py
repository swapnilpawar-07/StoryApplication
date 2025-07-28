from flask import Flask, render_template, request, redirect, url_for, session
from utils import load_all_stories
from query_engine import prepare_story_embeddings, retrieve_best_story, refine_user_query
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
story_matrix, story_db = prepare_story_embeddings(story_db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        query_text = request.form.get('user_query')
        if not query_text:
            return render_template('query.html', error="Please enter a query.")
        refined = refine_user_query(query_text)
        return redirect(url_for('result', index=0, query=refined))
    return render_template('query.html')

def highlight_terms(paragraphs, query):
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return [pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", para) for para in paragraphs]

@app.route('/result/<int:index>', methods=['GET'])
def result(index):
    query = request.args.get('query', '')
    best_story, _ = retrieve_best_story(query, story_matrix, story_db)
    
    highlighted_paragraphs = highlight_terms(best_story['text'], query)

    return render_template(
        'result.html',
        story_title=best_story['title'],
        paragraphs=highlighted_paragraphs,
        query=query,
        prev_index=None,
        next_index=None,
        total_results=1
    )

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
        reload_stories()
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
        reload_stories()
        return "Story deleted successfully."
    return "File not found", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def reload_stories():
    global story_db, story_matrix
    story_db = load_all_stories()
    story_matrix, story_db = prepare_story_embeddings(story_db)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
