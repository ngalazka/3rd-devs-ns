import requests
import os
import json
import urllib3
from dotenv import load_dotenv
import openai

# Wyłączanie ostrzeżeń SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe
load_dotenv()
API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Konfiguracja URL
report_url = "https://centrala.ag3nts.org/report"
headers = {"Content-Type": "application/json"}

# Przygotowanie metadanych dla 10 raportów
categories = {
    "2024-11-12_report-00-sektor_C4.txt": "wykrycie, jednostka, Aleksander Ragowski, skan biometryczny, kontrola, fabryka, nauczyciel, programowanie, Java",
    "2024-11-12_report-01-sektor_A1.txt": "ruch organiczny, zwierzyna leśna, fałszywy alarm, bezpieczeństwo",
    "2024-11-12_report-02-sektor_A3.txt": "patrol nocny, cisza, brak aktywności, monitoring, peryferia",
    "2024-11-12_report-03-sektor_A3.txt": "nocny patrol, czujniki, brak wykrycia, życie organiczne",
    "2024-11-12_report-04-sektor_B2.txt": "patrol, zachód, brak anomalii, komunikacja, bezpieczeństwo",
    "2024-11-12_report-05-sektor_C1.txt": "aktywność, brak, sensor, monitorowanie, detektor ruchu",
    "2024-11-12_report-06-sektor_C2.txt": "północny zachód, stabilny, skanery, temperatura, patrol",
    "2024-11-12_report-07-sektor_C4.txt": "ultradźwięki, nadajnik, Barbara Zawadzka, odciski palców, analiza, zabezpieczenie, frontend development, JavaScript, Python, sektor C4",
    "2024-11-12_report-08-sektor_A1.txt": "monitoring, patrol, brak ruchu, czujniki, cisza",
    "2024-11-12_report-09-sektor_C2.txt": "patrol, peryferia, brak anomalii, kontynuacja, cykl"
}

# Funkcja do wysyłania raportu
def send_report(categories):
    payload = {
        "task": "dokumenty",
        "apikey": API_KEY,
        "answer": categories
    }
    response = requests.post(report_url, headers=headers, json=payload, verify=False)
    if response.status_code == 200:
        print("Poprawnie przesłano raport.")
        print(response.json())
    else:
        print(f"Błąd podczas przesyłania raportu: {response.status_code}")
        print(response.text)

# Wyślij raport
send_report(categories)
