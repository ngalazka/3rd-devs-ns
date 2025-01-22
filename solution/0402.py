#!/usr/bin/env python3
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"
REPORT_URL = "https://centrala.ag3nts.org/report"

# Zgodnie z regułą (d > a) otrzymaliśmy:
correct_ids = ["01", "02", "04", "10"]

payload = {
    "task": "research",
    "apikey": API_KEY,
    "answer": correct_ids
}

response = requests.post(REPORT_URL, json=payload, verify=False)
print("📩 Odpowiedź centrali:", response.text)
