# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from future import standard_library

standard_library.install_aliases()
import requests
# import pickle
# import re
from . import makeart, simpleplugin
import xbmcgui
import xbmc
# import xbmcplugin
from dateutil.tz import tzutc, tzlocal, tzoffset
from dateutil.parser import *
# import dateutil
import bs4
from urllib.parse import urlparse
from collections import OrderedDict
import os
import json
import datetime
from builtins import range
from builtins import str

# URL_NOT_LINKS = 'https://www.ixbt.com/multimedia/video-methodology/bitrates/avc-1080-25p/1080-25p-10mbps.mp4'
URL_NOT_LINKS = 'http://tv-na-stene.ru/files/HD%20Red.mkv'

HEADERS_HTTP = {'User-Agent':
                    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0'
                    ' (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; '
                    '.NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)'}


def file_read(file):
    with open(file, 'rt') as f:  # , encoding="utf-8" , errors='ignore'
        try:
            return f.read()
        except Exception as e:
            print(e)
    return ''


class PluginSport(simpleplugin.Plugin):

    def __init__(self):
        super(PluginSport, self).__init__()
        global _
        self._dir = {'media': os.path.join(self.path, 'resources', 'media'),
                     'data': os.path.join(self.path, 'resources', 'data'),
                     'font': os.path.join(self.path, 'resources', 'data', 'font'),
                     'lib': os.path.join(self.path, 'resources', 'lib'),
                     'thumb': os.path.join(self.profile_dir, 'thumb')}

        if not os.path.exists(self.dir('thumb')):
            os.mkdir(self.dir('thumb'))

        self._site = self.get_setting('url_site')
        self.settings_changed = False
        self.stop_update = False

        self._date_scan = None  # Время сканирования в utc
        self._listing = OrderedDict()

        self._language = xbmc.getInfoLabel('System.Language')  # Russian English

        if self._language != 'Russian':
            self._site = os.path.join(self.get_setting('url_site'), 'en')
        else:
            self._site = self.get_setting('url_site')

        self._progress = xbmcgui.DialogProgressBG()

        self._leagues = OrderedDict()
        self._leagues_artwork = OrderedDict()

        self._icons_league_pcl = os.path.join(self.profile_dir, 'iconleague.pcl')

        self.load()


    @staticmethod
    def create_id(key):
        """
        Создаем id для записи
        :param key: str оригинальная для записи строка
        :return: возвращает id
        """
        return hash(key)

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

    @staticmethod
    def get_path_sopcast(href):
        url = urlparse(href)
        path = "plugin://program.plexus/?mode=2&url=" + url.geturl() + "&name=Sopcast"
        return path

    @staticmethod
    def format_str_column_width(txt, column_width):
        txt = txt.strip()
        result = u'{1:<{0:}}'.format(
            column_width, txt[:column_width] if len(txt) > column_width else txt)
        return result

    @property
    def date_scan(self):
        return self._date_scan

    @property
    def version_kodi(self):
        return int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    def dir(self, dir_):
        return self._dir[dir_]

    def get(self, id_, key):
        item = self._listing.get(id_, None)
        if item is None:
            self.update()
            item = self._listing.get(id_, None)
            if item is None:
                return None

        return item.get(key, None)

    def load(self):
        try:
            with self.get_storage() as storage:
                self._listing = storage['listing']
                self._date_scan = storage['date_scan']
                self._leagues = storage['leagues']
                self._leagues_artwork = storage['leagues_artwork']
        except Exception as e:
            self.logd('ERROR load data', e)

    def dump(self):
        try:
            with self.get_storage() as storage:
                storage['listing'] = self._listing
                storage['date_scan'] = self._date_scan
                storage['leagues'] = self._leagues
                storage['leagues_artwork'] = self._leagues_artwork
        except Exception as e:
            self.logd('ERROR dump data', e)

    def _selected_leagues(self, leagues, title):

        selected_old = self._get_selected_leagues(leagues)
        if self.version_kodi < 17:
            selected = xbmcgui.Dialog().multiselect(title, leagues.keys())
        else:
            selected = xbmcgui.Dialog().multiselect(title, leagues.keys(), preselect=selected_old, useDetails=False)
        if selected is not None and selected != selected_old:
            self._set_selected_leagues(selected, leagues)
            self.logd('selected_leagues', selected)
            self.dump()
            #  with self.get_storage() as storage:
            #      storage['leagues'] = self._leagues

            self.on_settings_changed()

    def _get_selected_leagues(self, leagues):
        return [index for index, item in enumerate(leagues.items()) if item[1]]

    def _set_selected_leagues(self, selected, leagues):
        for index, item in enumerate(leagues.items()):
            leagues[item[0]] = False
            if index in selected:
                leagues[item[0]] = True

    def _add_league(self, league):
        if self._leagues.get(league, None) is None:
            self._leagues[league] = True
            self._leagues_artwork[league] = True
            self.dump()
        #  with self.get_storage() as storage:
        #      storage['leagues'] = self._leagues

    def selected_leagues(self):
        self._selected_leagues(self._leagues, _('Choosing a Sports Tournament'))

    def _is_league(self, league, leagues):
        if leagues.get(league, None) is not None:
            if not leagues[league]:
                return False
        else:
            self._add_league(league)
        return True

    def selected_leagues_artwork(self):
        self._selected_leagues(self._leagues_artwork, _('Select leagues to create ArtWork...'))

    def get_http(self, url):
        try:
            self.log('HTTP GET - URL {}'.format(url))
            r = requests.get(url, headers=HEADERS_HTTP, timeout=10)
            self.log(r.status_code)
            for it in r.headers.items():
                self.log('{}: {}'.format(it[0], it[1]))
            return r
        except requests.exceptions.ReadTimeout:
            err = 'HTTP ERROR: Read timeout occured'
        except requests.exceptions.ConnectTimeout:
            err = 'HTTP ERROR: Connection timeout occured!'
        except requests.exceptions.ConnectionError:
            err = 'HTTP ERROR: Seems like dns lookup failed..'
        except requests.exceptions.HTTPError as err:
            err = 'HTTP ERROR: HTTP Error occured'
            err += 'Response is: {content}'.format(content=err.response.content)

        self.log(err)
        raise Exception(err)

    #       return ''

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
        id_ = int(params.id)
        links = self.links(id_, isdump=True)
        self.logd('links', links)

        return self._get_links(id_, links)

    def links(self, id_, isdump=False):
        """
        Возвращает список ссылок кокретного элемента. При необходимости парсит по ссылке в элементе.
        :param id_: id элемента
        :return:
        """
        links = self.get(id_, 'href')
        tnd = self._time_now_date(id_)
        tsn = self._time_scan_now()
        dt = self.get_setting('delta_links')

        self.logd('links links', links)
        self.logd('links self.date_scan', self.date_scan)

        links = self.get(id_, 'href')

        self.logd('links links', links)

        # status = self.get(id_, 'status')
        #
        # if links and status == 'OFFLINE':
        #     self.logd('links', 'id - %s  status - %s ' % (id_, status))
        #     return links

        if not links or not self.date_scan or tsn > self.get_setting('delta_scan') or tsn > dt:  # and tnd < dt):
            self.logd('links - id - %s : time now date - %s time scan now - %s' %
                      (id_, tnd, tsn), links)
            try:
                html = self.get_http(self.get(id_, 'url_links')).content
                # file_html = os.path.join(self.path, 'links.html')
                # if not os.path.exists(file_html):
                #     with open(file_html, 'wb') as f:
                #         f.write(html)
            except Exception as e:
                xbmcgui.Dialog().notification(self.name, str(e), self.icon, 2000)
                self.logd('ERROR LINKS', str(e))
            finally:
                if not html:
                    self.logd('links', 'not html')
                    return links
            del links[:]
            links.extend(self._parse_links(id_, html))
            # if links and status == 'OFFLINE':
            #     self.dump()

        self.logd('self.get(%s, href)' % id_, self.get(id_, 'href'))

        return links

    def update(self):
        """
        Обновление списков для виртуальных папок, рисунков, удаление мусора, сохранение в pickle
        :return:
        """


        self.load()

        self.logd('plugin.update - self.settings_changed', self.settings_changed)

        for it in self._leagues.items():
            self.log('update self._leagues - {}: {}'.format(it[0], it[1]))

        if not self.is_update():
            return

        # progress = xbmcgui.DialogProgressBG()

        self._progress.create(self.name, _('UPDATE DATA ...'))

        try:

            self.log('START UPDATE')

            self._progress.update(1, message=_('Loading site data ...'))

            # import web_pdb
            # web_pdb.set_trace()

            html = self.get_http(self._site).content

            # self.log(html)

            # file_html = os.path.join(self.path, 'listing.html')
            # if not os.path.exists(file_html):
            #     with open(file_html, 'wb') as f:
            #         f.write(html)

            # html = file_read(file_html)

            self.log('***** 1')
            self._listing = self._parse_listing(html, progress=self._progress)
            self.log('***** 2')

            if not self._listing:
                try:
                    if self._progress:
                        self._progress.close()
                except:
                    pass
                self.logd('update', 'self._listing None')
                return

            for item in list(self._listing.values()):
                if 'thumb' not in item:
                    item['thumb'] = ''
                if 'icon' not in item:
                    item['icon'] = ''
                if 'poster' not in item:
                    item['poster'] = ''
                if 'fanart' not in item:
                    item['fanart'] = ''
                if 'url_links' not in item:
                    item['url_links'] = ''
                if 'href' not in item:
                    item['href'] = []

            self.log('***** 3')

            artwork = []
            for item in list(self._listing.values()):
                if item['thumb']:
                    artwork.append(item['thumb'])
                if item['icon']:
                    artwork.append(item['icon'])
                if item['poster']:
                    artwork.append(item['poster'])
                if item['fanart']:
                    artwork.append(item['fanart'])

            for file in os.listdir(self.dir('thumb')):
                f = os.path.join(self.dir('thumb'), file)
                if f not in artwork:
                    self.remove_thumb(f)

            self.log('***** 4')

            self._listing = OrderedDict(sorted(list(self._listing.items()), key=lambda t: t[1]['date']))
            self.log('***** 5')
            self._date_scan = self.time_now_utc()
            self.dump()
            self.log(
                'STOP UPDATE [date scan = {} - _time_scan_now() = {}]'.format(self.date_scan, self._time_scan_now()))
            self._progress.update(100, self.name, _('End update...'))


        except Exception as e:
            xbmcgui.Dialog().notification(self.name, str(e), xbmcgui.NOTIFICATION_ERROR, 10000)
            self.logd('ERROR UPDATE', str(e))
        finally:
            xbmc.sleep(500)
            self.log('***** 6')
            try:
                if self._progress:
                    self._progress.close()
            except:
                pass

    def is_update(self):
        """
        Проверяет необходимость обновления списков
        :return: True - обновляем, False - нет
        """
        try:
            if not self.date_scan:
                self.logd('is_update', 'True - not self.date_scan')
                return True
            if self.settings_changed:
                self.logd('is_update', 'True - self.settings_changed')
                return True
            if not os.path.exists(os.path.join(self.profile_dir, 'storage.pcl')):
                self.logd('is_update', 'True - not os.path.exists(storage.pcl)')
                return True
            if not self._listing:
                self.logd('is_update', 'True - not self._listing')
                return True
            if self._time_scan_now() > self.get_setting('delta_scan'):
                self.logd(
                    'is_update',
                    'True - self._time_scan_now() {} > self.get_setting(delta_scan) {}'.format(self._time_scan_now(),
                                                                                               self.get_setting(
                                                                                                   'delta_scan')))
                return True  #
        except Exception as e:
            self.logd('ERROR -> is_update', e)
            return True
        self.logd('is_update', 'False')
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

        href = params.href
        url = urlparse(href)
        if url.scheme == 'acestream':
            progress = xbmcgui.DialogProgressBG()
            path = self.get_path_acestream(href)
            if not path:
                return None
            try:

                if urlparse(path).port == 6878:

                    progress.create('Ace Stream Engine', self.name)

                    self.log('start acestream play - host - {} - port {}'.format(urlparse(path).hostname,
                                                                                 urlparse(path).port))

                    as_url = 'http://' + urlparse(path).hostname + ':' + '6878' + '/ace/getstream?id=' + \
                             urlparse(href).netloc + '&format=json'  # &_idx=" + str(ep)

                    json_response = requests.get(as_url).json()["response"]
                    self.log(json_response)
                    stat_url = json_response["stat_url"]
                    self.logd('stat_url', stat_url)
                    stop_url = json_response["command_url"] + '?method=stop'
                    self.logd('stop_url', stop_url)
                    purl = json_response["playback_url"]
                    self.logd('purl', purl)

                    for i in range(30):
                        xbmc.sleep(1000)
                        j = requests.get(stat_url).json()["response"]
                        if j == {}:
                            progress.update(i * 3, message=_('wait...'))
                        else:

                            status = j['status']
                            if status == 'dl':
                                progress.update(i * 3, message=_('playback...'))
                                xbmc.sleep(1000)
                                break
                            progress.update(i * 3, message=_('prebuffering...'))
                            self.logd('get stat acestream - ', j)
                            msg = 'seeds - %s speed - %s download - %s' % (
                                str(j['peers']), str(j['speed_down']), str(int(j['downloaded'] / 1024)))
                            progress.update(i * 3, msg)

                    if i == 29:
                        xbmcgui.Dialog().notification(
                            self.name, _('Torrent not available or invalid!'), self.icon, 500)
                        requests.get(stop_url)

                    progress.close()
                    xbmc.sleep(1000)
                    path = purl
            except Exception as e:
                xbmcgui.Dialog().notification(
                    self.name, _('Torrent not available or invalid!'), self.icon, 500)
                self.logd('error acestream (%s)' %
                          str(e), 'Torrent not available or invalid!')
                if progress:
                    progress.close()
                return None

        elif url.scheme == 'sop':
            path = self.get_path_sopcast(href)
        elif url.netloc == 'stream.livesport.ws':
            path = self._resolve_direct_link(url.geturl())
        else:
            path = url.geturl()

        if not path:
            msg = _('Resource Unavailable or Invalid!')
            xbmcgui.Dialog().notification(self.name, msg, self.icon, 500)
            self.logd('play', msg)
            return None

        self.logd('play', 'PATH PLAY: %s' % path)

        params = {'sender': self.id,
                  'message': 'resolve_url',
                  'data': {'command': 'Play.Live',
                           'id': params.id,
                           },
                  }

        command = json.dumps({'jsonrpc': '2.0',
                              'method': 'JSONRPC.NotifyAll',
                              'params': params,
                              'id': 1,
                              })

        result = xbmc.executeJSONRPC(command)

        self.logd('play', 'result xbmc.executeJSONRPC {}'.format(result))

        # return self.resolve_url(path, succeeded=True)
        return path

    @staticmethod
    def time_now_utc():
        """
        Возвращает текущее осведомленное(aware) время в UTC
        :return:
        """
        return datetime.datetime.now(tz=tzutc())

    @staticmethod
    def time_to_local(dt):
        """
        Переводит осведомленное (aware) время в локальное осведомленное
        :param dt: осведомленное (aware) время
        :return: локальное осведомленное (aware)
        """
        return dt.astimezone(tzlocal())

    def _time_naive_site_to_local_aware(self, dt):
        """
        Переводит наивное время из сайта в осведомленное (aware) локальное время
        :param dt: datetime относительное (naive) время из результатов парсинга сайта
        :return: datetime локальное осведомленное (aware) время
        """
        tz = tzoffset(None, int(self.get_setting('time_zone_site')) * 3600)
        dt = dt.replace(tzinfo=tz)
        return dt.astimezone(tzlocal())

    def _time_naive_site_to_utc_aware(self, dt):
        """
        Переводит наивное время из сайта в осведомленное (aware) время UTC
        :param dt: datetime относительное (naive) время из результатов парсинга сайта
        :return: datetime UTC осведомленное (aware) время
        """
        tz = tzoffset(None, int(self.get_setting('time_zone_site')) * 3600)
        dt = dt.replace(tzinfo=tz)
        return dt.astimezone(tzutc())

    def _time_now_date(self, id):
        """
        Время в минутах от текущего времени до даты в элементе списка. Если матча с таким id нет, возвращаем None
        """
        if id not in self._listing:
            return None

        return int((self.get(id, 'date') - self.time_now_utc()).total_seconds() / 60)

    def _time_scan_now(self):
        """
        Время в минутах от последнего сканирования до текущего времени
        """
        if self.date_scan is None:
            return None
        return int((self.time_now_utc() - self.date_scan).total_seconds() / 60)

    def _time_scan_date(self, id):
        """
        Время в минутах от последнего сканирования до даты в элементе списка. Если матча с таким id нет, возвращаем None
        """
        if self.date_scan is None:
            return None
        return int((self.get(id, 'date') - self.date_scan).total_seconds() / 60)

    def _format_timedelta(self, dt, pref):
        if self._language == 'Russian':
            h = int(dt.seconds / 3600)
            return '{} {} {} {:02} мин.'.format(pref, '%s дн.' % dt.days if dt.days else '',
                                                '%s ч.' % h if h else u'', int(dt.seconds % 3600 / 60))
        else:
            return '{} {}'.format(pref, str(dt).split('.')[0])

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
        if self.cache_thumb_name:
            thumb_cache = self.cache_thumb_name(thumb)
            self.logd('remove_cache_thumb', thumb_cache)
            if os.path.exists(thumb_cache):
                os.remove(thumb_cache)

    def clear(self):
        """

        :return: 
        """
        pics = os.listdir(self.dir('thumb'))
        for pic in pics:
            pic = os.path.join(self.dir('thumb'), pic)
            self.remove_thumb(pic)
        fs = os.listdir(self.profile_dir)
        self._date_scan = None
        self._listing.clear()
        self._leagues.clear()
        self._leagues_artwork.clear()
        self.dump()

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
                'ACESTREAM %s [%s]' % ('hls' if self.get_setting(
                    'is_hls1') else '', self.get_setting('ipace1')),
                'ACESTREAM %s [%s]' % ('hls' if self.get_setting(
                    'is_hls2') else '', self.get_setting('ipace2')),
                'HTTPAceProxy [%s]' % self.get_setting('ipproxy'),
                'Add-on TAM [127.0.0.1]',
                'Add-on Plexus']

            if self.version_kodi < 17:
                item = dialog.select(
                    'Select a playback method Ace Straem', list=list)
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
        elif item == 4:
            path = "plugin://program.plexus/?mode=1&url=" + \
                   url.geturl() + "&name=My+acestream+channel"

        return path

    def on_settings_changed(self):
        self.settings_changed = True
        xbmcgui.Dialog().notification(self.name, _('Changing settings ...'), self.icon, 1000)
        self.update()
        self.settings_changed = False
        xbmc.executebuiltin('Container.Refresh()')

    def reset(self):
        """
        Обновление с удалением файлов данных
        :return:
        """
        xbmcgui.Dialog().notification(self.name, _('Plugin data reset...'), self.icon, 500)
        self.log('START RESET DATA')
        self.clear()
        self.update()
        self.log('END RESET DATA')
        # xbmc.executebuiltin('Dialog.Close(all,true)')
        xbmc.executebuiltin('Container.Refresh()')

    def geturl_isfolder_isplay(self, id, href):
        """

        :param id:
        :param href:
        :return:
        """
        is_folder = True
        is_playable = False
        get_url = self.get_url(action='links', id=id)

        if self.get_setting('is_play'):
            is_folder = False
            is_playable = True
            get_url = self.get_url(action='play', href=href, id=id)

        return is_folder, is_playable, get_url

    def is_create_artwork(self):
        if self.get_setting('is_thumb') or self.get_setting('is_fanart') or self.get_setting('is_poster'):
            return True
        return False

