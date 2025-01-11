import requests
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from bs4 import BeautifulSoup
import urllib3

# Wyłącz ostrzeżenia SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja
login_url = "https://xyz.ag3nts.org/"
headers = {'Content-Type': 'application/x-www-form-urlencoded'}

# Tworzenie sesji
session = requests.Session()

# Funkcja do pobierania pytania z formularza logowania
def get_initial_question():
    response = session.get(login_url, verify=False)
    if response.status_code != 200:
        raise Exception("Nie udało się połączyć ze stroną.")
    soup = BeautifulSoup(response.text, 'html.parser')
    question_element = soup.select_one('#human-question')
    if question_element:
        question_text = question_element.get_text(strip=True)
        question = question_text.split(':')[1].strip()
        return question
    raise ValueError("Nie znaleziono pytania na stronie.")

# Funkcja do wysyłania promptu do OpenAI i uzyskiwania odpowiedzi
def get_ai_response(question):
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    system_prompt = (
        "You are a helpful assistant answering questions.\n"
        "<rules>\n"
        "- Capital of Poland is Kraków.\n"
        "- Known number from the book 'The Hitchhiker's Guide to the Galaxy' is 69.\n"
        "- Current year is 1999.\n"
        "Provide answer only in English language.\n"
        "Return a numeric value in the format (e.g., '2021').\n"
        "If asked for a color, answer with 'blue'.\n"
        "If asked for a place, answer with the correct name.\n"
        "</rules>"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    )
    ai_response = response.choices[0].message.content

    # Upewnij się, że odpowiedź jest liczbą lub poprawnym tekstem
    ai_response = ai_response.strip()
    if not re.match(r'^\d+$', ai_response):
        raise ValueError("Odpowiedź AI nie jest prawidłową liczbą: " + ai_response)

    return ai_response

# Funkcja do wysyłania odpowiedzi do serwera jako formularz
def send_form_data(username, password, ai_response):
    form_data = f"username={username}&password={password}&answer={ai_response}"
    response = session.post(login_url, data=form_data, headers=headers, verify=False)
    if response.status_code == 200:
        print("Odpowiedź serwera:", response.text)
        # Przeszukaj zawartość odpowiedzi pod kątem flagi
        flag_match = re.search(r'\{\{FLG:[^}]+\}\}', response.text)
        if flag_match:
            print("Znaleziono flagę:", flag_match.group(0))
        else:
            print("Nie znaleziono flagi w odpowiedzi serwera.")
        # Zapisz treść odpowiedzi do pliku
        with open("response.html", "w", encoding="utf-8") as file:
            file.write(response.text)
            print("Zapisano odpowiedź serwera jako response.html.")
    else:
        print("Nie udało się zalogować.")

# Funkcja do pobierania pliku z sekcji "Download section"
def download_file():
    file_url = "https://xyz.ag3nts.org/files/0_13_4b.txt"
    response = session.get(file_url, verify=False)
    if response.status_code == 200:
        with open("0_13_4b.txt", "w", encoding="utf-8") as file:
            file.write(response.text)
        print("Pobrano plik 0_13_4b.txt.")
    else:
        print("Nie udało się pobrać pliku.")

# Główna funkcja
def main():
    try:
        # Pobierz pytanie z formularza logowania
        question = get_initial_question()
        print(f"Pytanie: {question}")

        # Uzyskaj odpowiedź od AI
        ai_response = get_ai_response(question)
        print(f"Odpowiedź AI: {ai_response}")

        # Wyślij dane do serwera jako formularz
        send_form_data("tester", "574e112a", ai_response)

        # Pobierz plik po zalogowaniu
        download_file()

    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    main()
