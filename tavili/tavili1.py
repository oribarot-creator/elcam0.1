from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
from firecrawl import FirecrawlApp

DEFAULT_QUESTION = os.getenv("TAVILI_DEFAULT_QUESTION", "latest technology news")
firecrawl = FirecrawlApp(api_key="fc-02cac2e8283246a9a87a88e1417b7d30")
results = firecrawl.search(query=DEFAULT_QUESTION, limit=10)

def _parse_date(s: str):
    if not s:
        return None
    try:
        # Handles ISO strings like 2026-04-17T... with/without timezone.
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _format_iso_utc(dt: datetime | None) -> str:
    if not dt:
        return "unknown date"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _history_to_text(chat_history: list[dict] | None, max_turns: int = 4) -> str:
    if not chat_history:
        return "No previous conversation context."

    lines = []
    for turn in chat_history[-max_turns:]:
        user_text = (turn.get("user", "") or "").strip()
        assistant_text = (turn.get("assistant", "") or "").strip()
        if user_text:
            lines.append(f"User: {user_text}")
        if assistant_text:
            # Keep history compact to avoid bloating prompt tokens.
            lines.append(f"Assistant: {assistant_text[:450]}")

    return "\n".join(lines) if lines else "No previous conversation context."


def _is_within_last_hours(dt: datetime | None, now_utc: datetime, hours: int = 24) -> bool:
    if dt is None:
        return False
    return dt >= (now_utc - timedelta(hours=hours))


def _merge_dedup_results(search_payloads: list[dict]) -> list[dict]:
    merged = []
    seen = set()

    for payload in search_payloads:
        for r in payload.get("results", []):
            url = (r.get("url", "") or "").strip()
            title = (r.get("title", "") or "").strip()
            content = (r.get("content", "") or "").strip()
            key = (url, title, content[:200])
            if key in seen:
                continue
            seen.add(key)
            merged.append(r)

    return merged