MONTHS = {u"января": u"January",
          u"февраля": u"February",
          u"марта": u"March",
          u"апреля": u"April",
          u"мая": u"May",
          u"июня": u"June",
          u"июля": u"July",
          u"августа": u"August",
          u"сентября": u"September",
          u"октября": u"October",
          u"ноября": u"November",
          u"декабря": u"December"}


class PimpleTV(PluginSport):

    def create_listing_(self):
        return self.create_listing(self.get_listing(),
                                   content='movies',
                                   cache_to_disk=False)

    def _parse_listing(self, html, progress=None):
        """
        Парсим страницу для основного списка
        :param html:
        :return:listing = {
                        id : {
                            id: int,
                            label: '',
                            league: '',
                            date: datetime,     должно быть осведомленное время в UTC
                            thumb: '',
                            icon: '',
                            poster: '',
                            fanart: '',
                            url_links: '',
                            href: [
                                    {
                                    'id': int,
                                    'title': '',
                                    'kbps': '',
                                    'resol': '',
                                    'href': '',
                                }
                            ]
                        }
                    }
        """

        listing = {}

        soup = bs4.BeautifulSoup(html, 'html.parser')

        streams_day_soup = soup.findAll('div', {'class': 'streams-day'})

        i = 1
        try:
            total = len(soup.findAll('div', {'class': 'broadcast preview'}))
        except:
            total = 30

        self.logd('_parse_listing', 'count games - {}'.format(total))

        still = total
        fill = 0

        for day_soup in streams_day_soup:
            day = '%s %s %s %s' % (
                day_soup.text.split()[0], MONTHS[day_soup.text.split()[1]], datetime.datetime.now().year, '%s')

            self.logd('update', day)

            for row in list(day_soup.next_siblings):
                try:
                    if row['class'] == ['row']:
                        cols = row.findAll('div', {'class': 'broadcast preview'})
                        for col in cols:

                            str_time = col.find('div', 'bottom-line').span.text
                            dt = parse(day % str_time)

                            date_utc = self._time_naive_site_to_utc_aware(dt)

                            if self.get_setting('is_noold_item') and int(
                                    (date_utc - self.time_now_utc()).total_seconds() / 60) < -180:
                                continue

                            match = col.find('div', 'live-teams').text

                            id_ = self.create_id(str(date_utc) + match)

                            league = col.find('div', 'broadcast-category').text

                            home = match.split(u'\u2014')[0].strip()
                            away = match.split(u'\u2014')[1].strip()

                            poster = ''
                            thumb = ''
                            fanart = self.fanart
                            icon = self.icon


                            if self.is_create_artwork():
                                try:

                                    file_art = os.path.join(self.dir('thumb'), '{}_{}_{}.png'.format(id_, '{}', '{}'))

                                    art_value = {
                                        "league": league,
                                        'logo_home': self._site + col.find('div', 'home-logo').img['src'],
                                        'logo_guest': self._site + col.find('div', 'away-logo').img['src'],
                                        "home": home,
                                        'guest': away,
                                        'weekday': makeart.weekday(self.time_to_local(date_utc), self._language),
                                        'month': makeart.month(self.time_to_local(date_utc), self._language),
                                        'time': makeart.time(self.time_to_local(date_utc)),
                                    }

                                    art = makeart.ArtWork(self.dir('font'),
                                                          os.path.join(self.dir('data'), 'layout.json'),
                                                          art_value,
                                                          self.log)

                                    theme_artwork = self.get_setting('theme_artwork')

                                    file_art = file_art.format(theme_artwork, '{}')

                                    if theme_artwork == 0:  # Light
                                        art.set_color_font([0, 0, 0])
                                        art.set_background(os.path.join(self.dir('media'), 'light.png'))
                                    elif theme_artwork == 1:  # Dark
                                        art.set_background(os.path.join(self.dir('media'), 'dark.png'))
                                    elif theme_artwork == 2:  # Blue
                                        art.set_background(os.path.join(self.dir('media'), 'blue.png'))
                                    elif theme_artwork == 3:  # Transparent
                                        art.set_background(os.path.join(self.dir('media'), 'transparent.png'))
                                    else:
                                        self.logd('_parse_listing', 'error set artwork theme')

                                    if self.get_setting('is_thumb'):
                                        thumb = art.make_file(file_art.format('thumb'), 'thumb')
                                        self.logd('_parse_listing', thumb)
                                    if self.get_setting('is_fanart'):
                                        art.set_background_type('fanart', self.fanart)
                                        fanart = art.make_file(file_art.format('fanart'), 'fanart')
                                        self.logd('_parse_listing', fanart)
                                    if self.get_setting('is_poster'):
                                        poster = art.make_file(file_art.format('poster'), 'poster')
                                        self.logd('_parse_listing', poster)

                                except Exception as e:
                                    self.logd('ArtWork', 'ERROR [{}]'.format(str(e)))

                            if thumb:
                                icon = thumb
                            else:
                                thumb = icon


                            self.logd(
                                'parse_listing', 'ADD MATCH - %s - %s' % (self.time_to_local(date_utc), match))

                            # i += 2
                            # if progress:
                            #     progress.update(i, message=match)

                            if progress:
                                still = still - 1
                                fill = 100 - int(100 * float(still) / total)
                                progress.update(fill, message=match)

                            listing[id_] = {}
                            item = listing[id_]
                            item['id'] = id_
                            item['label'] = match
                            item['league'] = league
                            item['date'] = date_utc
                            item['thumb'] = thumb
                            item['icon'] = ''
                            item['poster'] = poster
                            item['fanart'] = fanart
                            item['url_links'] = self._site + \
                                col.find('div', 'live-teams').a['href']
                            if 'href' not in item:
                                item['href'] = []

                    else:
                        break
                except Exception as e:
                    self.logd('parse_listing', e)



        return listing

    def _parse_links(self, id_, html):
        """
        Парсим страницу для списка ссылок
        :param html:
        :return:
        """

        links = []

        soup = bs4.BeautifulSoup(html, 'html.parser')

        broadcast_table = soup.find('table', {'class': 'broadcast-table'})

        if broadcast_table is None:
            return []

        tbody = broadcast_table.find('tbody')

        for tr in tbody.find_all('tr'):
            td = tr.find_all('td')
            links.append({
                'id': id,
                'title': td[0].find('a').text,
                'kbps': td[2].text,
                'resol': td[3].text,
                'href': td[5].find('a')['href'],
            })

        return links

    def _get_links(self, id, links):
        """
        Возвращаем список ссылок для папки конкретного элемента
        :param id:
        :return:
        """
        l = []

        for link in links:

            urlprs = urlparse(link['href'])

            plot = ''

            if urlprs.scheme == 'acestream':
                icon = os.path.join(self.dir('media'), 'ace.png')
            elif urlprs.scheme == 'sop':
                icon = os.path.join(self.dir('media'), 'sop.png')
                plot = u'\n\nДля просмотра SopCast необходим плагин Plexus'
            else:
                icon = os.path.join(self.dir('media'), 'http.png')

            l.append({'label': '%s - %s - %s' % (link['title'], link['kbps'], link['resol']),
                      'info': {'video': {'title': self.get(id, 'label'), 'plot': self.get(id, 'label') + plot}},
                      'thumb': icon,
                      'icon': icon,
                      'fanart': '',
                      'art': {'icon': icon, 'thumb': icon, },
                      'url': self.get_url(action='play', href=link['href'], id=id),
                      'is_playable': True})


        if not l:
            return [{'label': 'Ссылок на трансляции нет, возможно появятся позже!',
                     'info': {'video': {'title': self._site, 'plot': self._site}},
                     'art': {'icon': self.icon, 'thumb': self.icon, },
                     'url': self.get_url(action='play', href=URL_NOT_LINKS),
                     'is_playable': True}]

        return l

    def _get_listing(self):
        """
        Возвращаем список для корневой виртуальной папки
        :return:
        """

        listing = []

        now_utc = self.time_now_utc()

        self.logd('pimpletv._get_listing()', '%s' %  self.time_to_local(now_utc))

        try:
            for item in self._listing.values():
                date_ = item['date']
                if date_ > now_utc:
                    dt = date_ - now_utc
                    plot = self._format_timedelta(dt, u'Через')
                    status = 'FFFFFFFF'
                else:
                    dt = now_utc - date_
                    if int(dt.total_seconds() / 60) < 110:
                        plot = u'Прямой эфир %s мин.' % int(
                            dt.total_seconds() / 60)
                        status = 'FFFF0000'
                    else:
                        plot = self._format_timedelta(dt, u'Закончен')
                        status = 'FF999999'

                title = u'[COLOR %s]%s[/COLOR]\n[B]%s[/B]\n[UPPERCASE]%s[/UPPERCASE]' % (
                    status, self.time_to_local(date_).strftime('%d.%m %H:%M'), item['label'], item['league'])

                label = u'[COLOR %s]%s[/COLOR] - [B]%s[/B]' % (
                    status, self.time_to_local(date_).strftime('%H:%M'), item['label'])

                plot = title + '\n' + plot + '\n\n' + self._site

                href = ''

                if self.get_setting('is_play'):
                    for h in item['href']:
                        if h['title'] == self.get_setting('play_engine').decode('utf-8'):
                            href = h['href']
                            break

                is_folder, is_playable, get_url = self.geturl_isfolder_isplay(
                    item['id'], href)

                listing.append({
                    'label': label,
                    'art': {
                        'thumb': item['thumb'],
                        'poster': item['poster'],
                        'fanart': item['fanart'],
                        'icon': item['thumb']
                    },
                    'info': {
                        'video': {
                            'plot': plot,
                            'title': label,
                        }
                    },
                    'is_folder': is_folder,
                    'is_playable': is_playable,
                    'url': get_url,
                })

        except Exception as e:
            self.logd('pimpletv._get_listing() ERROR', str(e))

        return listing



plugin = PimpleTV()
_ = plugin.initialize_gettext()
