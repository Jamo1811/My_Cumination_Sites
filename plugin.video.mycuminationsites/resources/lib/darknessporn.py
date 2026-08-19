# -*- coding: utf-8 -*-
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from resources.lib.models.site import Site
from resources.lib.models.item import Item
from resources.lib import utils

class CustomSite(Site):
    def __init__(self):
        super().__init__()
        self.name = "DarknessPorn"
        self.base_url = "https://darknessporn.com"
        self.icon = "DefaultFolder.png"

    def get_menu(self):
        """Hauptmenü: Neueste Videos & Kategorien."""
        self.add_dir("Neueste Videos", self.base_url, "list_videos")

        html = utils.get_html(self.base_url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            category_links = soup.select("ul.main-menu a, div.categories-list a, nav a")

            for link in category_links:
                title = link.text.strip()
                href = link.get("href")

                if not href or not title or href == "#" or "javascript" in href:
                    continue

                full_url = urljoin(self.base_url, href)
                self.add_dir(title, full_url, "list_videos")

    def list_videos(self, url):
        """Listet Videos & Paginierung auf."""
        html = utils.get_html(url)
        if not html:
            return

        soup = BeautifulSoup(html, "html.parser")
        video_boxes = soup.select("div.item, article.post, div.video-item, div.loop-video")

        for box in video_boxes:
            link_tag = box.select_one("a")
            img_tag = box.select_one("img")

            if not link_tag:
                continue

            title = link_tag.get("title") or box.select_one(".title, .entry-title")
            if hasattr(title, "text"):
                title = title.text.strip()
            if not title:
                title = link_tag.text.strip() or "Unbenanntes Video"

            video_href = link_tag.get("href")
            if not video_href:
                continue

            video_page_url = urljoin(self.base_url, video_href)

            thumbnail = ""
            if img_tag:
                thumbnail = (
                    img_tag.get("data-src")
                    or img_tag.get("data-lazy-src")
                    or img_tag.get("data-original")
                    or img_tag.get("src")
                    or ""
                )
                thumbnail = urljoin(self.base_url, thumbnail)

            item = Item()
            item.title = title
            item.url = video_page_url
            item.image = thumbnail
            item.action = "play_video"
            item.is_folder = False

            self.add_item(item)

        next_page = soup.select_one("a.next, a.next-page, li.next a, a[rel='next']")
        if next_page and next_page.get("href"):
            next_url = urljoin(self.base_url, next_page.get("href"))
            self.add_dir("[COLOR yellow]Nächste Seite >>[/COLOR]", next_url, "list_videos")

    def play_video(self, url):
        """Resolver für Stream-URLs auf Detailseiten."""
        html = utils.get_html(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        stream_url = None

        video_tag = soup.select_one("video source, video")
        if video_tag and video_tag.get("src"):
            stream_url = video_tag.get("src")

        if not stream_url:
            iframe = soup.select_one("iframe[src*='embed'], div.player-embed iframe")
            if iframe and iframe.get("src"):
                iframe_url = urljoin(self.base_url, iframe.get("src"))
                iframe_html = utils.get_html(iframe_url)
                if iframe_html:
                    iframe_soup = BeautifulSoup(iframe_html, "html.parser")
                    source = iframe_soup.select_one("video source, video")
                    if source and source.get("src"):
                        stream_url = source.get("src")

        if stream_url:
            return urljoin(self.base_url, stream_url)

        return None
