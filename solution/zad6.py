import requests
import os
import zipfile
import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI
import json
import urllib3
from pydub import AudioSegment  # Dodaj import do konwersji plików audio

# Wyłączanie ostrzeżeń SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja URL i API Key
url_zip = "https://centrala.ag3nts.org/dane/przesluchania.zip"
report_url = "https://centrala.ag3nts.org/report"
headers = {"Content-Type": "application/json"}

# Pobranie pliku ZIP i rozpakowanie
def download_and_extract_zip():
    response = requests.get(url_zip, verify=False)
    zip_path = "przesluchania.zip"
    with open(zip_path, "wb") as file:
        file.write(response.content)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall("przesluchania")
    print("Pobrano i rozpakowano plik przesluchania.zip")

# Funkcja do transkrypcji nagrań audio
def transcribe_audio_files():
    recognizer = sr.Recognizer()
    transcripts = []
    for file_name in os.listdir("przesluchania"):
        if file_name.endswith(".m4a"):
            file_path = os.path.join("przesluchania", file_name)
            wav_path = file_path.replace(".m4a", ".wav")
            
            # Konwersja pliku .m4a na .wav
            audio = AudioSegment.from_file(file_path)
            audio.export(wav_path, format="wav")

            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                try:
                    transcript = recognizer.recognize_google(audio_data, language="pl-PL")
                    transcripts.append(transcript)
                    print(f"Transkrypcja {file_name} zakończona.")
                except sr.UnknownValueError:
                    print(f"Nie można rozpoznać {file_name}")
    return " ".join(transcripts)

# Funkcja wykorzystująca OpenAI do analizy transkrypcji
def analyze_transcripts_with_openai(transcripts):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = (
        "Resolve conflicting information from the transcripts. "
        "Focus on the statement provided by Rafał, as it is the most reliable and credible source. "
        "Identify the specific institute from the transcripts and use internal knowledge to determine the street name where the institute is located. "
        "Think step by step and provide your answer as a street name in the following format: <answer>street name</answer>."
    )

    if not transcripts.strip():
        print("Błąd: Transkrypcja jest pusta.")
        return ""

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": transcripts}
    ]

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=100,
        temperature=0.3
    )

    response = completion.choices[0].message.content
    start_tag = "<answer>"
    end_tag = "</answer>"
    answer = response[response.find(start_tag) + len(start_tag):response.find(end_tag)].strip()

    return answer

# Funkcja wysyłająca raport z odpowiedzią
def send_report(answer):
    if not answer:
        print("Błąd: Brak odpowiedzi do wysłania.")
        return

    payload = {
        "task": "mp3",
        "apikey": "c794741d-f14e-4a1f-ad45-54119db0635c",
        "answer": answer
    }
    response = requests.post(report_url, headers=headers, json=payload, verify=False)
    if response.status_code == 200:
        print("Poprawnie przesłano odpowiedź.")
        print(response.json())
    else:
        print(f"Błąd podczas przesyłania pliku: {response.status_code}")
        print(response.text)

# Główna funkcja programu
def main():
    download_and_extract_zip()
    transcripts = transcribe_audio_files()
    if transcripts:
        answer = analyze_transcripts_with_openai(transcripts)
        print("Ulica, na której znajduje się instytut profesora Maja:")
        print(answer)
        send_report(answer)
    else:
        print("Nie udało się uzyskać transkrypcji.")

if __name__ == "__main__":
    main()
	
	