import sys
from urllib.parse import parse_qsl
import xbmcgui
import xbmcplugin

# Basis-URL und Handle von Kodi abfangen
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

def build_url(query):
    return f"{BASE_URL}?{query}"

def show_main_menu():
    """Erstellt das Hauptmenü in Kodi"""
    # Beispiel für einen ersten Menüeintrag
    list_item = xbmcgui.ListItem(label="Darknessporn")
    
    # URL definieren, die aufgerufen wird, wenn man auf den Eintrag klickt
    url = build_url("site=darknessporn")
    
    # IsFolder=True bedeutet: Es öffnet sich ein Untermenü/eine Liste
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=True)
    
    # Verzeichnis-Ende an Kodi melden
    xbmcplugin.endOfDirectory(HANDLE)

def router(paramstring):
    """Verteilt die Anfragen je nach Parameter"""
    params = dict(parse_qsl(paramstring))
    
    if not params:
        # Kein Parameter -> Hauptmenü anzeigen
        show_main_menu()
    elif params.get("site") == "darknessporn":
        # Hier rufen wir später dein Skript aus resources/lib/darknessporn.py auf
        dialog = xbmcgui.Dialog()
        dialog.notification("Info", "Darknessporn ausgewählt!", xbmcgui.NOTIFICATION_INFO, 3000)

if __name__ == "__main__":
    router(sys.argv[2][1:])

