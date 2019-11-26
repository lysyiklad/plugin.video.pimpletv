# -*- coding: utf-8 -*-

import os
import xbmc


import simpleplugin

class PimpletvPlugin(simpleplugin.Plugin):

    def media(self):
        return os.path.join(self.path, 'resources', 'media')

    def font(self):
        return os.path.join(self.path, 'resources', 'data', 'font')

    def lib(self):
        return os.path.join(self.path, 'resources', 'lib')

    def userdata(self):
        return xbmc.translatePath(self.addon.getAddonInfo('profile'))

    def get_cache_thumb_name(self, thumb):
        thumb_cached = xbmc.getCacheThumbName(thumb)
        thumb_cached = thumb_cached.replace('tbn', 'png')
        return os.path.join(os.path.join(xbmc.translatePath("special://thumbnails"), thumb_cached[0], thumb_cached))

    def get_setting(self, param, t):
        setting = {
            'is_thumb': False,
            'is_fanart': False,
            'delta_scan': 0,
        }
        return setting[param]
