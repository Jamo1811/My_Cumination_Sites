# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin
from urllib.parse import urlencode

class Site:
    def __init__(self):
        self.handle = int(sys.argv[1])
        self.base_url = sys.argv[0]

    def build_url(self, query):
        return f"{self.base_url}?{urlencode(query)}"

    def add_dir(self, title, url, action, image=""):
        link_url = self.build_url({'action': action, 'url': url})
        item = xbmcgui.ListItem(label=title)
        if image:
            item.setArt({'thumb': image, 'icon': image})
        xbmcplugin.addDirectoryItem(handle=self.handle, url=link_url, listitem=item, isFolder=True)

    def add_item(self, item_obj):
        link_url = self.build_url({'action': item_obj.action, 'url': item_obj.url})
        item = xbmcgui.ListItem(label=item_obj.title)
        if item_obj.image:
            item.setArt({'thumb': item_obj.image, 'icon': item_obj.image})
        
        # Markiert den Eintrag als abspielbares Video
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle=self.handle, url=link_url, listitem=item, isFolder=item_obj.is_folder)

