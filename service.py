# -*- coding: utf-8 -*-

import os
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
        if default.plugin.get_setting('full_reset'):
            default.plugin.set_setting('full_reset', False)
            default.plugin.log('START FULL RESET')
            default.plugin.remove_all_thumb()
        
        default.plugin.update()
        default.plugin.settings_changed = False
        xbmc.executebuiltin('Container.Refresh()')


if __name__ == "__main__":
    monitor = Monitor()
    while not monitor.abortRequested():
        default.plugin.log('START SERVICE!')
        default.plugin.update()        
        default.plugin.log('STOP SERVICE!')
        if monitor.waitForAbort(default.plugin.get_setting('delta_scan') * 60 * 1000):
            break
