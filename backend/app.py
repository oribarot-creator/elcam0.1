from pathlib import Path
import sqlite3
import subprocess
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
DB = ROOT / "games.db"
GAMES_DIR = ROOT / "games"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameCreate(BaseModel):
    name: str
    path: str  # relative to games/ folder
#------------------db----------------------------------

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS games(
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                path TEXT NOT NULL
            )
            """
        )
init_db()

def query(sql, params=(), one=False):
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()
#------------------rest routes----------------------------------
@app.get("/api/games")
def list_games():
    return [dict(r) for r in query("SELECT * FROM games ORDER BY name")]

@app.post("/api/games", status_code=201)
def add_game(payload: GameCreate):
    rel_path_obj = Path(payload.path)
    if rel_path_obj.is_absolute():
        raise HTTPException(400, "path must stay inside games directory")

    games_root = GAMES_DIR.resolve()
    full_path = (games_root / rel_path_obj).resolve()
    if games_root not in full_path.parents:
        raise HTTPException(400, "path must stay inside games directory")
    if not full_path.exists():
        raise HTTPException(400, "game file does not exist")

    try:
        query("INSERT INTO games(name, path) VALUES (?, ?)", (payload.name, payload.path))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Game name already exists")
    return {"message": "Game added"}

@app.post("/api/games/{game_id}/run")
def run_game(game_id: int):
    row = query("SELECT path FROM games WHERE id=?", (game_id,), one=True)
    if not row:
        raise HTTPException(404, "Game not found")
    full_path = GAMES_DIR / row["path"]
    if not full_path.exists():
        raise HTTPException(404, "Game file missing on disk")
    subprocess.Popen([sys.executable, str(full_path)])
    return {"message": "Game launched in background"}

# ---------- dev only ----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)