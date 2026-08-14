# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import urllib.error
import xbmc
import xbmcgui
import xbmcvfs

# ==============================================================================
# HIER DEINE DATEN ANPASSEN
# ==============================================================================
GITHUB_USER = "jamo1811"       # Trage hier deinen GitHub-Benutzernamen ein
GITHUB_REPO = "my-cumination-sites" # Trage hier deinen Repo-Namen ein
BRANCH = "main"                     

# Füge hier deinen kopierten Schlüssel ein:
GITHUB_TOKEN = "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"

DEST_DIR = xbmcvfs.translatePath(
    "special://home/addons/plugin.video.cumination/resources/lib/sources/custom_sites/"
)

HEADERS = {
    "User-Agent": "Kodi-CustomSite-Downloader/1.0",
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def notify(message, heading="GH-Downloader", icon=xbmcgui.NOTIFICATION_INFO, time=3000):
    xbmcgui.Dialog().notification(heading, message, icon, time)


def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[Custom-GHDownloader] {msg}", level)


def sync_github_sites():
    log("Starte Synchronisation mit privatem GitHub-Repo...")

    if not os.path.exists(DEST_DIR):
        try:
            os.makedirs(DEST_DIR)
        except Exception as e:
            log(f"Konnte Zielordner nicht erstellen: {str(e)}", xbmc.LOGERROR)
            notify("Ordner-Fehler!", icon=xbmcgui.NOTIFICATION_ERROR)
            return

    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?ref={BRANCH}"
    req = urllib.request.Request(api_url, headers=HEADERS)

    try:
        notify("Prüfe privates Repo...", time=2000)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                notify("Zugriff verweigert!", icon=xbmcgui.NOTIFICATION_ERROR)
                return
            
            files = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        log(f"HTTP Fehler {e.code}: {e.reason}", xbmc.LOGERROR)
        if e.code == 401 or e.code == 404:
            notify("Token ungültig oder Repo nicht gefunden!", icon=xbmcgui.NOTIFICATION_ERROR)
        else:
            notify(f"GitHub Fehler {e.code}", icon=xbmcgui.NOTIFICATION_ERROR)
        return
    except Exception as e:
        log(f"Fehler: {str(e)}", xbmc.LOGERROR)
        notify("Verbindungsfehler!", icon=xbmcgui.NOTIFICATION_ERROR)
        return

    updated_count = 0
    failed_count = 0

    for item in files:
        file_name = item.get("name", "")
        file_api_url = item.get("url")

        if item.get("type") == "file" and file_name.endswith(".py") and file_name != "custom_ghdownloader.py":
            target_file_path = os.path.join(DEST_DIR, file_name)
            
            raw_headers = HEADERS.copy()
            raw_headers["Accept"] = "application/vnd.github.v3.raw"

            try:
                raw_req = urllib.request.Request(file_api_url, headers=raw_headers)
                with urllib.request.urlopen(raw_req, timeout=15) as resp:
                    file_content = resp.read()
                    with open(target_file_path, "wb") as f:
                        f.write(file_content)
                updated_count += 1
                log(f"Erfolgreich geladen: {file_name}")
            except Exception as e:
                failed_count += 1
                log(f"Fehler bei {file_name}: {str(e)}", xbmc.LOGERROR)

    if updated_count > 0:
        notify(f"{updated_count} Skripte aktualisiert!")
    elif failed_count > 0:
        notify("Download-Fehler!", icon=xbmcgui.NOTIFICATION_WARNING)
    else:
        notify("Keine Skripte gefunden.")


if __name__ == "__main__":
    sync_github_sites()

