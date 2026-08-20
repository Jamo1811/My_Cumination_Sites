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

# ==================== HILFSFUNKTIONEN ====================

def log(msg):
    xbmc.log(f'{addon_name}: {msg}', xbmc.LOGINFO)

def fetch_html(url):
    """Lädt eine HTML-Seite"""
    req = urllib.request.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('Referer', REFERER)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        log(f'Fehler: {e}')
        return None

def extract_video_url(html):
    """Extrahiert die MP4-URL aus der Seite"""
    # Suche nach nosofiles.com URLs (wie in deinem Screenshot)
    patterns = [
        r'(https?://st1\.nosofiles\.com/[^\s"\']+\.mp4[^\s"\']*)',
        r'(https?://[^\s"\']+\.mp4[^\s"\']*)',
        r'(https?://[^\s"\']+/trailer\.mp4[^\s"\']*)',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def try_resolveurl(url):
    """Versucht ResolveURL"""
    try:
        from resolveurl import resolveurl
        resolved = resolveurl.resolve(url)
        if resolved:
            log(f'ResolveURL: {resolved}')
            return resolved
    except:
        pass
    return None

# ==================== VIDEO-LISTE ====================

def show_video_list():
    """Zeigt eine Liste von Videos"""
    # HIER MÜSSEN ECHTE VIDEO-LINKS VON DARKNESSPORN.COM REIN!
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
    log(f'Starte: {video_url}')
    
    # 1. Seite laden
    html = fetch_html(video_url)
    if not html:
        xbmcgui.Dialog().ok(addon_name, 'Seite konnte nicht geladen werden')
        return
    
    # 2. Direkt nach MP4-URL suchen
    final_url = extract_video_url(html)
    
    # 3. Wenn keine MP4: ResolveURL versuchen
    if not final_url:
        # Suche nach Embed-Link
        embed_match = re.search(r'(https?://darknessporn\.com/embed/\d+)', html)
        if embed_match:
            log(f'Embed gefunden: {embed_match.group(1)}')
            final_url = try_resolveurl(embed_match.group(1))
    
    # 4. Wenn immer noch nichts: Dialog mit gefundenen URLs
    if not final_url:
        # Extrahiere alle URLs für Debug
        all_urls = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8)[^\s"\']*)', html)
        if all_urls:
            msg = 'Gefundene URLs:\n' + '\n'.join(all_urls[:3])
            xbmcgui.Dialog().ok(addon_name, msg)
        else:
            xbmcgui.Dialog().ok(addon_name, 'Keine Video-URL gefunden!')
        return
    
    log(f'FINALE URL: {final_url}')
    
    # 5. Kodi-Player vorbereiten
    list_item = xbmcgui.ListItem()
    list_item.setPath(final_url)
    
    # User-Agent encoden
    encoded_ua = urllib.parse.quote(USER_AGENT)
    headers = f'User-Agent={encoded_ua}&Referer={urllib.parse.quote(REFERER)}'
    list_item.setProperty('inputstream.adaptive.stream_headers', headers)
    list_item.setProperty('http-user-agent', USER_AGENT)
    list_item.setProperty('http-referer', REFERER)
    
    # Für HLS-Streams
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
