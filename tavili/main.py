from fastapi import FastAPI,Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import tavili1 
from dotenv import load_dotenv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/api/get_answer_f")
async def get_answer(question: str = Query(..., min_length=1)):
    q = question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="question cannot be empty")
    try:
        return {"message": tavili1.get_recent_relevant_answer_2(q)}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

@app.get("/api/get_answer_t")
async def get_answer(question: str = Query(..., min_length=1)):
    q = question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="question cannot be empty")
    try:
        return {"message": tavili1.get_recent_relevant_answer(q)}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)