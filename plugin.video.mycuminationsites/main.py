import sys
import urllib.parse
import requests
from bs4 import BeautifulSoup
import xbmc
import xbmcgui
import xbmcplugin

# Basis-URL des Add-ons
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

# Standard-Header, damit die Website Anfragen von Kodi nicht blockiert
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def get_params():
    """Liest die übergebenen Parameter aus sys.argv[2] aus"""
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        cleaned_params = paramstring.lstrip('?')
        if (cleaned_params[-1] == '/'):
            cleaned_params = cleaned_params[:-1]
        pairsofparams = cleaned_params.split('&')
        for paramcombo in pairsofparams:
            splitparams = paramcombo.split('=')
            if len(splitparams) == 2:
                param[splitparams[0]] = urllib.parse.unquote_plus(splitparams[1])
    return param

def build_url(query):
    """Erstellt eine gueltige Kodi-Plugin-URL"""
    return BASE_URL + '?' + urllib.parse.urlencode(query)

def main_menu():
    """Erstellt das Hauptmenue"""
    # Beispiel-Kategorie
    url = build_url({'action': 'list_videos', 'category_url': 'https://beispiel-seite.com/videos/'})
    li = xbmcgui.ListItem(label='Neueste Videos')
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
    
    xbmcplugin.endOfDirectory(HANDLE)

def list_videos(category_url):
    """Ladt die HTML-Seite und parst die Videos"""
    try:
        response = requests.get(category_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hier deine BeautifulSoup-Logik einfügen, z. B.:
        # for item in soup.find_all('div', class_='video-item'):
        #     ...
        
    except Exception as e:
        xbmc.log(f"[MyCumination] Fehler beim Laden: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', 'Seite konnte nicht geladen werden', xbmcgui.NOTIFICATION_ERROR)

    xbmcplugin.endOfDirectory(HANDLE)

# Haupt-Router
params = get_params()
action = params.get('action')
url = params.get('category_url')

if action is None:
    main_menu()
elif action == 'list_videos':
    list_videos(url)

