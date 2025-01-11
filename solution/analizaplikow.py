import requests
import os
import zipfile
import json
from dotenv import load_dotenv
import urllib3
from pydub import AudioSegment
import openai
from PIL import Image
import pytesseract

# Wyłączanie ostrzeżeń SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe
load_dotenv()
API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Konfiguracja URL
url_zip = "https://centrala.ag3nts.org/dane/pliki_z_fabryki.zip"
report_url = "https://centrala.ag3nts.org/report"
headers = {"Content-Type": "application/json"}

# Pobranie pliku ZIP i rozpakowanie
def download_and_extract_zip():
    response = requests.get(url_zip, verify=False)
    zip_path = "pliki_z_fabryki.zip"
    with open(zip_path, "wb") as file:
        file.write(response.content)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall("fabryka")
    print("Pobrano i rozpakowano plik pliki_z_fabryki.zip")

# Funkcja do analizy plików tekstowych
def process_text_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return analyze_content_with_gpt(content)

# Funkcja do analizy plików audio
def process_audio_file(file_path):
    audio = AudioSegment.from_mp3(file_path)
    audio.export("temp.wav", format="wav")
    with open("temp.wav", "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return analyze_content_with_gpt(transcript['text'])

# Funkcja do analizy plików obrazów
def process_image_file(file_path):
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang="eng")
        return analyze_content_with_gpt(text)
    except Exception as e:
        print(f"Błąd podczas przetwarzania obrazu {file_path}: {e}")
        return None

# Funkcja do analizy treści za pomocą GPT
def analyze_content_with_gpt(file_type, content):
    prompt = (
        f"You are an advanced assistant that classifies content into categories based on the presence of specific information:\n\n"
        f"- Classify as 'people' if the content mentions discovering or capturing specific individuals (captured or not but describing their hostile activit-this is important), or finding traces of human presence (such as footprints, personal items, or visual identification).\n"
        f"- Classify as 'hardware' if the content describes hardware repairs, maintenance, or issues with physical devices (such as sensors, antennas, or machinery).\n"
        f"- Classify as 'none' if the content mentions software updates, algorithm improvements, or any modifications to AI models or digital systems.\n"
        f"- Classify as 'none' if the content mentions people without evidence of their presence or capture.\n"
        f"- You'll never receive a text that mentions both people and hardware.\n\n"
        f"Here are some examples of reports and their correct classifications:\n"
        f"Example 1:\nText: Godzina 22:43. Wykryto jednostkę organiczną w pobliżu północnego skrzydła fabryki. Osobnik przedstawił się jako Aleksander Ragowski. Przeprowadzono skan biometryczny, zgodność z bazą danych potwierdzona. Jednostka przekazana do działu kontroli.\nClassification: people\n\n"
        f"Example 2:\nText: Godzina 11:50. W czujniku ruchu wykryto usterkę spowodowaną zwarciem kabli. Przyczyną była mała mysz, która dostała się między przewody. Odłączono zasilanie, usunięto ciało obce i zabezpieczono kable. Czujnik ponownie skalibrowany.\nClassification: hardware\n\n"
        f"Example 3:\nText: Przeprowadzono aktualizację modułu AI analizującego wzorce ruchu. Wprowadzono dodatkowe algorytmy umożliwiające szybsze przetwarzanie i bardziej precyzyjną analizę zachowań niepożądanych. Aktualizacja zakończona sukcesem.\nClassification: none\n\n"
        f"Example 4:\nText: Rozmawialiśmy z dostawcą pizzy, który może nam pomóc w dostawie jedzenia. Nie znaleziono żadnych śladów jego obecności w obiekcie.\nClassification: none\n\n"
        f"Here is the {file_type} content to analyze:\n\n{content}\n\n"
        f"Provide only the category in your response."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that analyzes and classifies content into categories."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0.0
    )
    return response['choices'][0]['message']['content'].strip().lower()

# Funkcja do kategorii plików
def categorize_files():
    categories = {"people": [], "hardware": []}

    for root, dirs, files in os.walk("fabryka"):
        if "facts" in root:
            continue  # Pomijanie folderu z faktami

        for file_name in files:
            file_path = os.path.join(root, file_name)
            category = None

            if file_name.endswith(".txt"):
                print(f"Przetwarzanie pliku tekstowego: {file_name}")
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                category = analyze_content_with_gpt("text", content)

            elif file_name.endswith(".mp3"):
                print(f"Przetwarzanie pliku audio: {file_name}")
                audio = AudioSegment.from_mp3(file_path)
                audio.export("temp.wav", format="wav")
                with open("temp.wav", "rb") as audio_file:
                    transcript = openai.Audio.transcribe("whisper-1", audio_file)
                category = analyze_content_with_gpt("audio", transcript['text'])

            elif file_name.endswith(".png"):
                print(f"Przetwarzanie pliku obrazu: {file_name}")
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image, lang="eng")
                category = analyze_content_with_gpt("image", text)

            # 🔧 Interpretacja kategorii
            if category in ["people", "hardware", "both"]:
                print(f"Kategoria: {category}")
                if category == "people":
                    categories["people"].append(file_name)
                elif category == "hardware":
                    categories["hardware"].append(file_name)
                elif category == "both":
                    categories["people"].append(file_name)
                    categories["hardware"].append(file_name)

            else:
                print(f"Kategoria: 'none' (pominięto)")

    return categories

# Funkcja do wysyłania raportu
def send_report(categories):
    payload = {
        "task": "kategorie",
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

# Główna funkcja programu
def main():
    download_and_extract_zip()
    categories = categorize_files()
    print("Wygenerowane kategorie:")
    print(json.dumps(categories, indent=4))
    send_report(categories)

if __name__ == "__main__":
    main()