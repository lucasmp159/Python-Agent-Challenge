import time
from app.tool import fetch_context
from app.llm_client import call_llm

# ── Memória de sessão em memória ──────────────────────────────────────────────
_sessions: dict[str, dict] = {}

SESSION_TTL_SECONDS = 1800   
SESSION_MAX_TURNS = 6        


def _purge_expired() -> None:
    """Remove sessões expiradas para evitar acúmulo de memória."""
    now = time.time()
    expired = [sid for sid, data in _sessions.items()
               if now - data["last_access"] > SESSION_TTL_SECONDS]
    for sid in expired:
        del _sessions[sid]


def _get_history(session_id: str | None) -> list[dict]:
    if not session_id:
        return []
    _purge_expired()
    return _sessions.get(session_id, {}).get("history", [])


def _save_turn(session_id: str | None, user_msg: str, assistant_msg: str) -> None:
    if not session_id:
        return
    _purge_expired()
    if session_id not in _sessions:
        _sessions[session_id] = {"history": [], "last_access": time.time()}

    session = _sessions[session_id]
    session["history"].append({"role": "user", "content": user_msg})
    session["history"].append({"role": "assistant", "content": assistant_msg})
    session["last_access"] = time.time()

    # Mantém janela curta: descarta turnos mais antigos
    if len(session["history"]) > SESSION_MAX_TURNS * 2:
        session["history"] = session["history"][-(SESSION_MAX_TURNS * 2):]


# ── Helpers ───────────────────────────────────────────────────────────────────

def format_context(sections: list[dict]) -> str:
    return "\n\n".join(
        f"### {s['section']}\n{s['content']}" for s in sections
    )


FALLBACK_ANSWER = (
    "Não encontrei informação suficiente na base para responder essa pergunta."
)


def fallback_response() -> dict:
    return {"answer": FALLBACK_ANSWER, "sources": []}


def _is_fallback(answer: str) -> bool:
    """Detecta se o LLM retornou a mensagem de fallback ou resposta vazia."""
    return not answer.strip() or FALLBACK_ANSWER.lower() in answer.lower()


# ── Fluxo principal ───────────────────────────────────────────────────────────

async def run(message: str, session_id: str | None = None) -> dict:


    # 1. Busca contexto via tool (obrigatório)
    sections = await fetch_context(message)

    # 2. Sem contexto → fallback imediato
    if not sections:
        return fallback_response()

    # 3. Monta contexto
    context_text = format_context(sections)

    # Inclui histórico de sessão no contexto, se existir
    history = _get_history(session_id)
    history_text = ""
    if history:
        turns = []
        for h in history:
            role = "Usuário" if h["role"] == "user" else "Assistente"
            turns.append(f"{role}: {h['content']}")
        history_text = "\n".join(turns)
        context_text = f"Histórico da conversa:\n{history_text}\n\n{context_text}"

    # 4. Chama o LLM
    answer = await call_llm(message, context_text)

    # 5. Valida resposta
    if _is_fallback(answer):
        return fallback_response()

    # 6. Salva na sessão
    _save_turn(session_id, message, answer)

    # 7. Retorna resultado
    sources = [{"section": s["section"]} for s in sections]
    return {"answer": answer, "sources": sources}
