# -*- coding: utf-8 -*-

import os
import xbmc
#import xbmcgui
# import xbmcaddon


from default import plugin
from resources.lib.plugin import Plugin

# Настройки после которых требуется обновление данных
SETTING_UPDATE = [
    'url_site',
    'time_zone_site',
    'is_poster',
    'is_thumb',
    'is_fanart',
    'is_play',
    'is_pars_links',
    'is_noold_item',
    'theme_artwork',
]

class Monitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self._settings = self._get_settings()

    def _get_settings(self):
        noupdate = {}
        for name_setting in SETTING_UPDATE:
            noupdate[name_setting] = plugin.get_setting(name_setting)
        return noupdate

    def onSettingsChanged(self):
        super(Monitor, self).onSettingsChanged()
        new_settings = self._get_settings()
        if new_settings != self._settings:
            if new_settings['theme_artwork'] != self._settings['theme_artwork']:
                plugin.reset()
            else:
                plugin.on_settings_changed()
            self._settings = new_settings
            xbmc.executebuiltin('Container.Refresh()')


if __name__ == "__main__":
    monitor = Monitor()
    while not monitor.abortRequested():
        if plugin.get_setting('is_update_service'):
            if not xbmc.Player().isPlaying():
                plugin.log('START SERVICE!')
                plugin.update()
                plugin.log('STOP SERVICE!')
        if monitor.waitForAbort(plugin.get_setting('scan_service') * 60):
            break
