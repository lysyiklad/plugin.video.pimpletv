# -*- coding: utf-8 -*-

import datetime
import os
import pickle
import urllib2
from collections import OrderedDict
from urlparse import urlparse
from abc import abstractmethod

from dateutil.parser import *
from dateutil.tz import tzlocal, tzoffset

from . import simpleplugin
import xbmc
import xbmcgui
import xbmcplugin

LISTING_PICKLE = 'listing.pickle'


# def file_read(file):
#     with open(file, 'rt') as f:  # , encoding="utf-8" , errors='ignore'
#         try:
#             return f.read()
#         except Exception as e:
#             print(e)
#     return ''


class Plugin(simpleplugin.Plugin):

    def __init__(self):
        super(Plugin, self).__init__()
        self._dir = {'media': os.path.join(self.path, 'resources', 'media'),
                     'font': os.path.join(self.path, 'resources', 'data', 'font'),
                     'lib': os.path.join(self.path, 'resources', 'lib'),
                     'thumb': os.path.join(self.config_dir, 'thumb')}

        self._site = self.get_setting('url_site')
        self._listing_pickle = os.path.join(self.config_dir, LISTING_PICKLE)
        self.settings_changed = False
        self.stop_update = False

        self._date_scan = datetime.datetime.now()
        self._listing = OrderedDict()

        self.load()

    @abstractmethod
    def _parse_listing(self, html):
        """
        Парсим страницу для основного списка
        :param html: страница html
        :return: словарь словарей с данными для формирования списка корневой виртуальной папки
        """
        pass

    @abstractmethod
    def _parse_links(self, html):
        """
        Парсим страницу со ссылками
        :param html: страница html
        :return: список словарей для формирования списка папки со ссылками
        """
        pass

    @abstractmethod
    def _get_listing(self):
        pass

    @abstractmethod
    def _get_links(self, id):
        pass

    def create_listing_(self):
        return self.create_listing(self.get_listing(),
                                   content='movies',
                                   sort_methods=(
                                       xbmcplugin.SORT_METHOD_DATEADDED, xbmcplugin.SORT_METHOD_VIDEO_RATING),
                                   cache_to_disk=True)

    def get_listing(self):
        """
        Список для корневой виртуальной папки.
        :return:
        """
        self.update()
        return self._get_listing()

    def get_links(self, params):
        """
        Список для папки ссылок
        :param params: Передается в self.get_url(action='links', id=item['id'])
        :return:
        """
        id = int(params['id'])
        links = self.links(id)
        self.logd('links', links)

        if not links:
            return [{'label': 'Ссылок на трансляции нет, возможно появятся позже!',
                     'info': {'video': {'title': 'https://www.pimpletv.ru', 'plot': 'https://www.pimpletv.ru'}},
                     'art': {'icon': self.icon, 'thumb': self.icon, },
                     'url': self.get_url(action='play',
                                         href='https://www.ixbt.com/multimedia/video-methodology/camcorders-and-others/htc-one-x-avc-baseline@l3.2-1280x720-variable-fps-aac-2ch.mp4'),
                     'is_playable': True}]

        return self._get_links(id)

    def links(self, id):
        """
        Возвращает список ссылок кокретного элемента. При необходимости парсит по ссылке в элементе.
        :param id: id элемента
        :return:
        """
        links = self._listing[id]['href']

        self.logd('links - id - %s' % id, links)

        dt = self._get_minute_delta_now(id)

        if links or dt < -140 or dt > 60:
            return links

        html = self.http_get(self._listing[id]['url_links'])

        links.extend(self._parse_links(html))

        self.logd('self._listing[id][href]', self._listing[id]['href'])

        return links

    def update(self):
        """
        Обновление списков для виртуальных папок, рисунков, удаление мусора, сохранение в pickle
        :return:
        """
        self.logd('plugin.update - self.settings_changed', self.settings_changed)

        # Проверка необходимости обновления БД
        if not self.is_update():
            return

        self.log('START UPDATE')

        self._date_scan = datetime.datetime.now()
        # html = GET_FILE(os.path.join(self._plugin.path, 'PimpleTV.htm'))
        html = self.http_get(self._site)

        self._listing = self._parse_listing(html)

        for id_ in self._listing:
            self.links(id_)

        # 1. Удалить из self._listing не действительные матчи
        # 2. Удалить из thumb не действительные картинки и их кеши
        #
        artwork_real = []
        for id_, item in self._listing.items():
            if id_ in self._listing:
                if item['thumb']:
                    artwork_real.append(item['thumb'])
                if item['icon']:
                    artwork_real.append(item['icon'])
                if item['poster']:
                    artwork_real.append(item['poster'])
                if item['fanart']:
                    artwork_real.append(item['fanart'])
            else:
                self.remove_thumb(item['thumb'])
                self.remove_thumb(item['icon'])
                self.remove_thumb(item['poster'])
                self.remove_thumb(item['fanart'])

        dir_thumb = self.dir('thumb')
        files = os.listdir(dir_thumb)

        # подчищаем хвосты
        for file in files:
            f = os.path.join(dir_thumb, file)
            if f not in artwork_real:
                self.remove_thumb(f)

        self._listing = OrderedDict(
            sorted(self._listing.items(), key=lambda t: t[1]['date']))

        self.dump()
        # self.log(self._listing)
        self.log('STOP UPDATE')

        # self.stop_update = False
        # self.logd('plugin.update - self.stop_update', self.stop_update)

    def is_update(self):
        """
        Проверяет необходимость обновления списков
        :return: True - обновляем, False - нет
        """
        try:
            if self.settings_changed:
                self.settings_changed = False
                return True
            if not os.path.exists(self._listing_pickle):
                return True
            if not self._listing:
                return True
            dt = int((datetime.datetime.now() - self._date_scan).total_seconds() / 60)
            # Время сканирования меньше текущего времени на self.get_setting('delta_scan', True) - мин.
            if dt > self.get_setting('delta_scan'):
                return True  #
        except Exception as e:
            self.logd('is_update', e)
            return True
        return False

    def play(self, params):
        """
        Воспроизводит ссылку
        :param params: Передается в self.get_url(action='play', href=href, id=item['id']) и
                                    self.get_url(action='play', href=link['href'], id=id
        :return:
        """
        path = ''
        msg = ''
        self.logd('play', params)
        if 'href' not in params or not params['href']:
            links = self.links(int(params['id']))
            self.logd('play', links)
            for h in links:
                if h['title'] == self.get_setting('play_engine').decode('utf-8'):
                    params['href'] = h['href']
                    break
            if 'href' not in params or not params['href']:
                msg = 'НЕТ ССЫЛОК НА ТРАНСЛЯЦИЮ МАТЧА!'
                self.logd('play', msg)
                self.notification(msg)
                return None

        href = params['href']
        url = urlparse(href)
        if url.scheme == 'acestream':
            path = self.get_path_acestream(href)
        elif url.scheme == 'sop':
            path = self.get_path_sopcast(href)
        else:
            path = url.geturl()

        if not path:
            msg = 'ПУСТОЙ ПУТЬ НА ТРАНСЛЯЦИЮ МАТЧА!'
            self.notification(msg)
            self.logd('play', msg)
            return None

        self.logd('play', 'PATH PLAY: %s' % path)

        return self.resolve_url(path, succeeded=True)

    @property
    def date_scan(self):
        return self._date_scan

    def load(self):
        if os.path.exists(self._listing_pickle):
            with open(self._listing_pickle, 'rb') as f:
                self._date_scan, self._listing = pickle.load(f)

    def dump(self):
        with open(self._listing_pickle, 'wb') as f:
            pickle.dump([self._date_scan, self._listing], f)

    @staticmethod
    def format_timedelta(dt, pref):
        h = int(dt.seconds / 3600)
        return u'{} {} {} {:02} мин.'.format(pref, u'%s дн.' % dt.days if dt.days else u'',
                                             u'%s ч.' % h if h else u'', int(dt.seconds % 3600 / 60))

    @staticmethod
    def create_id(key):
        """
        Создаем id для записи
        :param key: str оригинальная для записи строка
        :return: возвращает id
        """
        return hash(key)

    def _get_minute_delta_now(self, id):
        """
        Время в минутах до даты в элементе списка. Если матча с таким id нет, возвращаем None
        """
        if id not in self._listing:
            return None

        dt = int((self._listing[id]['date'] - datetime.datetime.now().replace(tzinfo=tzlocal())).total_seconds() / 60)
        return dt

    def dir(self, dir_):
        return self._dir[dir_]

    def http_get(self, url):
        try:
            req = urllib2.Request(url=url)
            req.add_header('User-Agent',
                           'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0'
                           ' (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; '
                           '.NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')

            response = urllib2.urlopen(req)
            self.log(self._get_response_info(response))
            html = response.read()
            response.close()
            return html
        except Exception as e:
            xbmcgui.Dialog().notification('Ошибка запроса', str(e),
                                          xbmcgui.NOTIFICATION_ERROR, 10000)
            err = '*** HTTP ERROR: %s - url: %s ' % (str(e), url)
            self.log(err)

    @staticmethod
    def _get_response_info(response):
        response_info = ['Response info', 'Status code: {0}'.format(response.code)]
        if response.code != 200:
            raise Exception('Error (%s) в %s ' %
                            (response.code, response.geturl()))
        response_info.append('URL: {0}'.format(response.geturl()))
        response_info.append('Info: {0}'.format(response.info()))
        return '\n'.join(response_info)

    def item(self, id_):
        return self._listing[id_]

    def remove_thumb(self, thumb):
        """
        Удаляет рисунок и кеш
        :param thumb: 
        :return: 
        """
        if os.path.exists(thumb):
            self.logd('remove_thumb', thumb)
            os.remove(thumb)
        self.remove_cache_thumb(thumb)

    def remove_cache_thumb(self, thumb):
        """
        Удаляет кеш рисунка
        :param thumb: 
        :return: 
        """
        # определяем кеши картинок и удаляем кеши картинок из системы
        if self.cache_thumb_name:
            thumb_cache = self.cache_thumb_name(thumb)
            self.logd('remove_cache_thumb', thumb_cache)
            if os.path.exists(thumb_cache):
                os.remove(thumb_cache)

    def remove_all_thumb(self):
        """
        
        :return: 
        """
        pics = os.listdir(self.dir('thumb'))
        for pic in pics:
            pic = os.path.join(self.dir('thumb'), pic)
            self.remove_thumb(pic)
        if os.path.exists(self._listing_pickle):
            os.remove(self._listing_pickle)
            self._plugin.logd('remove listing.pickle', self._listing_pickle)

    @property
    def version_kodi(self):
        return int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    @staticmethod
    def cache_thumb_name(thumb):
        """
        Находит кеш рисунка
        :param thumb:
        :return:
        """
        thumb_cached = xbmc.getCacheThumbName(thumb)
        thumb_cached = thumb_cached.replace('tbn', 'png')
        return os.path.join(os.path.join(xbmc.translatePath("special://thumbnails"), thumb_cached[0], thumb_cached))

    def notification(self, msg):
        """
        Выводит уведомление о пустой ссылке
        :param msg:
        :return:
        """
        title = self.name.encode('utf-8')
        time = 500
        icon = self.icon.encode('utf-8')
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (title, msg, time, icon))

    @staticmethod
    def get_path_sopcast(href):
        url = urlparse(href)
        path = "plugin://program.plexus/?mode=2&url=" + url.geturl() + "&name=Sopcast"
        return path

    def get_path_acestream(self, href):
        """
        В зависимости от настроек формирует путь для воспроизведения acestream
        :param href: acestream://132121321321321321321321
        :return:
        """
        path = ''
        item = 0
        url = urlparse(href)
        if self.get_setting('is_default_ace'):
            item = self.get_setting('default_ace')
        else:
            dialog = xbmcgui.Dialog()
            list = [
                'ACESTREAM %s [%s]' % ('hls' if self.get_setting('is_hls1') else '', self.get_setting('ipace1')),
                'ACESTREAM %s [%s]' % ('hls' if self.get_setting('is_hls2') else '', self.get_setting('ipace2')),
                'HTTPAceProxy [%s]' % self.get_setting('ipproxy'),
                'Add-on TAM [127.0.0.1]']

            if self.version_kodi < 17:
                item = dialog.select('Выбор способа воспроизведения Ace Straem', list=list)
            else:
                item = dialog.contextmenu(list)

            if item == -1:
                return None

        cid = url.netloc

        if item == 0:
            path = 'http://%s:6878/ace/%s?id=%s' % (
                self.get_setting('ipace1'), 'manifest.m3u8' if self.get_setting(
                    'is_hls1') else 'getstream', cid)
        elif item == 1:
            path = 'http://%s:6878/ace/%s?id=%s' % (
                self.get_setting('ipace2'), 'manifest.m3u8' if self.get_setting(
                    'is_hls2') else 'getstream', cid)
        elif item == 2:
            path = "http://%s:8000/pid/%s/stream.mp4" % (
                self.get_setting('ipproxy'), cid)
        elif item == 3:
            path = "plugin://plugin.video.tam/?mode=play&url=%s&engine=ace_proxy" % href

        return path

    def convert_local_datetime(self, dt):
        """
        Переводит dt в локальное осведомленное (aware) время
        :param dt: datetime относительное (naive) время
        :return: datetime локальное осведомленное (aware) время
        """
        tz = tzoffset(None, int(self.get_setting('time_zone_site')) * 3600)
        dt = dt.replace(tzinfo=tz)
        return dt.astimezone(tzlocal())

    def full_reset(self):
        """
        Полный сброс списков
        :return:
        """
        self.settings_changed = True
        if self.get_setting('full_reset'):
            self.set_setting('full_reset', False)
            self.log('START FULL RESET')
            self.remove_all_thumb()

        self.update()
        self.settings_changed = False
