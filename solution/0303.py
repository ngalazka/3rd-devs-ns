import requests
import os
import json
import urllib3
import openai
from dotenv import load_dotenv

# Wyłączanie ostrzeżeń SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wczytaj zmienne środowiskowe
load_dotenv()
API_KEY = "c794741d-f14e-4a1f-ad45-54119db0635c"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Konfiguracja URL
api_url = "https://centrala.ag3nts.org/apidb"
headers = {"Content-Type": "application/json"}

# Funkcja do wykonywania zapytań do API
def query_api(sql_query):
    payload = {
        "task": "database",
        "apikey": API_KEY,
        "query": sql_query
    }
    response = requests.post(api_url, headers=headers, json=payload, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd podczas wykonywania zapytania: {response.status_code}")
        print(response.text)
        return None

# 1. Pobranie listy tabel
tables = query_api("show tables")
print("Dostępne tabele:", tables)

# 2. Pobranie struktury tabel
table_structures = {}
for table in [item['Tables_in_banan'] for item in tables.get('reply', [])]:
    structure = query_api(f"show create table {table}")
    if structure and 'reply' in structure:
        table_structures[table] = structure['reply']

print("Struktura tabel:", json.dumps(table_structures, indent=2))

# 3. Generowanie zapytania SQL z pomocą GPT
def generate_sql_query(structures):
    schema_string = json.dumps(structures, indent=2)
    system_prompt = f"You are an SQL expert. Here is the DB schema: {schema_string}. Generate a SQL query that answers the user request. Return only the query, with no additional text."
    user_prompt = "Które aktywne datacenter (DC_ID) są zarządzane przez pracowników, którzy są na urlopie (is_active=0)?"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message['content'].replace('```sql', '').replace('```', '').strip()

# Wygenerowane zapytanie
sql_query = generate_sql_query(table_structures)
print("Wygenerowane zapytanie SQL:", sql_query)

# 4. Wykonanie zapytania SQL
data = query_api(sql_query)
print("Wyniki zapytania:", data)

# 5. Wysłanie odpowiedzi do centrali
def send_answer(answer):
    headers_with_key = {"Content-Type": "application/json", "apikey": API_KEY}
    payload = {"task": "database", "apikey": API_KEY, "answer": answer}
    response = requests.post("https://centrala.ag3nts.org/report", headers=headers_with_key, json=payload, verify=False)
    if response.status_code == 200:
        print("Poprawnie przesłano odpowiedź.")
        print(response.json())
    else:
        print(f"Błąd podczas przesyłania odpowiedzi: {response.status_code}")
        print(response.text)

# Przygotowanie odpowiedzi
if data and 'reply' in data:
    dc_ids = [int(item['dc_id']) for item in data['reply']]
    print("Przesyłane ID datacenter:", dc_ids)
    send_answer(dc_ids)
