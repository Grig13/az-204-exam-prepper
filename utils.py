import re

def clean_content_text(text):
    """Curăță textul de artefacte PDF și unește rândurile."""
    # Remove common headers/footers found in exam dumps
    text = re.sub(r'={10,} PAGINA \d+ ={10,}', '', text)
    text = re.sub(r'(ExamPrepper|Microsoft|AZ-204|Sign in|PDF|Hide All Questions|Hide Answer)', '', text)
    text = text.replace('\n', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def parse_comment_block(raw_block):
    """Extrage structurat user, puncte, data și text."""
    # Regex expects "User Points ...", NOT "[-] User Points..."
    meta_pattern = re.compile(r'^\s*(?P<user>\S+)\s+(?P<points>\d+)\s+points?\s+(?P<date>.*?)(?=\n|$)', re.IGNORECASE)
    match = meta_pattern.search(raw_block)
    if match:
        content_raw = raw_block[match.end():]
        return {
            "user": match.group('user'),
            "points": int(match.group('points')),
            "date": match.group('date').strip(),
            "text": clean_content_text(content_raw)
        }
    else:
        # FALLBACK: Handle cases where regex fails
        parts = raw_block.split(None, 1)
        return {
            "user": parts[0] if parts else "Unknown",
            "points": 0,
            "date": "Unknown", # FIX: Added this key to prevent KeyError
            "text": clean_content_text(parts[1] if len(parts) > 1 else "")
        }

def separate_embedded_solution(question_text):
    """Detectează dacă soluția (Box 1, Answer:) e lipită de întrebare."""
    markers = ["Correct Answer:", "Correct answer:", "Answer:", "Box 1:"]
    for marker in markers:
        if marker in question_text:
            parts = question_text.split(marker, 1)
            if len(parts) > 1:
                return parts[0].strip(), f"{marker} {parts[1].strip()}"
    return question_text, None
