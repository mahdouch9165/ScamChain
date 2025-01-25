import requests

def check_honeypot(address):
    url = f"https://api.honeypot.is/v2/IsHoneypot?address={address}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()