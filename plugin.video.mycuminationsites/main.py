def play_video(video_url):
    try:
        # Header inklusive Referer, damit der Stream-Server nicht blockiert
        headers = HEADERS.copy()
        headers['Referer'] = video_url

        response = requests.get(video_url, headers=headers, timeout=10)
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
        
        # 2. Suche nach MP4 / M3U8 URLs per RegEx im Quelltext
        if not stream_url:
            matches = re.findall(r'https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*', html)
            if matches:
                stream_url = matches[0]

        # Stream an Kodi mit Referer-Header übergeben
        if stream_url:
            # Kodi mitgeben, dass beim Abspielen der Referer mitgesendet werden muss
            final_stream_url = f"{stream_url}|User-Agent={urllib.parse.quote(headers['User-Agent'])}&Referer={urllib.parse.quote(video_url)}"
            
            xbmc.log(f"[MyCumination] Stream gefunden: {final_stream_url}", level=xbmc.LOGINFO)
            play_item = xbmcgui.ListItem(path=final_stream_url)
            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmc.log(f"[MyCumination] Kein Stream auf {video_url} gefunden.", level=xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Fehler', 'Kein direkter Stream-Link gefunden', xbmcgui.NOTIFICATION_ERROR)
            
    except Exception as e:
        xbmc.log(f"[MyCumination] Abspiel-Fehler: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', 'Wiedergabe fehlgeschlagen', xbmcgui.NOTIFICATION_ERROR)
