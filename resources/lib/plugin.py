# -*- coding: utf-8 -*-

import os
import xbmc
import simpleplugin


class PimpletvPlugin(simpleplugin.Plugin):

    def __init__(self):
        super(PimpletvPlugin, self).__init__()
        self._dir = {
            'media': os.path.join(self.path, 'resources', 'media'), 
            'font': os.path.join(self.path, 'resources', 'data', 'font'),
            'lib': os.path.join(self.path, 'resources', 'lib'),
            'userdata': xbmc.translatePath(self.addon.getAddonInfo('profile')),
        }        
        self._dir['thumb'] = os.path.join(self._dir['userdata'], 'thumb')
    
    def dir(self, dir):
        return self._dir[dir]    

    # def media(self):
    #     return os.path.join(self.path, 'resources', 'media')

    # def font(self):
    #     return os.path.join(self.path, 'resources', 'data', 'font')

    # def lib(self):
    #     return os.path.join(self.path, 'resources', 'lib')

    # def userdata(self):
    #     return xbmc.translatePath(self.addon.getAddonInfo('profile'))
        
    @property
    def version_kodi(self):
        return int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    def get_cache_thumb_name(self, thumb):
        thumb_cached = xbmc.getCacheThumbName(thumb)
        thumb_cached = thumb_cached.replace('tbn', 'png')
        return os.path.join(os.path.join(xbmc.translatePath("special://thumbnails"), thumb_cached[0], thumb_cached))   
