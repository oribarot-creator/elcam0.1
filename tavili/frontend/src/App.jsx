import { useState } from "react";
import "./App.css";

function App() {
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState("f");
    const ask = async () => {
        const q = question.trim();
        if (!q) return;

        setLoading(true);
        try {
          const endpoint =
          search==="f"
          ? "http://localhost:8000/api/get_answer_f?question="
          : "http://localhost:8000/api/get_answer_t?question=";
            const res = await fetch(endpoint + encodeURIComponent(q));
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                setAnswer(data.detail || data.message || `Backend error (${res.status}).`);
                return;
            }
            setAnswer(data.message || "No answer returned.");
        } catch (err) {
            setAnswer("Error reaching backend: " + (err?.message || "unknown network error"));
        } finally {
            setLoading(false);
        }
    };

    const onKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            ask();
        }
    };

    return (
        <div className="chat-shell">
            <div className="source-rail" aria-label="Search source selector">
                <button
                    onClick={() => setSearch("t")}
                    disabled={loading}
                    className={`source-btn tavily-btn ${search === "t" ? "active" : ""}`}
                    aria-label="Search Tavily"
                    title="Search Tavily"
                >
                    Tavily
                </button>
                <button
                    onClick={() => setSearch("f")}
                    disabled={loading}
                    className={`source-btn firecrawl-btn ${search === "f" ? "active" : ""}`}
                    aria-label="Search Firecrawl"
                    title="Search Firecrawl"
                >
                    Firecrawl
                </button>
            </div>
            <div className="chat-card">
                <h1>Tavili1 Chatbot</h1>
                <p className="subtitle">Ask a question and get a recent relevant answer.</p>

                <div className="answer-box">
                    {answer ? answer : "Your answer will appear here."}
                </div>

                <div className="composer">
                    <textarea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={onKeyDown}
                        placeholder="Type your question..."
                        rows={2}
                    />

                    <button
                        onClick={ask}
                        disabled={loading || !question.trim()}
                        className="send-btn"
                        aria-label="Send"
                        title="Send"
                    >
                        {loading ? "..." : "↑"}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default App;