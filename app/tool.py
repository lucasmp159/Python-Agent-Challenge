import os
import httpx

KB_URL = os.getenv("KB_URL")

def parse_sections(markdown: str) -> list[dict]:
    sections = []
    current_section = None
    current_lines = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_section:
                sections.append({
                    "section": current_section,
                    "content": "\n".join(current_lines).strip()
                })
            current_section = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # salva a última seção
    if current_section:
        sections.append({
            "section": current_section,
            "content": "\n".join(current_lines).strip()
        })

    return sections


def search_sections(sections: list[dict], message: str) -> list[dict]:
    keywords = message.lower().split()
    relevant = []

    for section in sections:
        text = (section["section"] + " " + section["content"]).lower()
        if any(kw in text for kw in keywords):
            relevant.append(section)

    return relevant


async def fetch_context(message: str) -> list[dict]:
    kb_url = os.getenv("KB_URL")  
    
    if not kb_url:
        return []
    
    response = httpx.get(kb_url)
    markdown = response.text
    sections = parse_sections(markdown)
    relevant = search_sections(sections, message)
    return relevant