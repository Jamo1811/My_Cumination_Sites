import sys
import re
import urllib.request
import urllib.parse
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# ==================== GRUNDKONFIGURATION ====================
handle = int(sys.argv[1])
base_url = sys.argv[0]
addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
REFERER = 'https://darknessporn.com/'

# ==================== HILFSFUNKTIONEN ====================

def log(msg):
    xbmc.log(f'{addon_name}: {msg}', xbmc.LOGINFO)

def fetch_html(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('Referer', REFERER)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        log(f'Fehler beim Laden: {e}')
        return None

def extract_all_urls(html):
    """Findet ALLE URLs in der Seite"""
    urls = []
    # Suche nach iframe
    iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    urls.extend(iframes)
    
    # Suche nach Video-URLs
    videos = re.findall(r'(https?://[^\s"\']+\.(?:m3u8|mp4|ts)[^\s"\']*)', html, re.IGNORECASE)
    urls.extend(videos)
    
    # Suche nach JavaScript-Variablen
    js_urls = re.findall(r'(?:file|src|video_url|url)\s*[:=]\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html, re.IGNORECASE)
    urls.extend(js_urls)
    
    # Suche nach embed-Links
    embeds = re.findall(r'(https?://[^\s"\']+/(?:embed|e|v)/[^\s"\']+)', html, re.IGNORECASE)
    urls.extend(embeds)
    
    return list(set(urls))  # Doppelte entfernen

def try_resolveurl(video_url):
    try:
        from resolveurl import resolveurl
        resolved = resolveurl.resolve(video_url)
        if resolved:
            log(f'ResolveURL erfolgreich: {resolved}')
            return resolved
    except:
        pass
    return None

# ==================== VIDEO-LISTE ====================

def show_video_list():
    """Zeigt eine Liste von Videos"""
    # Ersetze diese URLs mit echten Links von darknessporn.com
    videos = [
        {'title': '🔴 Defloration Real Teen', 'url': 'https://darknessporn.com/56493-defloration-real-teen-young-teenies/'},
        {'title': '🔴 Test Video 2', 'url': 'https://darknessporn.com/anderes-video/'},
    ]
    
    for video in videos:
        list_item = xbmcgui.ListItem(label=video['title'])
        list_item.setInfo('video', {'title': video['title']})
        url = base_url + '?action=play&url=' + urllib.parse.quote(video['url'])
        xbmcplugin.addDirectoryItem(handle, url, list_item, isFolder=False)
    
    xbmcplugin.endOfDirectory(handle)

# ==================== ABSPIELEN ====================

def play_video(video_url):
    log(f'Starte mit URL: {video_url}')
    
    # 1. Seite laden
    html = fetch_html(video_url)
    if not html:
        xbmcgui.Dialog().ok(addon_name, 'Seite konnte nicht geladen werden')
        return
    
    # 2. Alle URLs aus der Seite extrahieren
    found_urls = extract_all_urls(html)
    log(f'Gefundene URLs: {found_urls}')
    
    # 3. Versuche jede URL mit ResolveURL
    final_url = None
    for url in found_urls:
        if 'iframe' in url.lower() or 'embed' in url.lower():
            # Iframe/Embed laden und dort weitersuchen
            iframe_html = fetch_html(url)
            if iframe_html:
                more_urls = extract_all_urls(iframe_html)
                log(f'Im Iframe gefunden: {more_urls}')
                for u in more_urls:
                    resolved = try_resolveurl(u)
                    if resolved:
                        final_url = resolved
                        break
        else:
            resolved = try_resolveurl(url)
            if resolved:
                final_url = resolved
                break
        
        if final_url:
            break
    
    # 4. Wenn nichts gefunden: Debug-Dialog anzeigen
    if not final_url:
        # Zeige alle gefundenen URLs im Dialog
        if found_urls:
            msg = 'Gefundene URLs:\n' + '\n'.join(found_urls[:5])
            xbmcgui.Dialog().ok(addon_name, msg)
        else:
            xbmcgui.Dialog().ok(addon_name, 'Keine Video-URL gefunden!')
        return
    
    log(f'FINALE URL: {final_url}')
    
    # 5. Kodi-Player vorbereiten
    list_item = xbmcgui.ListItem()
    list_item.setPath(final_url)
    
    encoded_ua = urllib.parse.quote(USER_AGENT)
    headers = f'User-Agent={encoded_ua}&Referer={urllib.parse.quote(REFERER)}'
    list_item.setProperty('inputstream.adaptive.stream_headers', headers)
    
    if '.m3u8' in final_url:
        list_item.setProperty('inputstream', 'inputstream.adaptive')
        list_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    
    xbmcplugin.setResolvedUrl(handle, True, list_item)

# ==================== ROUTER ====================

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring))
    if 'action' in params and params['action'] == 'play':
        video_url = urllib.parse.unquote(params['url'])
        play_video(video_url)
    else:
        show_video_list()

# ==================== START ====================

if __name__ == '__main__':
    router(sys.argv[2][1:])
