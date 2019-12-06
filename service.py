# -*- coding: utf-8 -*-

import os
import xbmc
import xbmcgui
# import xbmcaddon


from default import plugin
from resources.lib.plugin import Plugin

# Настройки после которых не требуется обновление данных
SETTING_NO_UPDATE = [
    "is_default_ace",
    "default_ace",
    "ipace1",
    "is_hls1",
    "ipace2",
    "is_hls2",
    "ipproxy",
    'delta_scan',
    "delta_links",
]

class Monitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self._settings = self._get_settings()

    def _get_settings(self):
        noupdate = {}
        for name_setting in SETTING_NO_UPDATE:
            noupdate[name_setting] = plugin.get_setting(name_setting)
        return noupdate

    def onSettingsChanged(self):
        super(Monitor, self).onSettingsChanged()
        new_settings = self._get_settings()
        if new_settings == self._settings:
            plugin.on_settings_changed()
            xbmc.executebuiltin('Container.Refresh()')
        else:
            self._settings = new_settings


if __name__ == "__main__":
    monitor = Monitor()
    while not monitor.abortRequested():
        plugin.log('START SERVICE!')
        plugin.update()
        plugin.log('STOP SERVICE!')
        if monitor.waitForAbort(plugin.get_setting('delta_scan') * 60):
            break
