import requests
import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI
import urllib3

# Wyłącz ostrzeżenia SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja
report_url = "https://centrala.ag3nts.org/report"
headers = {'Content-Type': 'application/json'}

# Tworzenie sesji
session = requests.Session()

# Funkcja do ładowania pliku JSON
def load_json():
    with open("json.txt", "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

# Funkcja do sprawdzania poprawności odpowiedzi matematycznych
def correct_math_fields(data):
    for entry in data.get("test-data", []):
        question = entry.get("question")
        answer = entry.get("answer")
        try:
            correct_answer = eval(question)
            if answer != correct_answer:
                print(f"Poprawiono: {question} -> {correct_answer} (było: {answer})")
                entry["answer"] = correct_answer
        except Exception as e:
            print(f"Błąd w pytaniu: {question}, {e}")
    return data

# Funkcja do poprawiania pól 'test.q' z wykorzystaniem LLM
def correct_test_fields(data):
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    for entry in data.get("test-data", []):
        test = entry.get("test")
        if test and "q" in test:
            question = test.get("q")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant answering questions."},
                    {"role": "user", "content": question}
                ]
            )
            test["a"] = response.choices[0].message.content.strip()
            print(f"Poprawiono pytanie: {question} -> Odpowiedź: {test['a']}")
    return data

# Funkcja do zapisania poprawionego pliku JSON
def save_json(data):
    with open("corrected_json.txt", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print("Zapisano poprawiony plik jako corrected_json.txt")

# Funkcja do wysyłania poprawionego pliku na serwer
def send_corrected_file():
    with open("corrected_json.txt", "r", encoding="utf-8") as file:
        corrected_data = json.load(file)
    form_data = {
        "task": "JSON",
        "apikey": corrected_data.get("apikey"),
        "answer": corrected_data
    }
    response = session.post(report_url, json=form_data, headers=headers, verify=False)
    
    # Logowanie odpowiedzi serwera
    print("Pełna odpowiedź serwera:")
    print(response.text)
    
    if response.status_code == 200:
        print("Poprawny plik został przesłany.")
    else:
        print(f"Nie udało się przesłać pliku. Kod błędu: {response.status_code}, Odpowiedź: {response.text}")


# Główna funkcja
def main():
    try:
        # Wczytaj plik JSON
        data = load_json()

        # Popraw pola matematyczne
        corrected_data = correct_math_fields(data)

        # Popraw pola 'test.q'
        corrected_data = correct_test_fields(corrected_data)

        # Zapisz poprawiony plik
        save_json(corrected_data)

        # Wyślij poprawiony plik na serwer
        send_corrected_file()
    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    main()
