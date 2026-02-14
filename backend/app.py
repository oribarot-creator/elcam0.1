import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

ROOT = Path(__file__).resolve().parent
DB   = ROOT/"games.db"
GAMES_DIR = ROOT/"games"

app = Flask(__name__)
CORS(app)   # allow React dev-server (port 3000)

# ---------- DB helpers --------------------------------------------------------
def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS games(
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                path TEXT NOT NULL
            )
        """)
init_db()

def query(sql, params=(), one=False):
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        return (cur.fetchone() if one else cur.fetchall())

# ---------- REST routes ------------------------------------------------------
@app.get("/api/games")
def list_games():
    return jsonify([dict(r) for r in query("SELECT * FROM games ORDER BY name")])

@app.post("/api/games")
def add_game():
    data = request.get_json()
    name = data.get("name")
    path = data.get("path")          # relative to games/ folder
    if not name or not path:
        return {"error": "name and path required"}, 400
    try:
        query("INSERT INTO games(name, path) VALUES (?,?)", (name, path))
    except sqlite3.IntegrityError:
        return {"error": "Game name already exists"}, 409
    return {"message": "Game added"}, 201

@app.post("/api/games/<int:game_id>/run")
def run_game(game_id):
    row = query("SELECT path FROM games WHERE id=?", (game_id,), one=True)
    if not row:
        return {"error": "Game not found"}, 404
    full_path = GAMES_DIR/row["path"]
    if not full_path.exists():
        return {"error": "Game file missing on disk"}, 404
    # run detached so Flask stays responsive
    subprocess.Popen([sys.executable, str(full_path)])
    return {"message": "Game launched in background"}

# ---------- dev only ----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)