# -*- coding: utf-8 -*-
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_html(url):
    """Holt den Quelltext einer Webseite via Requests"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"[DarknessPorn] Fehler beim Laden von {url}: {e}")
    return None
