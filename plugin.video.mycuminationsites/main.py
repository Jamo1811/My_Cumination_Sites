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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'de,en-US;q=0.7,en;q=0.3'
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
        
        # KolorTube Theme spezifische Selektoren
        videos = soup.find_all('article') or soup.select('div.thumb-block, div.post, div.video-block')
        
        for video in videos:
            a_tag = video.find('a')
            if not a_tag:
                continue
            
            video_url = a_tag.get('href')
            
            # Titel aus a-tag, title-Attribut oder h2/h3 auslesen
            title = a_tag.get('title')
            if not title:
                heading = video.find(['h2', 'h3', 'span'])
                title = heading.text.strip() if heading else a_tag.text.strip()
            
            # Vorschaubild (Thumb) auslesen
            img_tag = video.find('img')
            thumb = ''
            if img_tag:
                thumb = img_tag.get('data-src') or img_tag.get('data-original') or img_tag.get('src') or ''
            
            if video_url and title and len(title) > 2:
                url = build_url({'action': 'play_video', 'video_url': video_url})
                li = xbmcgui.ListItem(label=title)
                if thumb:
                    li.setArt({'thumb': thumb, 'icon': thumb})
                
                li.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)
                
    except Exception as e:
        xbmc.log(f"[MyCumination] Fehler beim Laden: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', 'Konnte Videos nicht laden', xbmcgui.NOTIFICATION_ERROR)

    xbmcplugin.endOfDirectory(HANDLE)

def play_video(video_url):
    try:
        response = requests.get(video_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        stream_url = None
        
        # 1. Video Tag
        video_element = soup.find('video')
        if video_element:
            source = video_element.find('source')
            stream_url = source.get('src') if source else video_element.get('src')
        
        # 2. Iframe Fallback
        if not stream_url:
            iframe = soup.find('iframe')
            if iframe:
                stream_url = iframe.get('src')

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
