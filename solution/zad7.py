import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import urllib3

# Wyłączanie ostrzeżeń SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja API Key i adresów URL
robot_description_url = "https://centrala.ag3nts.org/data/c794741d-f14e-4a1f-ad45-54119db0635c/robotid.json"
report_url = "https://centrala.ag3nts.org/report"
headers = {"Content-Type": "application/json"}

# Funkcja pobierająca opis robota
def download_robot_description():
    response = requests.get(robot_description_url, verify=False)
    if response.status_code == 200:
        return response.json()["description"]
    else:
        print("Błąd podczas pobierania opisu robota.")
        return ""

# Funkcja generująca obraz przy użyciu DALL-E
def generate_robot_image(description):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = (
        "Generate an image of a robot based on the following description: " + description
    )

    image = client.images.generate(
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url"
    )

    return image.data[0].url

# Funkcja wysyłająca raport z linkiem do grafiki
def send_report(image_url):
    if not image_url:
        print("Błąd: Brak URL grafiki do wysłania.")
        return

    payload = {
        "task": "robotid",
        "apikey": "c794741d-f14e-4a1f-ad45-54119db0635c",
        "answer": image_url
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
    description = download_robot_description()
    if description:
        image_url = generate_robot_image(description)
        print("Wygenerowany URL grafiki:")
        print(image_url)
        send_report(image_url)
    else:
        print("Nie udało się pobrać opisu robota.")

if __name__ == "__main__":
    main()
