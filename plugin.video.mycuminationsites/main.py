import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin

def play_video(video_url, page_url):
    try:
        # 1. Header definieren, die der CDN-Server fordert
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': page_url  # Die URL der Video-Detailseite
        }
        
        # 2. Header für Kodis FFmpeg-Player mit Pipe '|' anhängen
        header_string = urllib.parse.urlencode(headers)
        stream_url_with_headers = f"{video_url}|{header_string}"
        
        # 3. ListItem aufbauen und Inhaltsprüfung deaktivieren
        play_item = xbmcgui.ListItem(path=stream_url_with_headers)
        play_item.setContentLookup(False)  # Verhindert, dass Kodi den Stream vorab scannt
        play_item.setMimeType('video/mp4')
        
        # 4. An Kodi übergeben
        xbmcplugin.setResolvedUrl(HANDLE, True, play_item)

    except Exception as e:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
