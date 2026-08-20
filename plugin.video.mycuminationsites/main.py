import re

def play_video(video_url):
    try:
        response = requests.get(video_url, headers=HEADERS, timeout=10)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        stream_url = None
        
        # 1. Direkter Video/Source-Tag
        video_element = soup.find('video')
        if video_element:
            source = video_element.find('source')
            if source and source.get('src'):
                stream_url = source.get('src')
            elif video_element.get('src'):
                stream_url = video_element.get('src')
        
        # 2. Suche per RegEx nach MP4 oder M3U8 Links im JS-Code
        if not stream_url:
            match = re.search(r'file\s*:\s*["\'](https?://[^"\']+\.(?:mp4|m3u8)[^"\']*)["\']', html)
            if match:
                stream_url = match.group(1)
                
        if not stream_url:
            match_source = re.search(r'src\s*=\s*["\'](https?://[^"\']+\.(?:mp4|m3u8)[^"\']*)["\']', html)
            if match_source:
                stream_url = match_source.group(1)

        # 3. Falls Iframe genutzt wird
        if not stream_url:
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                stream_url = iframe.get('src')

        # Stream an Kodi übergeben
        if stream_url:
            xbmc.log(f"[MyCumination] Stream gefunden: {stream_url}", level=xbmc.LOGINFO)
            play_item = xbmcgui.ListItem(path=stream_url)
            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmc.log(f"[MyCumination] Kein Stream auf {video_url} gefunden.", level=xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Fehler', 'Kein direkter Stream-Link gefunden', xbmcgui.NOTIFICATION_ERROR)
            
    except Exception as e:
        xbmc.log(f"[MyCumination] Abspiel-Fehler: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', 'Wiedergabe fehlgeschlagen', xbmcgui.NOTIFICATION_ERROR)
