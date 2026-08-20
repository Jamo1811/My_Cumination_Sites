import sys
import urllib.parse
import requests
from bs4 import BeautifulSoup
import xbmc
import xbmcgui
import xbmcplugin

HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

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

if __name__ == '__main__':
    main_menu()
