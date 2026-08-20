import sys
import urllib.parse
import requests
from bs4 import BeautifulSoup
import xbmc
import xbmcgui
import xbmcplugin

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE_URL = sys.argv[0] if len(sys.argv) > 0 else ''

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def build_url(query):
    return BASE_URL + '?' + urllib.parse.urlencode(query)

def main_menu():
    items = [
        ('Neueste Videos', 'https://darknessporn.com/'),
        ('Most Viewed Videos', 'https://darknessporn.com/most-viewed/'),
        ('Popularste Videos', 'https://darknessporn.com/popular/'),
    ]
    for title, target_url in items:
        url = build_url({'action': 'list_videos', 'category_url': target_url})
        li = xbmcgui.ListItem(label=title)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

def get_params():
    param = {}
    if len(sys.argv) >= 3:
        paramstring = sys.argv[2]
        if len(paramstring) >= 2:
            cleaned_params = paramstring.lstrip('?')
            if cleaned_params.endswith('/'):
                cleaned_params = cleaned_params[:-1]
            pairsofparams = cleaned_params.split('&')
            for paramcombo in pairsofparams:
                splitparams = paramcombo.split('=')
                if len(splitparams) == 2:
                    param[splitparams[0]] = urllib.parse.unquote_plus(splitparams[1])
    return param

def router():
    try:
        params = get_params()
        action = params.get('action')
        if not action:
            main_menu()
        else:
            main_menu()
    except Exception as e:
        xbmc.log(f"[MyCumination] Critical Error: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', str(e), xbmcgui.NOTIFICATION_ERROR)

if __name__ == '__main__':
    router()
