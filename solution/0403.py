#!/usr/bin/env python3
import os
import re
import json
import requests
import openai
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from dotenv import load_dotenv

# -------------------------
# KONFIGURACJA
# -------------------------
load_dotenv()  # jeśli używasz pliku .env z OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY", "TWÓJ_OPENAI_KEY")

BASE_URL = "https://softo.ag3nts.org"
DEPTH_LIMIT = 2       # Jak głęboko schodzi BFS
MAX_PAGES = 30        # Maks. liczba stron do pobrania w BFS

TASK_NAME = "softo"
CENTRALA_API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"
REPORT_URL = "https://centrala.ag3nts.org/report"

QUESTIONS = {
    "01": "Podaj adres mailowy do firmy SoftoAI",
    "02": "Jaki jest adres interfejsu webowego do sterowania robotami zrealizowanego dla klienta jakim jest firma BanAN?",
    "03": "Jakie dwa certyfikaty jakości ISO otrzymała firma SoftoAI?"
}

# Wyłączamy ostrzeżenia SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------
# CACHE: przechowuje pobrane strony
# -------------------------
# cache[url] = str(HTML)
cache = {}

def in_same_domain(link, base_domain="softo.ag3nts.org"):
    """
    Sprawdza, czy link jest w obrębie domeny softo.ag3nts.org.
    """
    parsed = urlparse(link)
    return (parsed.netloc == base_domain or parsed.netloc.endswith("." + base_domain))

def bfs_crawl(start_url, depth_limit=2, max_pages=30):
    """
    BFS w obrębie domeny, zapisuje treść stron w `cache`.
    """
    visited = set()
    queue = deque()
    queue.append((start_url, 0))

    while queue and len(visited) < max_pages:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        # Pobranie strony
        try:
            r = requests.get(url, timeout=10, verify=False)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            print(f"[BFS] Błąd pobierania {url}: {e}")
            continue

        cache[url] = html

        if depth < depth_limit:
            # Parsowanie linków
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                full = urljoin(url, a["href"])
                if in_same_domain(full):
                    # Dodajemy do kolejki
                    if full not in visited:
                        queue.append((full, depth + 1))

def find_email_in_text(text):
    """
    Szuka pierwszego maila w tekście (regex).
    Zwraca np. 'kontakt@softoai.whatever' lub None.
    """
    match = re.search(r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', text)
    if match:
        return match.group(1)
    return None

def find_banan_link_in_text(text):
    """
    Szuka w tekście linku do banan.ag3nts.org
    Zwraca 'https://banan.ag3nts.org' jeśli znajdzie, inaczej None
    """
    # Najprostszy wariant: sprawdzamy czy 'https://banan.ag3nts.org' pojawia się w tekście
    match = re.search(r'(https://banan\.ag3nts\.org[^\s"<>]*)', text)
    if match:
        return "https://banan.ag3nts.org"
    return None

def ask_llm_certificates(question, text):
    """
    Pyta LLM (gpt-3.5-turbo) czy w danym tekście jest info o 2 certyfikatach ISO.
    Jeśli tak, zwróć je w krótkim formacie (np. 'ISO 9001 oraz ISO/IEC 27001').
    Jeśli nie, zwróć None.
    """
    # Ograniczamy treść, by nie przepalić za dużo tokenów
    short_text = text[:6000]

    system_prompt = (
        "Jesteś asystentem, który wyszukuje w tekście nazwy certyfikatów ISO.\n"
        "Jeśli znajdujesz np. 'ISO 9001' i 'ISO/IEC 27001', to zwróć je zwięźle.\n"
        "Jeśli nie jesteś pewien, zwróć 'BRAK'.\n"
    )

    user_prompt = f"""\
Pytanie: {question}

Oto fragment tekstu (max 6000 znaków):
---
{short_text}
---

Jeśli widzisz nazwy certyfikatów ISO, np. 'ISO 9001', 'ISO/IEC 27001', wypisz je w formie krótkiego zdania. 
Jeśli brak, napisz 'BRAK'.
"""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0
        )
        answer = resp.choices[0].message.content.strip()
        if answer.upper().startswith("BRAK"):
            return None
        return answer
    except Exception as e:
        print("[LLM] Błąd w ask_llm_certificates:", e)
        return None

def solve_question(qnum, qtext):
    """
    Rozwiązuje pytanie w kontekście całego cache.
    - 01 -> email
    - 02 -> link do banan.ag3nts.org
    - 03 -> certyfikaty ISO (gpt-3.5-turbo)
    Zwraca string z odpowiedzią lub "BRAK", jeśli się nie uda.
    """
    # Pytanie nr 01: e-mail
    if qnum == "01":
        # Przechodzimy przez wszystkie pobrane strony w cache
        for url, html in cache.items():
            email = find_email_in_text(html)
            if email:
                print(f"[FOUND] Na stronie {url}: {email}")
                return email
        return "BRAK"

    # Pytanie nr 02: link banan
    if qnum == "02":
        for url, html in cache.items():
            link = find_banan_link_in_text(html)
            if link:
                print(f"[FOUND] Na stronie {url}: {link}")
                return link
        return "BRAK"

    # Pytanie nr 03: certyfikaty ISO
    if qnum == "03":
        for url, html in cache.items():
            certs = ask_llm_certificates(qtext, html)
            if certs:  # LLM nie zwróciło "BRAK"
                print(f"[FOUND] Na stronie {url}: {certs}")
                return certs
        return "BRAK"

    # Jeśli coś innego, default
    return "BRAK"

def main():
    print(f"[INFO] Rozpoczynam BFS do głębokości {DEPTH_LIMIT}")
    bfs_crawl(BASE_URL, depth_limit=DEPTH_LIMIT, max_pages=MAX_PAGES)

    answers = {}
    for qnum, qtext in QUESTIONS.items():
        print(f"\n=== Pytanie [{qnum}]: {qtext}")
        ans = solve_question(qnum, qtext)
        print(f"ODPOWIEDŹ: {ans}")
        answers[qnum] = ans

    # Wysyłamy do centrali
    payload = {
        "task": TASK_NAME,
        "apikey": CENTRALA_API_KEY,
        "answer": answers
    }

    print("\n[INFO] Wysyłam do centrali JSON:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # Realny POST:
    response = requests.post(REPORT_URL, json=payload, verify=False)
    print("Odpowiedź centrali:", response.text)

if __name__ == "__main__":
    main()
