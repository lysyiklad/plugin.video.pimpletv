# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon

import default
from resources.lib.plugin import PimpletvPlugin

class Monitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.id = xbmcaddon.Addon().getAddonInfo('id')

    def onSettingsChanged(self):        
        default.plugin.settings_changed = True
        default.plugin.update()
        xbmc.executebuiltin('Container.Refresh()')


if __name__ == "__main__":
    monitor = Monitor()
    while not monitor.abortRequested():
        default.plugin.log('START SERVICE!')
        default.plugin.update()
        xbmc.executebuiltin('Container.Refresh()')
        default.plugin.log('STOP SERVICE!')
        if monitor.waitForAbort(600):
            break
