import sys
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
import xbmc
import xbmcgui
import xbmcplugin

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE_URL = sys.argv[0] if len(sys.argv) > 0 else ''

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
}

def build_url(query):
    return BASE_URL + '?' + urllib.parse.urlencode(query)

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

def main_menu():
    items = [
        ('Neueste Videos', 'https://darknessporn.com/?filter=latest'),
        ('Most Viewed Videos', 'https://darknessporn.com/?filter=most_viewed'),
        ('Top Bewertet', 'https://darknessporn.com/?filter=top-rated'),
    ]
    for title, target_url in items:
        url = build_url({'action': 'list_videos', 'category_url': target_url})
        li = xbmcgui.ListItem(label=title)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

def list_videos(category_url):
    try:
        session = requests.Session()
        response = session.get(category_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        count = 0
        added_urls = set()

        for a_tag in soup.find_all('a', href=True):
            video_url = a_tag['href']
            
            if not video_url.startswith('http'):
                video_url = urllib.parse.urljoin('https://darknessporn.com/', video_url)

            if video_url in added_urls or '?filter=' in video_url or '/category/' in video_url:
                continue

            img_tag = a_tag.find('img')
            if img_tag:
                title = a_tag.get('title') or img_tag.get('alt') or img_tag.get('title') or a_tag.text.strip()
                thumb = img_tag.get('data-src') or img_tag.get('data-original') or img_tag.get('data-webp') or img_tag.get('src') or ''
                
                if title and len(title) > 3 and ('/video/' in video_url or '/watch/' in video_url or len(video_url.rstrip('/').split('/')) > 3):
                    added_urls.add(video_url)
                    url = build_url({'action': 'play_video', 'video_url': video_url})
                    li = xbmcgui.ListItem(label=title)
                    if thumb:
                        li.setArt({'thumb': thumb, 'icon': thumb})
                    
                    li.setProperty('IsPlayable', 'true')
                    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)
                    count += 1

        if count == 0:
            xbmcgui.Dialog().notification('Hinweis', 'Keine Videos gefunden', xbmcgui.NOTIFICATION_WARNING)
            
    except Exception as e:
        xbmc.log(f"[MyCumination] Fehler beim Laden: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', str(e), xbmcgui.NOTIFICATION_ERROR)

    xbmcplugin.endOfDirectory(HANDLE)

def play_video(video_url):
    try:
        headers = HEADERS.copy()
        headers['Referer'] = video_url

        session = requests.Session()
        response = session.get(video_url, headers=headers, timeout=15)
        html = response.text
        
        stream_url = None

        # 1. KolarTube JS-Variablen
        js_matches = re.findall(r'(?:video_url|file|src|stream_url)\s*[:=]\s*["\'](https?://[^\'\"]+\.(?:mp4|m3u8)[^\'\"]*)["\']', html, re.IGNORECASE)
        for match in js_matches:
            if not any(x in match.lower() for x in ['preview', 'trailer', 'short', 'gif', 'taser', 'thumb']):
                stream_url = match
                break

        # 2. HTML5 Video Container
        if not stream_url:
            soup = BeautifulSoup(html, 'html.parser')
            for src_tag in soup.find_all(['source', 'video']):
                link = src_tag.get('src') or src_tag.get('data-src') or ''
                if link and not any(x in link.lower() for x in ['preview', 'trailer', 'short', 'gif']):
                    stream_url = link
                    break

        # 3. Regex Fallback
        if not stream_url:
            matches = re.findall(r'https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*', html)
            for match in matches:
                if not any(x in match.lower() for x in ['preview', 'trailer', 'short', 'gif', 'taser', 'thumb']):
                    stream_url = match
                    break

        # 4. Embedded iframe Player
        if not stream_url:
            soup = BeautifulSoup(html, 'html.parser')
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                iframe_url = iframe.get('src')
                if iframe_url.startswith('//'):
                    iframe_url = 'https:' + iframe_url
                iframe_resp = session.get(iframe_url, headers=headers, timeout=10)
                iframe_matches = re.findall(r'https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*', iframe_resp.text)
                for match in iframe_matches:
                    if not any(x in match.lower() for x in ['preview', 'trailer', 'short', 'gif']):
                        stream_url = match
                        break

        if stream_url:
            stream_url = urllib.parse.unquote(stream_url).replace('&amp;', '&')
            final_stream_url = f"{stream_url}|User-Agent={urllib.parse.quote(headers['User-Agent'])}&Referer={urllib.parse.quote(video_url)}"
            play_item = xbmcgui.ListItem(path=final_stream_url)
            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmcgui.Dialog().notification('Fehler', 'Kein Hauptstream gefunden', xbmcgui.NOTIFICATION_ERROR)
            
    except Exception as e:
        xbmc.log(f"[MyCumination] Abspiel-Fehler: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', str(e), xbmcgui.NOTIFICATION_ERROR)

def router():
    params = get_params()
    action = params.get('action')
    url = params.get('category_url') or params.get('video_url')

    if not action:
        main_menu()
    elif action == 'list_videos':
        list_videos(url)
    elif action == 'play_video':
        play_video(url)

if __name__ == '__main__':
    router()
