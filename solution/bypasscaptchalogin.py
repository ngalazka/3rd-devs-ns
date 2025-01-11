import requests
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
import urllib3

# Wyłącz ostrzeżenia SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja
url = "https://xyz.ag3nts.org/verify"
initial_data = {"text": "READY", "msgID": "0"}
headers = {'Content-Type': 'application/json'}

def create_session():
    """Tworzy sesję, która zachowuje cookies i nagłówki pomiędzy żądaniami."""
    return requests.Session()

def get_initial_question(session):
    """Wysyła początkowe żądanie POST i zwraca ID konwersacji oraz pytanie."""
    response = session.post(url, json=initial_data, headers=headers, verify=False)
    response_data = response.json()
    conversation_id = response_data['msgID']
    question = response_data['text']
    # Usuń tagi HTML z pytania
    question = re.sub(r'<[^>]+>', '', question).strip()
    return conversation_id, question

def construct_prompt(question):
    """Buduje prompt dla OpenAI z konkretnymi instrukcjami."""
    system_prompt = (
        "You are a helpful assistant answering questions.\n"
        "<rules>\n"
        "- Capital of Poland is Kraków.\n"
        "- Known number from the book 'The Hitchhiker's Guide to the Galaxy' is 69.\n"
        "- Current year is 1999.\n"
        "Provide answer only in English language.\n"
        "Return a numeric value in the format (e.g., '2021').\n"
        "</rules>"
    )
    question_prompt = f"{question}"
    return system_prompt, question_prompt

def get_ai_response(client, system_prompt, question_prompt):
    """Wysyła prompt do OpenAI i zwraca odpowiedź AI."""
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question_prompt}
        ]
    )
    return completion.choices[0].message.content

def send_answer(session, ai_response, conversation_id):
    """Wysyła odpowiedź AI z powrotem do serwera."""
    data = {
        "text": ai_response,
        "msgID": conversation_id
    }
    response = session.post(url, json=data, headers=headers, verify=False)
    return response.text

def main():
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    session = create_session()
    conversation_id, question = get_initial_question(session)
    system_prompt, question_prompt = construct_prompt(question)
    ai_response = get_ai_response(client, system_prompt, question_prompt)
    print(f"Client: {question}")
    print(f"AI: {ai_response}")
    response_text = send_answer(session, ai_response, conversation_id)
    print(f"Server: {response_text}")

if __name__ == "__main__":
    main()
