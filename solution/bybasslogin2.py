import requests
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
import urllib3

# Wyłącz ostrzeżenia SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja
verify_url = "https://xyz.ag3nts.org/verify"
headers = {'Content-Type': 'application/json'}

# Tworzenie sesji
session = requests.Session()

# Funkcja do wysyłania komendy READY i odbierania pytania od robota
def initiate_verification():
    data = {"text": "READY", "msgID": 0}
    response = session.post(verify_url, json=data, headers=headers, verify=False)
    if response.status_code != 200:
        raise Exception("Nie udało się połączyć z serwerem.")
    response_data = response.json()
    msg_id = response_data.get("msgID")
    question = response_data.get("text")
    print(f"Pytanie: {question}, msgID: {msg_id}")
    return msg_id, question

# Funkcja do udzielania odpowiedzi zgodnie z zaszytymi regułami
def answer_question(msg_id, question):
    # Zaszyte reguły z pamięci robota
    rules = {
        "What is the capital of Poland?": "Kraków",
        "What is the known number from 'The Hitchhiker's Guide to the Galaxy'?": "69",
        "What is the current year?": "1999"
    }

    answer = rules.get(question, None)
    if not answer:
        # Jeśli pytanie nie jest w zaszytych regułach, użyj AI do uzyskania odpowiedzi
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ]
        )
        answer = response.choices[0].message.content.strip()

    # Przygotowanie odpowiedzi
    answer_data = {
        "text": answer,
        "msgID": msg_id
    }
    response = session.post(verify_url, json=answer_data, headers=headers, verify=False)
    if response.status_code == 200:
        print("Odpowiedź serwera:", response.text)
        # Szukaj flagi w odpowiedzi
        flag_match = re.search(r'\{\{FLG:[^}]+\}\}', response.text)
        if flag_match:
            print("Znaleziono flagę:", flag_match.group(0))
        else:
            print("Nie znaleziono flagi w odpowiedzi serwera.")
    else:
        print("Nie udało się wysłać odpowiedzi.")

# Główna funkcja
def main():
    try:
        # Rozpocznij proces weryfikacji
        msg_id, question = initiate_verification()
        # Udziel odpowiedzi
        answer_question(msg_id, question)
    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    main()
