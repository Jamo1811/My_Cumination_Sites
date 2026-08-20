import sys
import urllib.parse
from bs4 import BeautifulSoup
import cloudscraper
import xbmcgui
import xbmcplugin

# Kodi Parameter auslesen
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
PARAMS = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))

# Hauptdomain definieren
TARGET_DOMAIN = "darknessporn.com"

# Liste von Wörtern/Domains, die ignoriert werden sollen
EXCLUDE_KEYWORDS = [
    'neurogrid7', 'rmhfrtnd', 'trklinkcm', 'zlink7', 'trustpears', 
    'cmonbae', 'punishworld', 'femdoms', 'theporndude', 'thepornlinks',
    'terms-of-use', 'upload', '/tr/', '/uk/', '/vi/', '/zh-CN/'
]

def fetch_and_parse(target_url):
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

    try:
        response = scraper.get(target_url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        xbmcgui.Dialog().notification('Fehler beim Laden', str(e), xbmcgui.NOTIFICATION_ERROR)
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    items = []

    links_container = soup.find('div', id='links')

    if links_container:
        for a_tag in links_container.find_all('a', href=True):
            link = a_tag['href'].strip()
            raw_title = a_tag.text.strip()

            # 1. Nur Links zulassen, die zur Zielseite gehören
            if TARGET_DOMAIN not in link and not link.startswith('/'):
                continue

            # 2. Bekannte Werbe- und Sprach-Links filtern
            if any(keyword in link for keyword in EXCLUDE_KEYWORDS):
                continue

            # 3. Anker-Links (#) oder leere Links ignorieren
            if link.endswith('#') or link == 'https://' + TARGET_DOMAIN + '/':
                continue

            # Titel aus der URL generieren
            clean_title = raw_title
            if not clean_title or clean_title.startswith('http') or clean_title == '#':
                path_segment = link.rstrip('/').split('/')[-1]
                clean_title = path_segment.replace('-', ' ').title()

            if not clean_title:
                continue

            items.append({
                'title': clean_title,
                'url': link,
                'thumb': ''
            })

    return items


def list_directory(site_url):
    xbmcplugin.setContent(HANDLE, 'videos')
    items = fetch_and_parse(site_url)

    for item in items:
        list_item = xbmcgui.ListItem(label=item['title'])

        is_playable = item['url'].endswith(('.mp4', '.m3u8', '.mkv', '.avi'))

        if is_playable:
            url = item['url']
            list_item.setProperty('IsPlayable', 'true')
            is_folder = False
        else:
            url = f"{BASE_URL}?action=browse&url={urllib.parse.quote_plus(item['url'])}"
            is_folder = True

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=is_folder)

    xbmcplugin.endOfDirectory(HANDLE)


# Haupt-Steuerung
action = PARAMS.get('action')
url_param = PARAMS.get('url')

if action == 'browse' and url_param:
    list_directory(url_param)
else:
    START_URL = f'https://{TARGET_DOMAIN}'
    list_directory(START_URL)
