import os
import json
import requests

# Tus credenciales fijas
CLIENT_ID = "7845742212273146"
CLIENT_SECRET = "B2WjP8cLbez9IqE5CVRj5jzJjJILOhCE"

# Leer refresh_token desde archivo
def load_refresh_token():
    try:
        with open("refresh_token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise Exception("⚠️ No se encontró 'refresh_token.txt'. Ingresalo manualmente para iniciar.")

# Guardar nuevo refresh_token
def save_refresh_token(token):
    with open("refresh_token.txt", "w") as f:
        f.write(token)

def refresh_access_token(client_id, client_secret, refresh_token):
    url = "https://api.mercadolibre.com/oauth/token"
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()

def fetch_mercado_libre_trends(access_token):
    url = "https://api.mercadolibre.com/trends/MLA/MLA1246"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    os.makedirs("trend", exist_ok=True)
    with open('trend/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data

# === MAIN TEST ===
try:
    refresh_token = load_refresh_token()

    print("🔁 Refrescando access token...")
    token_data = refresh_access_token(CLIENT_ID, CLIENT_SECRET, refresh_token)
    access_token = token_data["access_token"]
    new_refresh_token = token_data["refresh_token"]

    print("💾 Guardando nuevo refresh_token...")
    save_refresh_token(new_refresh_token)

    print("📡 Llamando a la API de tendencias...")
    trends_data = fetch_mercado_libre_trends(access_token)

    print("✅ ¡Tendencias guardadas en trend/data.json!")
    print(f"🔍 Primera keyword: {trends_data[0]['keyword'] if trends_data else 'Vacío'}")

except Exception as e:
    print(f"❌ Error: {e}")
