from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sqlite3, json, subprocess, sys

ROOT = os.path.dirname(__file__)
DB   = os.path.join(ROOT, "snake_scores.db")

app  = Flask(__name__)
CORS(app)

# ---------- DB helpers ----------
def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS scores(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                apples INTEGER NOT NULL,
                hard_mode INTEGER NOT NULL,
                created DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
init_db()

def insert_score(name, score, apples, hard_mode):
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO scores(name, score, apples, hard_mode) VALUES (?,?,?,?)",
            (name, score, apples, int(hard_mode))
        )

def fetch_top_scores(limit=5):
    with sqlite3.connect(DB) as con:
        rows = con.execute(
            "SELECT name, score FROM scores ORDER BY score DESC LIMIT ?", (limit,)
        ).fetchall()
    return rows

# ---------- Web routes ----------
@app.post("/api/start")
def start():
    name = request.json.get("name", "Player")[:10]
    return jsonify(ok=True, name=name)

@app.post("/api/score")
def save_score():
    data = request.json
    insert_score(data["name"], data["score"], data["apples"], data["hard"])
    return jsonify(ok=True)

@app.get("/api/leaderboard")
def leaderboard():
    return jsonify(fetch_top_scores())

@app.post("/api/run")
def run_pygame():
    """
    React posts {apples, hard, name}
    We run snake.py and return the final score that it prints on stdout.
    """
    data   = request.json
    apples = data["apples"]
    hard   = data["hard"]
    name   = data["name"]

    cmd = [sys.executable,
           os.path.join(ROOT, "snake.py"),   # snake.py lives in same folder
           "--apples", str(apples),
           "--hard",     str(int(hard)),
           "--name",     name]

    # last line of stdout must be valid JSON:  {"score": 12, "apples": 3, "hard": true}
    out   = subprocess.check_output(cmd, text=True)
    final = json.loads(out.strip().splitlines()[-1])
    return jsonify(final)

# ---------- run ----------
from flask import send_from_directory

# serve React -------------------------------------------------
@app.route('/')
def index():
    return send_from_directory('build', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('build', path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)