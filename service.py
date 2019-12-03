# -*- coding: utf-8 -*-

import os
import xbmc
import xbmcgui
# import xbmcaddon


import default
from resources.lib.plugin import Plugin


class Monitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)

    def onSettingsChanged(self):
        super(Monitor, self).onSettingsChanged()
        default.plugin.on_settings_changed()
        xbmc.executebuiltin('Container.Refresh()')


if __name__ == "__main__":
    monitor = Monitor()
    while not monitor.abortRequested():        
        default.plugin.log('START SERVICE!')
        default.plugin.update()
        default.plugin.log('STOP SERVICE!')
        if monitor.waitForAbort(default.plugin.get_setting('delta_scan') * 60 * 1000):
            break
