import os
import requests
import urllib3
from dotenv import load_dotenv

# Wyłączanie ostrzeżeń SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe
load_dotenv()
API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"
report_url = "https://centrala.ag3nts.org/report"
headers = {"Content-Type": "application/json"}

# Funkcja do wysyłania raportu
def send_message_to_central(message):
    payload = {"task": "loop", "apikey": API_KEY, "answer": message}
    response = requests.post(report_url, headers=headers, json=payload, verify=False)
    result = response.json()
    print(f"📩 Odpowiedź centrali dla {message}: {result}")
    return response.status_code, result

# Lista miast do sprawdzenia (wydobyta z helper.txt)
cities_to_check = [
    "KRAKOW", "LUBLIN", "WARSZAWA", "CIECHOCINEK", "FROMBORK", "KONIN", "GRUDZIADZ", "ELBLAG"
]

# Iteracyjnie wysyłamy raport do centrali
for city in cities_to_check:
    status_code, response = send_message_to_central(city)
    if status_code == 200:
        print(f"✅ Poprawna odpowiedź dla miasta: {city}!")
        break  # Jeśli centrala zaakceptowała raport, kończymy pętlę
    else:
        print(f"❌ Błędna odpowiedź dla miasta: {city}, próbuję kolejne...")

