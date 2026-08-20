# -*- coding: utf-8 -*-
import sys
import os
from urllib.parse import parse_qsl
import xbmcgui
import xbmcplugin

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(ADDON_DIR, 'resources', 'lib')
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

from darknessporn import CustomSite

HANDLE = int(sys.argv[1])

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    site = CustomSite()
    
    action = params.get("action")
    url = params.get("url")

    if not action:
        site.get_menu()
        xbmcplugin.endOfDirectory(HANDLE)
        
    elif action == "list_videos":
        site.list_videos(url)
        xbmcplugin.endOfDirectory(HANDLE)

    elif action == "search_video":
        site.search_video()
        xbmcplugin.endOfDirectory(HANDLE)

    elif action == "switch_language":
        site.switch_language()

    elif action == "play_video":
        stream_url = site.play_video(url)
        if stream_url:
            play_item = xbmcgui.ListItem(path=stream_url)
            xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification("Fehler", "Stream-URL konnte nicht extrahiert werden.", xbmcgui.NOTIFICATION_ERROR, 3000)

if __name__ == "__main__":
    router(sys.argv[2][1:])
