# -*- coding: utf-8 -*-

import os
import datetime
import bs4
from dateutil.tz import tzlocal, tzoffset
from dateutil.parser import *
import urllib2

from .database import DB
from .makepic import CreatePictures

ID_PLUGIN = 'plugin.video.pimpletv'

SITE = 'https://www.pimpletv.ru'

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


def GET_FILE(file):
    with open(file, 'rt', errors='ignore', encoding="utf-8") as f:
        try:
            return f.read()
        except Exception as e:
            print(e)
    return ''


def create_id_match(date_broadcast, match):
    return hash(date_broadcast + match)


def format_timedelta(dt, pref):
    h = int(dt.seconds / 3600)
    return u'{} {} {} {:02} мин.'.format(pref, u'%s дн.' % dt.days if dt.days else u'',
                                       u'%s ч.' % h if h else u'', int(dt.seconds % 3600 / 60))


class PimpleTV(object):
    tzs = 3

    def __init__(self, plugin):
        self._plugin = plugin
        self._db = DB(self._plugin)
        self._picmake = CreatePictures(self._plugin)

    def _http_get(self, url):
        try:
            req = urllib2.Request(url=url)
            req.add_header('User-Agent',
                           'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0'
                           ' (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; '
                           '.NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
            resp = urllib2.urlopen(req)
            http = resp.read()
            resp.close()
            return http
        except Exception as e:
            print('[%s]: GET EXCEPT [%s]' % (ID_PLUGIN, e), 4)
            self._plugin.log(url)

    def update(self):

        # Проверка необходимости обновления БД
        # if self.is_not_update():
        #    return

        time_scan = datetime.datetime.now()
        # html = GET_FILE(os.path.join(self._plugin.path(), 'PimpleTVnew.htm'))
        html = self._http_get(SITE)

        #self._plugin.log(html)

        soup = bs4.BeautifulSoup(html, 'html.parser')

        streams_day_soup = soup.findAll('div', {'class': 'streams-day'})

        ids = []

        for day_soup in streams_day_soup:
            day = '%s %s %s %s' % (
                day_soup.text.split()[0], MONTHS[day_soup.text.split()[1]], datetime.datetime.now().year, '%s')
            self._plugin.log(day)

            for row in list(day_soup.next_siblings):
                try:
                    # if isinstance(row, bs4.element.Tag) and row['class'] == ['row']:
                    if row['class'] == ['row']:
                        cols = row.findAll('div', {'class': 'broadcast preview'})
                        for col in cols:
                            # dbg_log(col.find('div', 'broadcast-category').text)
                            # dbg_log(SITE + col.find('div', 'home-logo').img['src'])
                            # dbg_log(SITE + col.find('div', 'away-logo').img['src'])
                            # dbg_log(col.find('div', 'live-teams').text)
                            # dbg_log(SITE + col.find('div', 'live-teams').a['href'])
                            # dbg_log(col.find('div', 'bottom-line').span.text)

                            str_time = col.find('div', 'bottom-line').span.text
                            dt = parse(day % str_time)
                            tz = tzoffset(None, self.tzs * 3600)
                            dt = dt.replace(tzinfo=tz)
                            date_local = dt.astimezone(tzlocal())
                            self._plugin.log(date_local)

                            match = col.find('div', 'live-teams').text

                            # Определяем хэш матча
                            id = create_id_match(str(date_local), match)

                            ids.append(id)

                            league = col.find('div', 'broadcast-category').text

                            poster, thumb, fanart, icon = self._picmake.create(
                                home_logo=SITE + col.find('div', 'home-logo').img['src'],
                                away_logo=SITE + col.find('div', 'away-logo').img['src'],
                                # home_logo=os.path.join(self._plugin.media(), 'home.png'),
                                # away_logo=os.path.join(self._plugin.media(), 'away.png'),
                                id=id, date_broadcast=date_local, match=match, league=league)

                            matchdb = self._db.get_match(id)
                            if matchdb is None:
                                self._db.add_match(time=time_scan,
                                                   id=id,
                                                   match=match,
                                                   league=league,
                                                   date_broadcast=date_local,
                                                   thumb=thumb,
                                                   icon=icon,
                                                   poster=poster,
                                                   fanart=fanart,
                                                   url_links=SITE + col.find('div', 'live-teams').a['href'])
                            else:
                                matchdb.time = time_scan
                                matchdb.thumb = thumb
                                matchdb.icon = icon
                                matchdb.poster = poster
                                matchdb.fanart = fanart

                        #  self.get_href_match(id)

                    else:
                        break
                except Exception as e:
                    print('PimpleTV.update() - error - %s' % e)

        # matchs_db = self._db.match.select()
        # # Определяем список файлов картинок, которые должны быть
        # active_artwork = []
        # for id in ids:
        #     active_artwork.append('poster_%s.png' % id)
        #     if self._plugin.get_setting('is_thumb', True):
        #         active_artwork.append('thumb_%s.png' % id)
        #     if self._plugin.get_setting('is_fanart', True):
        #         active_artwork.append('fanart_%s.png' % id)

        # # Удаляем старье
        # for match_db in matchs_db:
        #     if match_db.id not in ids:
        #         # определяем кеши картинок и удаляем кеши картинок из системы
        #         if self._plugin.get_cache_thumb_name:
        #             thumb_cache = self._plugin.get_cache_thumb_name(match_db.thumb)
        #             self._plugin.log(thumb_cache)
        #             if os.path.exists(thumb_cache):
        #                 os.remove(thumb_cache)
        #         # удаляем картинки из системы
        #         os.remove(match_db.poster)
        #         # удаляем матч из базы
        #         self._db.delete_match(match_db.id)

        # files = os.listdir(self._picmake.target_folder)

        # exception_file = ['match.db']

        # for file in files:
        #     if file not in active_artwork and file not in exception_file:
        #         f = os.path.join(self._picmake.target_folder, file)
        #         os.remove(f)
        #         if self._plugin.get_cache_thumb_name:
        #             thumb_cache = self._plugin.get_cache_thumb_name(f)
        #             self._plugin.log(thumb_cache)
        #             if os.path.exists(thumb_cache):
        #                 os.remove(thumb_cache)

    def get_href_match(self, id):
        links = self._db.get_href_match(id)
        if links is not None:
            return links

        # html = GET_FILE(os.path.join(self._plugin.path(), 'Link1.html'))
        html = self._http_get(self._db.get_url_href(id))

        soup = bs4.BeautifulSoup(html, 'html.parser')

        broadcast_table = soup.find('table', {'class': 'broadcast-table'})

        if broadcast_table is None:
            return None

        tbody = broadcast_table.find('tbody')

        links = []

        for tr in tbody.find_all('tr'):
            td = tr.find_all('td')
            links.append({
                'id': id,
                'title': td[0].find('a').text,
                'kbps': td[2].text,
                'resol': td[3].text,
                'href': td[5].find('a')['href'],
            })

        self._db.add_link(id, links)

        return links

    def is_not_update(self):
        try:
            # Время сканирования меньше текущего времени на self._plugin.get_setting('delta_scan', True) - мин.
            if ((datetime.datetime.now() - self._db.date_scan()).seconds / 60) > self._plugin.get_setting('delta_scan',
                                                                                                          True):
                return False
            #
            #
            #
            #
        except Exception:
            return False
        return True

    def matches(self):

        #self.update()
        self._plugin.log('1111111111111111111111111111')
        now_date = datetime.datetime.now().replace(tzinfo=tzlocal())

        match = self._db.get_match(668941931662562689)
        self._plugin.log(match.id)

        yield {'label': 'str(match.id)',
               'url': self._plugin.get_url(action='links', id=131323132121), }



        # # now_date = datetime.datetime(2019, 9, 20, 0, 0, 0).replace(tzinfo=tzlocal())
        # matches = self._db.get_matches()  #match.select().order_by(self._db.match.date_broadcast)
        # self._plugin.log('222222222222222222222222222222')
        # self._plugin.log(type(matches))
        # self._plugin.log(type(self._db.match))
        # try:
        #     for m in matches:
        #         self._plugin.log('3333333333333333333333333333333')
        #         date_broadcast = parse(m.date_broadcast)
        #         if date_broadcast > now_date:
        #             dt = date_broadcast - now_date
        #             plot = format_timedelta(dt, 'Через')
        #         else:
        #             dt = now_date - date_broadcast
        #             if int(dt.total_seconds() / 60) < 110:
        #                 plot = 'Прямой эфир %s мин.' % int(dt.total_seconds() / 60)
        #             else:
        #                 plot = format_timedelta(dt, 'Закончен')

        #         if dt.seconds < -6600:
        #             status = 'FF999999'
        #         elif dt.seconds > 0:
        #             status = 'FFFFFFFF'
        #         else:
        #             status = 'FFFF0000'

        #         label = '[COLOR %s]%s[/COLOR] - [B]%s[/B]   [UPPERCASE]%s[/UPPERCASE]' % (
        #             status, date_broadcast.strftime('%d.%m %H:%M'), m.match, m.league)

        #         # plot = '%s\nЧерез %s' % (label, str(before_time))
        #         plot = label + '\n[B]' + plot + '[/B]'

        #         yield {'label': label,
        #          'thumb': m.thumb,
        #          'fanart': m.fanart,
        #          'poster': m.poster,
        #          'info': {'video': {'title': 'TITLE', 'plot': plot}},
        #          'icon': m.icon,
        #          'is_folder': False,
        #          'is_playable': True,
        #          'url': self._plugin.get_url(action='links', id=m.id),
        #          }

        #         # yield {
        #         #     'label': label,
        #         #     'art': {
        #         #         'thumb': m.thumb,
        #         #         'poster': m.poster,
        #         #         'fanart': m.fanart,
        #         #         'icon': m.icon
        #         #     },
        #         #     'info': {
        #         #         'video': {
        #         #             # 'imdbnumber': ,
        #         #             # 'count': ,
        #         #             # 'cast': ,
        #         #             # 'dateadded': ,
        #         #             # 'director': ,
        #         #             # 'genre': ,
        #         #             # 'country': ,
        #         #             # 'year': ,
        #         #             # 'rating': ,
        #         #             'plot': plot,
        #         #             # 'plotoutline': ,
        #         #             # 'title': ,
        #         #             # 'sorttitle': ,
        #         #             # 'duration': ,
        #         #             # 'originaltitle': ,
        #         #             # 'premiered': ,
        #         #             # 'votes': ,
        #         #             # 'trailer': ,
        #         #             # 'mediatype': ,
        #         #             # 'tagline': ,
        #         #             # 'mpaa': ,
        #         #             # 'playcount': ,
        #         #         }
        #         #     },
        #         #     'is_folder': False,
        #         #     'is_playable': True,
        #         #     'url': self._plugin.get_url(action='links', id=m.id),
        #         #     # 'context_menu': ,
        #         #     # 'online_db_ids':
        #         # }

        # except Exception as e:
        #     print(e)
