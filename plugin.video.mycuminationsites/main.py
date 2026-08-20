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

def get_params():
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
    return BASE_URL + '?' + urllib.parse.urlencode(query)

def main_menu():
    items = [
        ('Neueste Videos', 'https://darknessporn.com/'),
        ('Most Viewed Videos', 'https://darknessporn.com/most-viewed/'),
        ('Populärste Videos', 'https://darknessporn.com/popular/'),
    ]
    
    for title, target_url in items:
        url = build_url({'action': 'list_videos', 'category_url': target_url})
        li = xbmcgui.ListItem(label=title)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
    
    xbmcplugin.endOfDirectory(HANDLE)

def list_videos(category_url):
    try:
        response = requests.get(category_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        videos = soup.find_all('article') or soup.find_all('div', class_='post')
        
        for video in videos:
            a_tag = video.find('a')
            if not a_tag:
                continue
            
            video_url = a_tag.get('href')
            title = a_tag.get('title') or a_tag.text.strip()
            
            img_tag = video.find('img')
            thumb = img_tag.get('src') or img_tag.get('data-src') if img_tag else ''
            
            if video_url and title:
                url = build_url({'action': 'play_video', 'video_url': video_url})
                li = xbmcgui.ListItem(label=title)
                if thumb:
                    li.setArt({'thumb': thumb, 'icon': thumb})
                
                li.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)
                
    except Exception as e:
        xbmc.log(f"[MyCumination] Fehler beim Laden: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', 'Seite konnte nicht geladen werden', xbmcgui.NOTIFICATION_ERROR)

    xbmcplugin.endOfDirectory(HANDLE)

def play_video(video_url):
    try:
        response = requests.get(video_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        video_element = soup.find('video') or soup.find('source')
        stream_url = None
        
        if video_element:
            stream_url = video_element.get('src')
            
        if stream_url:
            play_item = xbmcgui.ListItem(path=stream_url)
            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmcgui.Dialog().notification('Fehler', 'Kein Stream gefunden', xbmcgui.NOTIFICATION_ERROR)
    except Exception as e:
        xbmc.log(f"[MyCumination] Abspiel-Fehler: {str(e)}", level=xbmc.LOGERROR)

# Haupt-Router
params = get_params()
action = params.get('action')
url = params.get('category_url') or params.get('video_url')

if action is None:
    main_menu()
elif action == 'list_videos':
    list_videos(url)
elif action == 'play_video':
    play_video(url)