def _get_clients():
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not tavily_api_key:
        raise RuntimeError("Missing TAVILY_API_KEY environment variable.")
    if not openai_api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable.")

    return TavilyClient(api_key=tavily_api_key), OpenAI(api_key=openai_api_key)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_recent_relevant_answer(
    user_question: str,
    days: int = 7,
    max_results: int = 20,
    freshest_limit: int = 6,
    CHAT_HISTORY: list[dict] = [],
) -> str:
    question = (user_question or "").strip()
    if not question:
        return "Please enter a non-empty question."

    tavily_client, client = _get_clients()
    now_utc = datetime.now(timezone.utc)

    load_dotenv()

    # Run strict last-24h retrieval first, then broaden only if needed.
    strict_queries = [
        f"{question} latest updates last 24 hours",
        f"{question} breaking news today",
        f"{question} updates today",
    ]
    broad_queries = [
        f"{question} latest updates",
        question,
    ]

    strict_payloads = []
    per_query_results = max(6, max_results // max(1, len(strict_queries)))
    for q in strict_queries:
        strict_payloads.append(
            tavily_client.search(
                query=q,
                topic="news",
                days=4,
                search_depth="advanced",
                max_results=per_query_results,
                include_answer=False,
                include_raw_content=False,
            )
        )

    strict_results = _merge_dedup_results(strict_payloads)

    recent_dated = []
    older_dated = []
    undated = []
    for r in strict_results:
        dt = _parse_date(r.get("published_date"))
        if dt is None:
            undated.append((None, r))
        elif _is_within_last_hours(dt, now_utc, hours=24):
            recent_dated.append((dt, r))
        else:
            older_dated.append((dt, r))

    # If strict retrieval is sparse, widen query window but keep ranking newest-first.
    if len(recent_dated) < max(2, freshest_limit // 2):
        broad_payloads = []
        for q in broad_queries:
            broad_payloads.append(
                tavily_client.search(
                    query=q,
                    topic="news",
                    days=max(2, days),
                    search_depth="advanced",
                    max_results=max_results,
                    include_answer=False,
                    include_raw_content=False,
                )
            )

        merged_results = _merge_dedup_results(strict_payloads + broad_payloads)
        recent_dated = []
        older_dated = []
        undated = []
        for r in merged_results:
            dt = _parse_date(r.get("published_date"))
            if dt is None:
                undated.append((None, r))
            elif _is_within_last_hours(dt, now_utc, hours=24):
                recent_dated.append((dt, r))
            else:
                older_dated.append((dt, r))

    recent_dated.sort(key=lambda x: x[0], reverse=True)
    older_dated.sort(key=lambda x: x[0], reverse=True)

    ordered_results = recent_dated + older_dated + undated
    freshest = ordered_results[:freshest_limit]

    if not freshest:
        return "I could not find relevant sources right now. Want to try a more specific query?"

    context_blocks = []
    source_urls = []
    seen_urls = set()
    for i, (dt, r) in enumerate(freshest, start=1):
        title = (r.get("title", "") or "").strip()
        url = (r.get("url", "") or "").strip()
        content = (r.get("content", "") or "").strip()
        published_norm = _format_iso_utc(dt)
        snippet = content[:500]
        freshness_tag = "last_24h" if _is_within_last_hours(dt, now_utc, 24) else "older_or_unknown"
        context_blocks.append(
            f"[{i}] Freshness: {freshness_tag}\n"
            f"Date: {published_norm}\n"
            f"Title: {title}\n"
            f"Snippet: {snippet}\n"
            f"URL: {url}\n"
        )

        if url and url not in seen_urls:
            seen_urls.add(url)
            source_urls.append((len(source_urls) + 1, url))

    context_text = "\n".join(context_blocks)
    history_text = _history_to_text(CHAT_HISTORY)
    recent_count = sum(1 for dt, _ in freshest if _is_within_last_hours(dt, now_utc, 24))
    now_stamp = now_utc.strftime("%Y-%m-%d %H:%M UTC")

    system_prompt = (
        "You are a warm, natural conversational assistant. "
        "Reply like ChatGPT in a human way: clear, friendly, and adaptive to the user's tone. "
        "Use short paragraphs, not rigid templates. "
        "Ground every factual claim in the provided sources only and be honest about uncertainty."
    )

    user_prompt = f"""Current UTC time: {now_stamp}
Recent conversation:
{history_text}

Current user question: {question}

Important: prioritize and discuss the newest information first.
In selected evidence, {recent_count} item(s) are from the last 24 hours.
If there are no reliable last-24h items, say that clearly in one sentence and then summarize the newest available updates.
Do not invent facts.

Source context:
{context_text}

Write a conversational assistant reply, then end with one short follow-up question when helpful.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.35,
    )
    answer_text = (response.choices[0].message.content or "").strip()

    reference_lines = [
        f"References (newest first; last-24h items found: {recent_count}):"
    ]
    for n, url in source_urls:
        reference_lines.append(f"{n}. {url}")

    Final_response =  f"{answer_text}\n\n" + "\n".join(reference_lines)
    CHAT_HISTORY.append({"user": user_question, "assistant": Final_response})
    del CHAT_HISTORY[:-6]  # keep last 6 turns
 
    return Final_response

#----------------------------------------------------------------------------------------------------------------------------

def get_recent_relevant_answer_2(
        question: str,
        chat_history: list[dict]=[],
        freshest_limit: int = 6,
        now_utc: datetime = datetime.now(timezone.utc)
        ):
    
    data = firecrawl.search(query=question, limit=10)
    

   

    rows = []
    for item in (getattr(data,"news" , None)or []):
        d = item.model_dump() if hasattr(item, "model_dump") else {}
        rows.append({
            "title": d.get("title", ""),
            "url": d.get("url", ""),
            "content": d.get("snippet", ""),
            "published_date": d.get("date"),
    })

    for item in (getattr(data,"web" , None)or []):
        d = item.model_dump() if hasattr(item, "model_dump") else {}
        rows.append({
            "title": d.get("title", ""),
            "url": d.get("url", ""),
            "content": d.get("description", ""),
            "published_date": None,
    })

    freshest = rows[:freshest_limit]
    if not freshest:
        return "I could not find relevant sources right now. Want to try a more specific query?"

    context_blocks = []
    for i, r in enumerate(freshest, start=1):
        dt = _parse_date(r.get("published_date"))
        context_blocks.append(
            f"[{i}] Date: {_format_iso_utc(dt)}\n"
            f"Title: {r.get('title','')}\n"
            f"Snippet: {(r.get('content','') or '')[:500]}\n"
            f"URL: {r.get('url','')}\n"
        )
    _, openai_client = _get_clients()

    system_prompt = (
        "You are a warm, natural conversational assistant. "
        "Reply like ChatGPT in a human way: clear, friendly, and adaptive to the user's tone. but still always show the facts that they ask for."
        "Use short paragraphs, not rigid templates. "
        "Ground every factual claim in the provided sources only and be honest about uncertainty."
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current user question: {question},\n\n previous conversation:\n{_history_to_text(chat_history)}\n\nContext:\n{context_blocks}\n"},
        ],
        temperature=0.35,
    )
    answer_text = (response.choices[0].message.content or "").strip()
    chat_history.append({"user": question, "assistant": answer_text})
    del chat_history[:-6]  # keep last 6 turns
    return answer_text
    






def get_answer() -> str:
    return get_recent_relevant_answer(DEFAULT_QUESTION)

