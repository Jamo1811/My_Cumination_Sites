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
        ('Alle Videos', 'https://darknessporn.com/', 'list_videos'),
        ('Neueste Videos', 'https://darknessporn.com/?filter=latest', 'list_videos'),
        ('Most Viewed Videos', 'https://darknessporn.com/?filter=most_viewed', 'list_videos'),
        ('Top Bewertet', 'https://darknessporn.com/?filter=top-rated', 'list_videos'),
        ('Kategorien', 'https://darknessporn.com/categories/', 'list_categories'),
    ]
    for title, target_url, action in items:
        url = build_url({'action': action, 'category_url': target_url})
        li = xbmcgui.ListItem(label=title)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

def list_categories(categories_url):
    try:
        session = requests.Session()
        response = session.get(categories_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        added_urls = set()

        # Eingrenzung auf den Hauptbereich
        main_content = soup.find('div', id='single-wrapper') or soup.find('div', class_='site') or soup

        for a_tag in main_content.find_all('a', href=True):
            href = a_tag['href']
            
            if ('/category/' in href or '/tag/' in href or '/categories/' in href) and href not in added_urls:
                if not href.startswith('http'):
                    href = urllib.parse.urljoin('https://darknessporn.com/', href)
                
                title = a_tag.text.strip() or a_tag.get('title') or ''
                img_tag = a_tag.find('img')
                thumb = ''
                if img_tag:
                    thumb = img_tag.get('data-src') or img_tag.get('src') or ''
                
                if title and len(title) > 2 and href != categories_url:
                    added_urls.add(href)
                    url = build_url({'action': 'list_videos', 'category_url': href})
                    li = xbmcgui.ListItem(label=title)
                    if thumb:
                        li.setArt({'thumb': thumb, 'icon': thumb})
                    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

    except Exception as e:
        xbmc.log(f"[MyCumination] Fehler bei Kategorien: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', str(e), xbmcgui.NOTIFICATION_ERROR)

    xbmcplugin.endOfDirectory(HANDLE)

def list_videos(category_url):
    try:
        session = requests.Session()
        response = session.get(category_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        count = 0
        added_urls = set()

        # Nur Artikel-Elemente / Video-Karten parsen (ignoriert Sidebar und Footer)
        articles = soup.find_all(['article', 'div'], class_=re.compile(r'post|video|item'))

        for art in articles:
            a_tag = art.find('a', href=True)
            if not a_tag:
                continue

            video_url = a_tag['href']
            if not video_url.startswith('http'):
                video_url = urllib.parse.urljoin('https://darknessporn.com/', video_url)

            if video_url in added_urls or video_url.endswith('/categories/'):
                continue

            img_tag = art.find('img')
            title = a_tag.get('title') or (img_tag.get('alt') if img_tag else '') or a_tag.text.strip()
            thumb = ''
            if img_tag:
                thumb = img_tag.get('data-src') or img_tag.get('data-original') or img_tag.get('src') or ''

            if title and len(title) > 3:
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
        soup = BeautifulSoup(html, 'html.parser')
        
        stream_url = None

        # 1. Suche nach vollwertigen Haupt-Videos (schließt Vorschau-Trailers aus)
        for tag in soup.find_all(['video', 'source']):
            src = tag.get('src') or tag.get('data-src') or ''
            if src and '.mp4' in src.lower():
                if not any(x in src.lower() for x in ['preview', 'trailer', 'short', 'thumb', 'gif', 'sample']):
                    stream_url = src
                    break

        # 2. Suche nach nosofiles CDN Links mit Unterdrückung von Previews
        if not stream_url:
            noso_matches = re.findall(r'https?://[^\s\'"]*nosofiles\.com[^\s\'"]*\.mp4[^\s\'"]*', html)
            for m in noso_matches:
                if not any(x in m.lower() for x in ['preview', 'short', 'thumb']):
                    stream_url = m
                    break

        # 3. Poster-Bild Fallback (_poster.jpg durch .mp4 ersetzen)
        if not stream_url:
            poster_match = re.search(r'https?://[^\s\'"]+output_[^\s\'"]+?_poster\.jpg[^\s\'"]*', html)
            if poster_match:
                stream_url = re.sub(r'_poster\.jpg.*$', '.mp4', poster_match.group(0))

        if stream_url:
            stream_url = urllib.parse.unquote(stream_url).replace('&amp;', '&')
            
            # Header für Kodi-Player anhängen, um Abbrüche zu vermeiden
            headers_str = f"User-Agent={urllib.parse.quote(headers['User-Agent'])}&Referer={urllib.parse.quote(video_url)}"
            final_stream_url = f"{stream_url}|{headers_str}"
            
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
    elif action == 'list_categories':
        list_categories(url)
    elif action == 'list_videos':
        list_videos(url)
    elif action == 'play_video':
        play_video(url)

if __name__ == '__main__':
    router()
