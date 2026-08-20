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

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
REFERER = 'https://darknessporn.com/'

# ==================== VIDEO-LISTE ====================

def show_video_list():
    """Zeigt eine Liste von Videos"""
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

# ==================== VIDEO-URL EXTRAHIEREN ====================

def fetch_html(url):
    """Lädt eine HTML-Seite"""
    req = urllib.request.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('Referer', REFERER)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        xbmc.log(f'{addon_name}: Fehler: {e}', xbmc.LOGERROR)
        return None

def extract_video_url(html):
    """Extrahiert die echte Video-URL (nicht Trailer!)"""
    # Suche nach output_...-URLs (die echten Videos)
    patterns = [
        r'(https?://st1\.nosofiles\.com/[^\s"\']*output_[a-f0-9-]+\.mp4[^\s"\']*)',
        r'(https?://[^\s"\']+\.mp4[^\s"\']*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        # Filtere Trailer aus
        real_urls = [u for u in matches if 'trailer' not in u.lower()]
        if real_urls:
            # Nimm die längste URL (meist das Hauptvideo)
            return max(real_urls, key=len)
    
    return None

# ==================== ABSPIELEN ====================

def play_video(video_url):
    xbmc.log(f'{addon_name}: Starte: {video_url}', xbmc.LOGINFO)
    
    # 1. Seite laden
    html = fetch_html(video_url)
    if not html:
        xbmcgui.Dialog().ok(addon_name, 'Seite konnte nicht geladen werden')
        return
    
    # 2. Video-URL extrahieren
    final_url = extract_video_url(html)
    
    if not final_url:
        xbmcgui.Dialog().ok(addon_name, 'Keine Video-URL gefunden')
        return
    
    xbmc.log(f'{addon_name}: Finale URL: {final_url}', xbmc.LOGINFO)
    
    # 3. Kodi-Player vorbereiten
    list_item = xbmcgui.ListItem()
    list_item.setPath(final_url)
    
    # User-Agent encoden
    encoded_ua = urllib.parse.quote(USER_AGENT)
    headers = f'User-Agent={encoded_ua}&Referer={urllib.parse.quote(REFERER)}'
    list_item.setProperty('inputstream.adaptive.stream_headers', headers)
    list_item.setProperty('http-user-agent', USER_AGENT)
    list_item.setProperty('http-referer', REFERER)
    
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
