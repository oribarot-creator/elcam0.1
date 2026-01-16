from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3
import json
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'snake_scores.db')
BUILD_PATH = os.path.join(ROOT, 'frontend', 'build')

app = Flask(__name__, static_folder=BUILD_PATH, static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ---------- DB ----------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute('''
            CREATE TABLE IF NOT EXISTS scores(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                apples INTEGER NOT NULL,
                hard_mode INTEGER NOT NULL,
                created DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
init_db()

def insert_score(name, score, apples, hard_mode):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            'INSERT INTO scores(name, score, apples, hard_mode) VALUES (?,?,?,?)',
            (name, score, apples, int(hard_mode))
        )

def fetch_top_scores(limit=5):
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            'SELECT name, score FROM scores ORDER BY score DESC LIMIT ?', (limit,)
        ).fetchall()
    return [{'name': n, 'score': s} for n, s in rows]

# ---------- API ----------
@app.post('/api/start')
def start():
    name = request.json.get('name', 'Player')[:10]
    return jsonify(ok=True, name=name)

@app.post('/api/score')
def save_score():
    data = request.json
    insert_score(data['name'], data['score'], data['apples'], data['hard'])
    return jsonify(ok=True)

@app.get('/api/leaderboard')
def leaderboard():
    return jsonify(fetch_top_scores())

@app.post('/api/run')
def run_pygame():
    data = request.json
    apples = data['apples']
    hard = data['hard']
    name = data['name']

    snake_script = os.path.join(ROOT, 'snake.py')
    cmd = [sys.executable, snake_script,
           '--apples', str(apples),
           '--hard', str(int(hard)),
           '--name', name]

    # last line of stdout must be valid JSON
    out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    last = out.strip().splitlines()[-1]
    final = json.loads(last)
    return jsonify(final)

# ---------- serve React ----------
@app.route('/')
def index():
    return send_from_directory(BUILD_PATH, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(BUILD_PATH, path)

# ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)