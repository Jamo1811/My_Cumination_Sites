import sys
import re
import urllib.parse
import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
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

PROXY_PORT = 18999
PROXY_SERVER = None

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Deaktiviere nervige Spam-Logs

    def do_GET(self):
        try:
            # Pfad parsen: /proxy?url=ENCODED_URL&ref=ENCODED_REF
            parsed_path = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_path.query)
            
            target_url = params.get('url', [None])[0]
            referer = params.get('ref', [None])[0]

            if not target_url:
                self.send_error(400, "Missing target URL")
                return

            req_headers = {
                'User-Agent': USER_AGENT,
                'Referer': referer if referer else target_url,
            }

            # Leite Range-Header von Kodi/FFmpeg direkt an den Hoster weiter
            if 'Range' in self.headers:
                req_headers['Range'] = self.headers['Range']

            resp = requests.get(target_url, headers=req_headers, stream=True, timeout=15)

            self.send_response(resp.status_code)
            for k, v in resp.headers.items():
                if k.lower() in ['content-type', 'content-length', 'content-range', 'accept-ranges']:
                    self.send_header(k, v)
            self.end_headers()

            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    self.wfile.write(chunk)

        except Exception as e:
            xbmc.log(f"[MyCumination Proxy Error]: {str(e)}", level=xbmc.LOGERROR)

def start_proxy_if_needed():
    global PROXY_SERVER
    if PROXY_SERVER is None:
        try:
            PROXY_SERVER = HTTPServer(('127.0.0.1', PROXY_PORT), ProxyHandler)
            t = threading.Thread(target=PROXY_SERVER.serve_forever)
            t.daemon = True
            t.start()
            xbmc.log(f"[MyCumination] Proxy Server gestartet auf Port {PROXY_PORT}", level=xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"[MyCumination Proxy Start Failed]: {str(e)}", level=xbmc.LOGERROR)

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

def extract_stream(session, page_url):
    res = session.get(page_url, timeout=10)
    html = res.text

    matches = re.findall(r'(https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*)', html)
    for m in matches:
        clean = m.replace('\\/', '/')
        if not any(x in clean.lower() for x in ['preview', 'trailer', 'short', 'thumb']):
            return clean

    soup = BeautifulSoup(html, 'html.parser')
    for iframe in soup.find_all('iframe', src=True):
        src = iframe['src']
        if not src.startswith('http'):
            src = urllib.parse.urljoin(page_url, src)

        try:
            sub = extract_stream(session, src)
            if sub:
                return sub
        except Exception:
            pass

    return None

def play_video(video_url):
    try:
        start_proxy_if_needed()

        session = requests.Session()
        session.headers.update(HEADERS)
        session.headers['Referer'] = video_url

        stream_url = extract_stream(session, video_url)

        if stream_url:
            # Baue eine rein lokale URL, damit Kodi nur mit localhost kommuniziert
            proxy_url = f"http://127.0.0.1:{PROXY_PORT}/proxy?url={urllib.parse.quote(stream_url)}&ref={urllib.parse.quote(video_url)}"

            play_item = xbmcgui.ListItem(path=proxy_url)
            play_item.setContentLookup(False)
            play_item.setMimeType('video/mp4')

            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmcgui.Dialog().notification('Fehler', 'Kein Stream gefunden', xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

    except Exception as e:
        xbmc.log(f"[MyCumination ERROR]: {str(e)}", level=xbmc.LOGERROR)
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
