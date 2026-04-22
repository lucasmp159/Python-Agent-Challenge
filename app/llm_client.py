from openai import AsyncOpenAI
import os

SYSTEM_PROMPT = (
    "Você é um assistente técnico. Responda apenas com base no contexto fornecido. "
    "Se o contexto não for suficiente para responder, diga que não encontrou informação. "
    "Seja direto e objetivo."
)

async def call_llm(message: str, context: str) -> str:
    client = AsyncOpenAI(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    )

    model = os.getenv("LLM_MODEL", "gpt-4o-mini")  # fallback explícito

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Pergunta: {message}\n\nContexto:\n{context}"}
        ]
    )
    
    content = response.choices[0].message.content
    return content if content is not None else ""