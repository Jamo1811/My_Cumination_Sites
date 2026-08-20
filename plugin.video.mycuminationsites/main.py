import sys
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
import xbmc
import xbmcgui
import xbmcplugin

# Prüfe, ob resolveurl installiert ist
try:
    import resolveurl
    HAS_RESOLVEURL = True
except ImportError:
    HAS_RESOLVEURL = False

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE_URL = sys.argv[0] if len(sys.argv) > 0 else ''

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
}

def build_url(query):
    return BASE_URL + '?' + urllib.parse.urlencode(query)

def get_params():
    param = {}
    if len(sys.argv) >= 3:
        paramstring = sys.argv[2]
        if len(paramstring) >= 2:
            cleaned_params = paramstring.lstrip('?').rstrip('/')
            for paramcombo in cleaned_params.split('&'):
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
        soup = BeautifulSoup(response.text, 'html.parser')
        added_urls = set()

        main_content = soup.find('div', id='single-wrapper') or soup.find('div', class_='site') or soup

        for a_tag in main_content.find_all('a', href=True):
            href = a_tag['href']
            if ('/category/' in href or '/tag/' in href or '/categories/' in href) and href not in added_urls:
                if not href.startswith('http'):
                    href = urllib.parse.urljoin('https://darknessporn.com/', href)
                
                title = a_tag.text.strip() or a_tag.get('title') or ''
                img_tag = a_tag.find('img')
                thumb = (img_tag.get('data-src') or img_tag.get('src') or '') if img_tag else ''
                
                if title and len(title) > 2 and href != categories_url:
                    added_urls.add(href)
                    url = build_url({'action': 'list_videos', 'category_url': href})
                    li = xbmcgui.ListItem(label=title)
                    if thumb:
                        li.setArt({'thumb': thumb, 'icon': thumb})
                    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
    except Exception as e:
        xbmcgui.Dialog().notification('Fehler', str(e), xbmcgui.NOTIFICATION_ERROR)
    xbmcplugin.endOfDirectory(HANDLE)

def list_videos(category_url):
    try:
        xbmcplugin.setContent(HANDLE, 'videos')
        session = requests.Session()
        response = session.get(category_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        count = 0
        added_urls = set()

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
            thumb = (img_tag.get('data-src') or img_tag.get('data-original') or img_tag.get('src') or '') if img_tag else ''

            if title and len(title) > 3:
                added_urls.add(video_url)
                url = build_url({'action': 'play_video', 'video_url': video_url})
                li = xbmcgui.ListItem(label=title)
                if thumb:
                    li.setArt({'thumb': thumb, 'icon': thumb})
                
                li.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)
                count += 1

        next_page_tag = soup.find('a', class_=re.compile(r'next|pagination-next'), href=True) or \
                        soup.find('a', string=re.compile(r'Nächste|Next|»|>', re.I), href=True)
        if next_page_tag:
            next_url = next_page_tag['href']
            if not next_url.startswith('http'):
                next_url = urllib.parse.urljoin('https://darknessporn.com/', next_url)
            url = build_url({'action': 'list_videos', 'category_url': next_url})
            li = xbmcgui.ListItem(label='[COLOR yellow]>> Nächste Seite >>[/COLOR]')
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

    except Exception as e:
        xbmcgui.Dialog().notification('Fehler', str(e), xbmcgui.NOTIFICATION_ERROR)
    xbmcplugin.endOfDirectory(HANDLE)

def play_video(video_url):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        session.headers['Referer'] = video_url

        res = session.get(video_url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')

        stream_url = None

        # 1. Suche nach iFrames (viele Erwachsenen-Seiten betten externe Hoster ein)
        iframe_urls = []
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if not src.startswith('http'):
                src = urllib.parse.urljoin('https://darknessporn.com/', src)
            iframe_urls.append(src)

        # Versuch mit ResolveURL (falls externe Hoster wie Dood, Streamtape etc. eingebettet sind)
        if HAS_RESOLVEURL:
            for url in iframe_urls:
                if resolveurl.HostedMediaFile(url).valid_url():
                    stream_url = resolveurl.resolve(url)
                    break

        # 2. Falls kein Hoster aufgelöst wurde: HTML5 Video-Tags scannen
        if not stream_url:
            for tag in soup.find_all(['video', 'source']):
                src = tag.get('src') or tag.get('data-src') or ''
                if src and ('.mp4' in src.lower() or '.m3u8' in src.lower()):
                    stream_url = src
                    break

        # 3. Falls immer noch nichts: Direkte Video-URLs aus Script-Blöcken isolieren
        if not stream_url:
            matches = re.findall(r'(https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*)', res.text)
            for m in matches:
                if not any(x in m.lower() for x in ['preview', 'trailer', 'short', 'thumb', 'sample']):
                    stream_url = m.replace('\\/', '/')
                    break

        if stream_url:
            # Baue Kodi-Header als Suffix an die Stream-URL an
            headers_pipe = f"User-Agent={urllib.parse.quote(HEADERS['User-Agent'])}&Referer={urllib.parse.quote(video_url)}"
            final_url = f"{stream_url}|{headers_pipe}" if '|' not in stream_url else stream_url

            play_item = xbmcgui.ListItem(path=final_url)
            if '.m3u8' in stream_url.lower():
                play_item.setMimeType('application/vnd.apple.mpegurl')
            else:
                play_item.setMimeType('video/mp4')

            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmcgui.Dialog().notification('Fehler', 'Kein abspielbarer Stream gefunden', xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

    except Exception as e:
        xbmc.log(f"[MyCumination] Fehler beim Abspielen: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

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
