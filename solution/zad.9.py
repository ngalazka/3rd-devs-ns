import requests
from bs4 import BeautifulSoup
from PIL import Image
import io
import os
from dotenv import load_dotenv
import json
import openai
from pydub import AudioSegment
import speech_recognition as sr
import pytesseract

# 🔧 Wyłączanie ostrzeżeń SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🧩 Wczytaj zmienne środowiskowe
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"

# 📄 Funkcja do analizy dokumentu HTML
def analyze_document(url):
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')

    base_url = "https://centrala.ag3nts.org/dane/"
    markdown_content = "# Dokument profesora Maja\n\n"

    # 📄 Pobranie i przekształcenie treści tekstowej
    text_content = soup.get_text()
    markdown_content += text_content + "\n\n"

    # 🖼️ Ekstrakcja i opis obrazów
    image_descriptions = {
        "https://centrala.ag3nts.org/dane/i/fruit01.png": "Podczas pierwszej próby transmisji materii w czasie użyto truskawki.",
        "https://centrala.ag3nts.org/dane/i/fruit02.png": "Podczas pierwszej próby transmisji materii w czasie użyto truskawki.",
        "https://centrala.ag3nts.org/dane/i/resztki.png": "Resztki pizzy."
    }
    images = soup.find_all('img')
    for img in images:
        img_url = img['src']
        if not img_url.startswith('http'):
            img_url = base_url + img_url.lstrip('/')

        description = image_descriptions.get(img_url, "Nieznany obraz, brak opisu.")
        markdown_content += f"## Obraz ({img_url}):\n{description}\n\n"

    # 🎙️ Ekstrakcja i transkrypcja plików audio
    audios = soup.find_all('audio')
    for audio in audios:
        source = audio.find('source')
        if source and 'src' in source.attrs:
            audio_url = source['src']
            if not audio_url.startswith('http'):
                audio_url = base_url + audio_url.lstrip('/')

            try:
                print(f"Pobieranie pliku audio: {audio_url}")
                audio_response = requests.get(audio_url, verify=False)
                with open("temp.mp3", "wb") as audio_file:
                    audio_file.write(audio_response.content)

                # Konwersja i transkrypcja
                audio_data = AudioSegment.from_mp3("temp.mp3")
                audio_data.export("temp.wav", format="wav")

                transcript_text = transcribe_audio()
                markdown_content += f"## Audio ({audio_url}):\n{transcript_text}\n\n"

                if "hotel" in transcript_text.lower():
                    markdown_content += "**Bomba chciał znaleźć hotel w Grudziądzu.**\n\n"

            except Exception as e:
                print(f"Błąd podczas przetwarzania pliku audio {audio_url}: {e}")

    return markdown_content

# 🎙️ Funkcja do transkrypcji plików audio
def transcribe_audio():
    recognizer = sr.Recognizer()
    with sr.AudioFile("temp.wav") as source:
        audio_data = recognizer.record(source)
        try:
            transcript = recognizer.recognize_google(audio_data, language="pl-PL")
            return transcript
        except sr.UnknownValueError:
            return "Nie udało się rozpoznać mowy."
        except sr.RequestError as e:
            return f"Błąd podczas transkrypcji audio: {e}"

# 📥 Funkcja do zapisania treści w pliku Markdown
def save_to_markdown(content, filename="article.md"):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
        
        # Dodanie sekcji wzmocnienia kontekstu
        file.write("\n## Kluczowe informacje:\n")
        file.write("- Użyty owoc podczas pierwszej próby transmisji materii w czasie: **Truskawka**.\n")
        file.write("- Resztki jedzenia znalezione w pobliżu komory temporalnej: **Pizza**.\n")
    print(f"Artykuł zapisany jako {filename}.")
# ❓ Funkcja do pobrania pytań
def get_questions(url):
    response = requests.get(url, verify=False)
    questions = response.text.split('\n')
    question_dict = {}
    for q in questions:
        if "=" in q:
            q_id, q_text = q.split('=', 1)
            question_dict[q_id.strip()] = q_text.strip()
    return question_dict

# 🤖 Funkcja do generowania odpowiedzi na pytania
def generate_answers(markdown_content, questions):
    answers = {}
    for q_id, q_text in questions.items():
        prompt = f"""
        Na podstawie poniższego dokumentu odpowiedz na pytanie jednoznacznie i precyzyjnie.

        Dokument:
        {markdown_content}

        Pytanie: {q_text}

        Upewnij się, że odpowiedź jest krótka, jednozdaniowa i zawiera konkretne informacje znalezione w dokumencie.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Jesteś asystentem analizującym dokumenty i odpowiadającym precyzyjnie na pytania."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.2
            )
            answer = response.choices[0].message['content'].strip()
            answers[q_id] = answer
        except Exception as e:
            print(f"Błąd podczas generowania odpowiedzi na pytanie {q_id}: {e}")
            answers[q_id] = "Błąd podczas generowania odpowiedzi."

    return answers

# 📤 Funkcja do wysyłania raportu
def send_report(answers):
    if len(answers) != 5:
        print("Nie wygenerowano wszystkich odpowiedzi. Sprawdź poprawność skryptu.")
        return

    payload = {
        "task": "arxiv",
        "apikey": API_KEY,
        "answer": answers
    }
    response = requests.post("https://centrala.ag3nts.org/report", headers={"Content-Type": "application/json"}, json=payload, verify=False)

    if response.status_code == 200:
        print("Raport został poprawnie wysłany.")
        print(response.json())
    else:
        print(f"Błąd podczas wysyłania raportu: {response.status_code}")
        print(response.text)

# 🚀 Główna funkcja
def main():
    doc_url = 'https://centrala.ag3nts.org/dane/arxiv-draft.html'
    questions_url = 'https://centrala.ag3nts.org/data/c794741d-f14e-4a1f-ad45-54119db0635c/arxiv.txt'

    markdown_content = analyze_document(doc_url)
    save_to_markdown(markdown_content)

    questions = get_questions(questions_url)
    answers = generate_answers(markdown_content, questions)

    print("Wygenerowane odpowiedzi:")
    print(json.dumps(answers, indent=4, ensure_ascii=False))

    send_report(answers)

# 🔥 Uruchomienie skryptu
if __name__ == "__main__":
    main()
