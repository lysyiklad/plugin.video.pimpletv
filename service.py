# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from future.utils import python_2_unicode_compatible, iteritems
#from resources.libs import TVZavr, TVZavrError
#from simplemedia import py2_decode

import xbmc
#import json
#from simplemedia import Addon

import default

#@python_2_unicode_compatible
class PimpleTVMonitor(xbmc.Monitor):
    

    # _history_added = False
    # _last_position = 0
    # _current_position = 0
    # _item = None

    def __init__(self):
        super(PimpleTVMonitor, self).__init__()



        # Addon().log_debug('Started {0}'.format(self))

    #     try:
    #         settings = TVZavr().service_get_settings()
    #     except (TVZavrError, simplemedia.WebClientError):
    #         self._progress_interval = 60
    #     else:
    #         self._progress_interval = float(settings['stat-progress-interval'])

    #     self._settings = self._get_settings()
    #     self._player = xbmc.Player()

    # def __del__(self):
    #     Addon().log_debug('Stoped {0}'.format(self))

    # def __str__(self):
    #     return '<TVZavrMonitor>'

    # def onNotification(self, sender, method, data):
    #     addon = Addon()
    #     addon.log_debug('{0}.onNotification({1}, {2}, {3})'.format(self, sender, method, py2_decode(data)))

    #     if data != 'nill':
    #         data = json.loads(data)

    #     if sender == 'xbmc':
    #         if method in ['Player.OnPlay', 'Player.OnPause', 'Player.OnSeek']:
    #             self._update_position()
    #             self.update_progress()
    #         elif method in ['Player.OnStop']:
    #             if self._item is not None:

    #                 if data.get('end', False):
    #                      self._current_position = -1
    #                 self.update_progress()

    #                 self._item = None

    #     elif sender == addon.id:
    #         if method == 'Other.OnPlay':
    #             if self._item is not None \
    #               and self._item['clip_id'] != data['clip_id']:
    #                 self._update_position()
    #                 self.update_progress()

    #             self._item = data
    #             self._history_added = False
    #             self._last_position = 0
    #             self._current_position = 0

    # def onSettingsChanged(self):
    #     super(TVZavrMonitor, self).onSettingsChanged()

    #     new_settings = self._get_settings()

    #     customer_regkey = Addon().get_setting('customer_regkey')
    #     if customer_regkey != 'fakeuser' \
    #       and new_settings != self._settings:

    #         differences = {}
    #         for key, val in iteritems(new_settings):
    #             if self._settings[key] != val:
    #                 differences[key] = val

    #         if differences:
    #             TVZavr().user_update(differences)

    #     self._settings.update(new_settings)

    # def _get_settings(self):
    #     addon = Addon()

    #     gender = addon.get_setting('customer_gender')
    #     store_progress = addon.get_setting('customer_store_progress')

    #     settings = {'name': addon.get_setting('customer_name'),
    #                 'birthday': addon.get_setting('customer_birthday'),
    #                 'gender': 'male' if gender == 0 else 'female',
    #                 'store_progress': 1 if store_progress else 0,
    #                 }
    #     return settings

    # def _update_position(self):
    #     if self._player.isPlaying():
    #         self._current_position = self._player.getTime()

    # def sync_progress(self):
    #     if self._item is not None:
    #         self._update_position()

    #         if (self._current_position - self._last_position) >= self._progress_interval:
    #             self.update_progress()

    # def update_progress(self):
    #     if self._item is not None:
    #         api = TVZavr()

    #         if not self._history_added \
    #           and self._current_position >= 30:
    #             try:
    #                 api.user_history_add(self._item['parent_id'])
    #             except (TVZavrError, simplemedia.WebClientError) as e:
    #                 addon.notify_error(e)
    #             else:
    #                 self._history_added = True

    #         if self._current_position != self._last_position:
    #             if self._settings['store_progress']:
    #                 try:
    #                     api.user_progress_add(self._item['clip_id'], self._current_position, self._item['ctx'])
    #                 except (TVZavrError, simplemedia.WebClientError) as e:
    #                     addon.notify_error(e)
    #                 else:
    #                     self._last_position = self._current_position
    #             elif self._history_added:
    #                 self._item = None

if __name__ == '__main__':

    sleep_sec = 10
    dev_check_sec = 0

    monitor = PimpleTVMonitor()
    while not monitor.abortRequested():

        print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'

        l = list(default.get_matches())

        # if dev_check_sec <= 0:
        #     try:
        #         TVZavr().check_device()
        #     except (TVZavrError, simplemedia.WebClientError) as e:
        #         pass
        #     else:
        #         dev_check_sec = 1800

        if monitor.waitForAbort(3600):
            break

        print '4444444444444444444444444444444444444444444444444444'
        #monitor.sync_progress()
        #dev_check_sec -= sleep_sec
