import sys
import re
import urllib.request
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# ==================== GRUNDKONFIGURATION ====================
handle = int(sys.argv[1])
base_url = sys.argv[0]
addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')

# WICHTIG: User-Agent OHNE Leerzeichen (oder encoded)
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
REFERER = 'https://darknessporn.com/'

# ==================== HILFSFUNKTIONEN ====================

def fetch_html(url):
    """Lädt eine HTML-Seite"""
    req = urllib.request.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('Referer', REFERER)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        xbmc.log(f'{addon_name}: Fehler: {e}', xbmc.LOGERROR)
        return None

def try_resolveurl(video_url):
    """Versucht ResolveURL (falls installiert)"""
    try:
        from resolveurl import resolveurl
        resolved = resolveurl.resolve(video_url)
        if resolved:
            return resolved
    except ImportError:
        xbmc.log(f'{addon_name}: ResolveURL nicht gefunden', xbmc.LOGINFO)
    except:
        pass
    return video_url

# ==================== EXTRAKTIONS-LOGIK (MUSS ANGEPASST WERDEN!) ====================

def extract_video_url_from_page(html):
    """
    Extrahiert die eigentliche Video-URL aus dem HTML der Seite.
    DAS MUSST DU AN DIE AKTUELLE SEITE ANPASSEN!
    """
    # 1. Versuche iframe zu finden (häufig bei eingebetteten Videos)
    iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if iframe_match:
        return iframe_match.group(1)
    
    # 2. Versuche direkte Video-URL (mp4, m3u8, etc.)
    video_match = re.search(r'(https?://[^\s"\']+\.(?:mp4|m3u8|ts)[^\s"\']*)', html, re.IGNORECASE)
    if video_match:
        return video_match.group(1)
    
    # 3. Versuche JavaScript-Variable (z.B. file: "https://...")
    js_match = re.search(r'(?:file|src|video_url)\s*[:=]\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
    if js_match:
        return js_match.group(1)
    
    return None

def extract_video_url_from_iframe(iframe_url):
    """
    Lädt die iframe-Seite (vom Hoster) und extrahiert dort die Video-URL.
    DAS MUSST DU AN DEN HOSTER ANPASSEN!
    """
    html = fetch_html(iframe_url)
    if not html:
        return None
    
    # Versuche verschiedene Patterns (häufig bei Hostern)
    patterns = [
        r'(?:file|src|video)\s*[:=]\s*["\']([^"\']+\.(?:mp4|m3u8))["\']',
        r'<video[^>]+src=["\']([^"\']+)["\']',
        r'data-video-url=["\']([^"\']+)["\']',
        r'{"file":"([^"]+)"}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

# ==================== MENÜ-STRUKTUR ====================

def show_video_list():
    """Zeigt eine Liste von Videos (hier als Beispiel)"""
    # In der Praxis: Lade die Hauptseite und parse die Videolinks
    # Beispiel: 3 statische Einträge zum Testen
    videos = [
        {'title': 'Test Video 1', 'url': 'https://darknessporn.com/video/123'},
        {'title': 'Test Video 2', 'url': 'https://darknessporn.com/video/456'},
    ]
    
    for video in videos:
        list_item = xbmcgui.ListItem(label=video['title'])
        list_item.setInfo('video', {'title': video['title']})
        url = base_url + '?action=play&url=' + urllib.parse.quote(video['url'])
        xbmcplugin.addDirectoryItem(handle, url, list_item, isFolder=False)
    
    xbmcplugin.endOfDirectory(handle)

# ==================== ABSPIELEN ====================

def play_video(video_url):
    """Spielt ein Video mit korrekten Headern ab"""
    xbmc.log(f'{addon_name}: Versuche URL: {video_url}', xbmc.LOGINFO)
    
    # 1. Zuerst ResolveURL versuchen
    final_url = try_resolveurl(video_url)
    
    # 2. Wenn ResolveURL nichts gefunden hat: Selbst scrapen
    if final_url == video_url:
        xbmc.log(f'{addon_name}: ResolveURL fehlgeschlagen, scrape selbst', xbmc.LOGINFO)
        html = fetch_html(video_url)
        if html:
            # Zuerst in der Seite selbst suchen
            found_url = extract_video_url_from_page(html)
            if found_url:
                # Wenn es ein iframe ist, diesen ebenfalls laden
                if 'iframe' in found_url.lower() or found_url.startswith('//'):
                    final_url = extract_video_url_from_iframe(found_url)
                else:
                    final_url = found_url
            else:
                xbmcgui.Dialog().ok(addon_name, 'Keine Video-URL in der Seite gefunden')
                return
    
    if not final_url:
        xbmcgui.Dialog().ok(addon_name, 'Video-URL konnte nicht aufgelöst werden')
        return
    
    xbmc.log(f'{addon_name}: Finale URL: {final_url}', xbmc.LOGINFO)
    
    # 3. Kodi-Player vorbereiten
    list_item = xbmcgui.ListItem()
    list_item.setPath(final_url)
    
    # Wichtig: User-Agent URL-encoden (wegen Leerzeichen!)
    encoded_ua = urllib.parse.quote(USER_AGENT)
    encoded_ref = urllib.parse.quote(REFERER)
    headers = f'User-Agent={encoded_ua}&Referer={encoded_ref}'
    
    list_item.setProperty('inputstream.adaptive.stream_headers', headers)
    list_item.setProperty('http-user-agent', USER_AGENT)
    list_item.setProperty('http-referer', REFERER)
    
    # Für HLS/DASH-Streams (falls nötig)
    if '.m3u8' in final_url:
        list_item.setProperty('inputstream', 'inputstream.adaptive')
        list_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    
    xbmcplugin.setResolvedUrl(handle, succeeded=True, listitem=list_item)

# ==================== ROUTER ====================

def router(paramstring):
    """Leitet Anfragen weiter"""
    params = dict(urllib.parse.parse_qsl(paramstring))
    
    if 'action' in params and params['action'] == 'play':
        video_url = urllib.parse.unquote(params['url'])
        play_video(video_url)
    else:
        show_video_list()

# ==================== START ====================

if __name__ == '__main__':
    router(sys.argv[2][1:])
