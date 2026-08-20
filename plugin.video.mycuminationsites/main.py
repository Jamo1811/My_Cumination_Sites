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

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

HEADERS = {
    'User-Agent': USER_AGENT,
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
        ('Meistgesehen', 'https://darknessporn.com/?filter=most_viewed', 'list_videos'),
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
        xbmc.log(f"[MyCumination] Versuche abzuspielen: {video_url}", xbmc.LOGINFO)
        
        session = requests.Session()
        session.headers.update(HEADERS)
        
        response = session.get(video_url, headers=HEADERS, timeout=15)
        html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        stream_url = None
        
        # Methode 1: Video-Tag mit src
        video_tag = soup.find('video')
        if video_tag:
            src = video_tag.get('src')
            if src:
                stream_url = src
        
        # Methode 2: source-Tag
        if not stream_url:
            source_tag = soup.find('source')
            if source_tag:
                src = source_tag.get('src')
                if src:
                    stream_url = src
        
        # Methode 3: iframe
        if not stream_url:
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                embed_url = iframe['src']
                try:
                    embed_response = session.get(embed_url, headers=HEADERS, timeout=10)
                    embed_html = embed_response.text
                    embed_soup = BeautifulSoup(embed_html, 'html.parser')
                    embed_video = embed_soup.find('video')
                    if embed_video and embed_video.get('src'):
                        stream_url = embed_video['src']
                except:
                    pass
        
        # Methode 4: Regex
        if not stream_url:
            patterns = [
                r'(https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*)',
                r'(https?://[^\s\'"]+/get_file/[^\s\'"]+)',
                r'(https?://[^\s\'"]+\.php\?[^\s\'"]*video[^\s\'"]*)'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, html)
                for m in matches:
                    clean = m.replace('\\/', '/')
                    if not any(x in clean.lower() for x in ['preview', 'trailer', 'thumb', 'poster']):
                        stream_url = clean
                        break
                if stream_url:
                    break
        
        # Methode 5: JSON
        if not stream_url:
            json_matches = re.findall(r'file\s*:\s*["\']([^"\']+\.(?:mp4|m3u8)[^"\']*)["\']', html)
            if json_matches:
                stream_url = json_matches[0]
        
        if stream_url:
            stream_url = stream_url.replace('\\/', '/')
            if not stream_url.startswith('http'):
                if stream_url.startswith('//'):
                    stream_url = 'https:' + stream_url
                else:
                    stream_url = urllib.parse.urljoin('https://darknessporn.com/', stream_url)
            
            cookie_str = '; '.join([f"{c.name}={c.value}" for c in session.cookies])
            headers_to_send = {
                'User-Agent': USER_AGENT,
                'Referer': video_url,
                'Accept': 'video/mp4,video/webm,video/*',
                'Connection': 'keep-alive'
            }
            if cookie_str:
                headers_to_send['Cookie'] = cookie_str
            
            header_pipe = urllib.parse.urlencode(headers_to_send)
            final_stream_url = f"{stream_url}|{header_pipe}"
            
            try:
                play_item = xbmcgui.ListItem(path=final_stream_url)
                play_item.setContentLookup(False)
                play_item.setMimeType('video/mp4')
                
                if stream_url.endswith('.m3u8'):
                    play_item.setProperty('inputstream', 'inputstream.adaptive')
                    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                
                xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
                xbmc.log("[MyCumination] Wiedergabe gestartet", xbmc.LOGINFO)
                
            except Exception as play_error:
                xbmc.log(f"[MyCumination] Play-Fehler: {play_error}", xbmc.LOGERROR)
                fallback_item = xbmcgui.ListItem(path=stream_url)
                fallback_item.setContentLookup(False)
                xbmcplugin.setResolvedUrl(HANDLE, True, fallback_item)
                
        else:
            xbmc.log("[MyCumination] Kein Stream-Link gefunden", xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Fehler', 'Kein Stream-Link auf der Seite gefunden', xbmcgui.NOTIFICATION_ERROR, 5000)
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
            
    except Exception as e:
        xbmc.log(f"[MyCumination] Allgemeiner Fehler: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', f'Wiedergabefehler: {str(e)[:50]}', xbmcgui.NOTIFICATION_ERROR, 5000)
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
