# -*- coding: utf-8 -*-
import os
import json
import urllib2
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib

from resources.lib.pimpletv import PimpleTV
from resources.lib.plugin import PimpletvPlugin


# addon = xbmcaddon.Addon()
# addon_path = addon.getAddonInfo('path')
# addonID = addon.getAddonInfo('id')


plugin = PimpletvPlugin()

pimpletv = PimpleTV(plugin)

@plugin.action()
def root():    
    return plugin.create_listing(pimpletv.matches(), content='movies', sort_methods=(xbmcplugin.SORT_METHOD_DATEADDED, xbmcplugin.SORT_METHOD_VIDEO_RATING), cache_to_disk=True)


if __name__ == '__main__':
    plugin.run()
