import sys
import os
from urllib.parse import parse_qsl
import xbmcgui
import xbmcplugin

# Den Pfad zu resources/lib bekannt machen, damit Python deine Module findet
ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(ADDON_DIR, 'resources', 'lib')
sys.path.append(LIB_DIR)

# Jetzt können wir dein Scraper-Modul importieren
try:
    import darknessporn
except ImportError:
    darknessporn = None

HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

def build_url(query):
    return f"{BASE_URL}?{query}"

def show_main_menu():
    """Erstellt das Hauptmenü"""
    list_item = xbmcgui.ListItem(label="Darknessporn")
    url = build_url("site=darknessporn")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

def show_darknessporn_menu():
    """Ruft die Logik aus deiner darknessporn.py auf"""
    if darknessporn:
        # Hier rufen wir die Funktionen aus deiner darknessporn.py auf
        # Bsp: darknessporn.get_videos()
        dialog = xbmcgui.Dialog()
        dialog.ok("Erfolg", "Darknessporn-Modul erfolgreich geladen!")
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok("Fehler", "darknessporn.py konnte nicht gefunden werden.")

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    
    if not params:
        show_main_menu()
    elif params.get("site") == "darknessporn":
        show_darknessporn_menu()

if __name__ == "__main__":
    router(sys.argv[2][1:])


