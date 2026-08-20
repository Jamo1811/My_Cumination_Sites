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
        xbmcplugin.setContent(HANDLE, 'videos')
        session = requests.Session()
        response = session.get(category_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
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
            thumb = ''
            if img_tag:
                thumb = img_tag.get('data-src') or img_tag.get('data-original') or img_tag.get('src') or ''

            if title and len(title) > 3:
                added_urls.add(video_url)
                url = build_url({'action': 'play_video', 'video_url': video_url})
                li = xbmcgui.ListItem(label=title)
                if thumb:
                    li.setArt({'thumb': thumb, 'icon': thumb})
                
                # Wir setzen hier isFolder=False, behandeln es aber in play_video als eigenständigen Player-Aufruf
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

        if count == 0:
            xbmcgui.Dialog().notification('Hinweis', 'Keine Videos gefunden', xbmcgui.NOTIFICATION_WARNING)
            
    except Exception as e:
        xbmc.log(f"[MyCumination] Fehler beim Laden: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', str(e), xbmcgui.NOTIFICATION_ERROR)

    xbmcplugin.endOfDirectory(HANDLE)

def play_video(video_url):
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Stream laden', 'Suche Videolink...')

    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        session.headers['Referer'] = video_url

        res = session.get(video_url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        candidates = []

        # 1. Direct HTML5 Tags
        for tag in soup.find_all(['video', 'source']):
            src = tag.get('src') or tag.get('data-src') or ''
            if src and ('.mp4' in src.lower() or '.m3u8' in src.lower()):
                candidates.append(src)

        # 2. iFrames
        for iframe in soup.find_all('iframe', src=True):
            iframe_src = iframe['src']
            if not iframe_src.startswith('http'):
                iframe_src = urllib.parse.urljoin('https://darknessporn.com/', iframe_src)
            try:
                if_res = session.get(iframe_src, timeout=10)
                found = re.findall(r'(https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*)', if_res.text)
                candidates.extend(found)
            except:
                pass

        # 3. RegEx in Javascript
        found_js = re.findall(r'(https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*)', res.text)
        candidates.extend(found_js)

        # Filter
        valid_url = None
        for cand in candidates:
            cand_clean = cand.replace('\\/', '/')
            if not any(x in cand_clean.lower() for x in ['preview', 'trailer', 'short', 'thumb', 'sample']):
                valid_url = cand_clean
                break

        pDialog.close()

        if valid_url:
            # Löse Redirects (z. B. nosofiles.com -> Direct CDN) komplett in Python auf
            try:
                head_res = session.get(valid_url, allow_redirects=True, stream=True, timeout=10)
                final_media_url = head_res.url
                head_res.close()
            except:
                final_media_url = valid_url

            # Erstelle ein sauberes ListItem für den Player
            play_item = xbmcgui.ListItem(path=final_media_url)
            
            # Übermittle User-Agent und Referer direkt an Kodis Netzwerk-Stack
            play_item.setProperty('stream:http_headers', f"User-Agent={HEADERS['User-Agent']}&Referer={video_url}")
            
            # Erzwinge Direktwiedergabe über den Kodi Player
            xbmc.Player().play(item=final_media_url, listitem=play_item)
        else:
            xbmcgui.Dialog().notification('Fehler', 'Kein Videostream gefunden', xbmcgui.NOTIFICATION_ERROR)

    except Exception as e:
        if 'pDialog' in locals():
            pDialog.close()
        xbmc.log(f"[MyCumination] Fehler bei Wiedergabe: {str(e)}", level=xbmc.LOGERROR)
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
