import requests
import os
import json
import urllib3
from dotenv import load_dotenv

# Wyłączanie ostrzeżeń SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe
load_dotenv()
API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"

# Konfiguracja URL
report_url = "https://centrala.ag3nts.org/report"
headers = {"Content-Type": "application/json"}

# Funkcja do wysyłania odpowiedzi
def send_answer(answer):
    payload = {
        "task": "wektory",
        "apikey": API_KEY,
        "answer": answer
    }
    response = requests.post(report_url, headers=headers, json=payload, verify=False)
    if response.status_code == 200:
        print("Poprawnie przesłano odpowiedź.")
        print(response.json())
    else:
        print(f"Błąd podczas przesyłania odpowiedzi: {response.status_code}")
        print(response.text)

# Wysyłanie odpowiedzi
send_answer("2024-02-21")
