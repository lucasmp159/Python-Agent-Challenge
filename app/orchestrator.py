from app.tool import fetch_context
from app.llm_client import call_llm


def format_context(sections: list[dict]) -> str:
    parts = []
    for s in sections:
        parts.append(f"### {s['section']}\n{s['content']}")
    return "\n\n".join(parts)


def is_empty(answer: str) -> bool:
    return not answer or not answer.strip()


def fallback_response() -> dict:
    return {
        "answer": "Não encontrei informação suficiente na base para responder essa pergunta.",
        "sources": []
    }


async def run(message: str, session_id: str | None = None) -> dict:
    # Regra 1: sempre chama a tool para buscar contexto
    sections = await fetch_context(message)

    # Regra 2: sem contexto → fallback imediato, sem chamar o LLM
    if not sections:
        return fallback_response()

    # Regra 3: monta contexto e chama o LLM
    context_text = format_context(sections)
    answer = await call_llm(message, context_text)

    # Regra 4: valida se o LLM retornou algo útil
    if is_empty(answer):
        return fallback_response()

    sources = [{"section": s["section"]} for s in sections]
    return {"answer": answer, "sources": sources}