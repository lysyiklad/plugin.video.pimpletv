# -*- coding: utf-8 -*-

import os
import xbmc
import xbmcgui
import simpleplugin
import urllib2

from pimpletv import PimpleTV


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

        self._pimpletv = PimpleTV(self)
        self.settings_changed = False
    
    def dir(self, dir):
        return self._dir[dir]

    def http_get(self, url):
        try:
            req = urllib2.Request(url=url)
            req.add_header('User-Agent',
                           'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0'
                           ' (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; '
                           '.NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
            response = urllib2.urlopen(req)

            # URL из запроса
            self.log("The URL is: %s" % response.geturl())
            # Ответ сервера
            code = response.code
            self.log("This gets the code: %s" % response.code)
            if code != 200:
                raise Exception('Ошибка (%s) в %s ' % (code, url))
            # Заголовки ответа в виде словаря
            self.log("The Headers are: %s" % response.info())
            # Достаем дату сервера из заголовков ответа
            self.log("The Date is: %s" % response.info()['date'])
            # Получаем заголовок 'server' из заголовков
            self.log("The Server is: %s" % response.info()['server'])
            # Получаем весь html страницы
            html = response.read()
            #self.log("Get all data: %s" % html)
            # Узнаем длину страницу
            self.log("Get the length :%s" % len(html))
            response.close()
            return html
        except Exception as e:
            xbmcgui.Dialog().notification('Ошибка запроса', str(e),
                                        xbmcgui.NOTIFICATION_ERROR, 10000)
            err = '*** HTTP ERROR: %s - url: %s ' % (str(e), url)
            self.log(err)


    def update(self):
        return self._pimpletv.update()

    def matches(self):
        return self._pimpletv.matches()

    def get_href_match(self, id):
        return self._pimpletv.get_href_match(id)

    def get_match(self, id):
        return self._pimpletv.get_match(id)

    @property
    def version_kodi(self):
        return int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    def get_cache_thumb_name(self, thumb):
        thumb_cached = xbmc.getCacheThumbName(thumb)
        thumb_cached = thumb_cached.replace('tbn', 'png')
        return os.path.join(os.path.join(xbmc.translatePath("special://thumbnails"), thumb_cached[0], thumb_cached))   
