def play_video(video_url):
    try:
        headers = HEADERS.copy()
        headers['Referer'] = video_url

        session = requests.Session()
        response = session.get(video_url, headers=headers, timeout=15)
        html = response.text
        
        stream_url = None

        # 1. Suche nach JavaScript-Variablen (wie video_url = "https://...")
        js_matches = re.findall(r'(?:video_url|file|src|stream_url)\s*[:=]\s*["\'](https?://[^\'\"]+\.(?:mp4|m3u8)[^\'\"]*)["\']', html, re.IGNORECASE)
        for match in js_matches:
            if not any(x in match.lower() for x in ['preview', 'trailer', 'short', 'gif', 'taser', 'thumb']):
                stream_url = match
                break

        # 2. Suche in <video> und <source> Tags
        if not stream_url:
            soup = BeautifulSoup(html, 'html.parser')
            for src_tag in soup.find_all(['source', 'video']):
                link = src_tag.get('src') or src_tag.get('data-src') or ''
                if link and not any(x in link.lower() for x in ['preview', 'trailer', 'short', 'gif']):
                    stream_url = link
                    break

        # 3. Allgemeiner Regex Fallback (Filtert Thumbnails/Previews aus)
        if not stream_url:
            matches = re.findall(r'https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*', html)
            for match in matches:
                if not any(x in match.lower() for x in ['preview', 'trailer', 'short', 'gif', 'taser', 'thumb']):
                    stream_url = match
                    break

        # 4. Falls die Seite in einen iframe ausweicht
        if not stream_url:
            soup = BeautifulSoup(html, 'html.parser')
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                iframe_url = iframe.get('src')
                if iframe_url.startswith('//'):
                    iframe_url = 'https:' + iframe_url
                iframe_resp = session.get(iframe_url, headers=headers, timeout=10)
                iframe_matches = re.findall(r'https?://[^\s\'"]+\.(?:mp4|m3u8)[^\s\'"]*', iframe_resp.text)
                for match in iframe_matches:
                    if not any(x in match.lower() for x in ['preview', 'trailer', 'short', 'gif']):
                        stream_url = match
                        break

        if stream_url:
            # HTML Entities dekodieren (z.B. &amp; zu &)
            stream_url = urllib.parse.unquote(stream_url).replace('&amp;', '&')
            
            final_stream_url = f"{stream_url}|User-Agent={urllib.parse.quote(headers['User-Agent'])}&Referer={urllib.parse.quote(video_url)}"
            play_item = xbmcgui.ListItem(path=final_stream_url)
            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmcgui.Dialog().notification('Fehler', 'Kein Hauptstream gefunden', xbmcgui.NOTIFICATION_ERROR)
            
    except Exception as e:
        xbmc.log(f"[MyCumination] Abspiel-Fehler: {str(e)}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Fehler', str(e), xbmcgui.NOTIFICATION_ERROR)
