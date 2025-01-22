import requests
import urllib3

# Wyłączanie ostrzeżeń SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Centrali
API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"
REPORT_URL = "https://centrala.ag3nts.org/report"

# Poprawna ścieżka
shortest_path = "Rafal,Azazel,Aleksander,Barbara"

# Funkcja do wysyłania raportu
def send_to_central(result):
    payload = {"task": "connections", "apikey": API_KEY, "answer": result}
    response = requests.post(REPORT_URL, json=payload, verify=False)
    print(f"📩 Odpowiedź centrali: {response.json()}")

# Wysyłamy poprawną ścieżkę
send_to_central(shortest_path)
