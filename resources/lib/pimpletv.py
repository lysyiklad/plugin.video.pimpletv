# -*- coding: utf-8 -*-

import os
import datetime
import bs4
from dateutil.tz import tzlocal, tzoffset
from dateutil.parser import *
import urllib2
import pickle
from collections import OrderedDict

# from .database import Match, Link
from .makepic import CreatePictures

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
    with open(file, 'rt') as f:  # , encoding="utf-8" , errors='ignore'
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
        self._picmake = CreatePictures(self._plugin)
        self._date_scan = datetime.datetime.now()
        self._matches = OrderedDict()

        self.load()

        """
        self._matches = {
            id : {
                time: datetime,
                id: int,
                match: '',
                league: '',
                date_broadcast: datetime,
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

    @property
    def date_scan(self):
        return self._date_scan

    def load(self):
        fp = os.path.join(self._plugin.userdata(), 'match.pickle')
        if os.path.exists(fp):
            with open(fp, 'rb') as f:
                self._date_scan, self._matches = pickle.load(f)

    def dump(self):
        with open(os.path.join(self._plugin.userdata(), 'match.pickle'), 'wb') as f:
            pickle.dump([self._date_scan, self._matches], f)

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
            self._plugin.log('GET EXCEPT [%s]' % e)

    def update(self):

        # Проверка необходимости обновления БД
        if self.is_not_update():
            for id in self._matches:
                self.get_href_match(id)
            return

        self._date_scan = datetime.datetime.now()
       # html = GET_FILE(os.path.join(self._plugin.path, 'PimpleTV.htm'))
        html = self._http_get(SITE)

        #self._plugin.log(html)

        soup = bs4.BeautifulSoup(html, 'html.parser')

        streams_day_soup = soup.findAll('div', {'class': 'streams-day'})

        id_real = []

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

                            id_real.append(id)

                            league = col.find('div', 'broadcast-category').text

                            poster, thumb, fanart = self._picmake.create(
                                home_logo=SITE + col.find('div', 'home-logo').img['src'],
                                away_logo=SITE + col.find('div', 'away-logo').img['src'],
                                # home_logo=os.path.join(self._plugin.media(), 'home.png'),
                                # away_logo=os.path.join(self._plugin.media(), 'away.png'),
                                id=id, date_broadcast=date_local, match=match, league=league)

                            if id is not self._matches:
                                self._matches[id] = {}

                            m = self._matches[id]
                            m['id'] = id
                            m['match'] = match
                            m['league'] = league
                            m['date_broadcast'] = date_local
                            m['thumb'] = thumb
                            m['icon'] = ''
                            m['poster'] = poster
                            m['fanart'] = fanart
                            m['url_links'] = SITE + col.find('div', 'live-teams').a['href']
                            if 'href' is not m:
                                m['href'] = []

                            self.get_href_match(id)

                    else:
                        break
                except Exception as e:
                    print('PimpleTV.update() - error - %s' % e)

        # 1. Удалить из self._matches не действительные матчи
        # 2. Удалить из thumb не действительные картинки и их кеши
        #
        artwork_real = []
        id_bad = []
        for id, m in self._matches.items():
            # print(id)
            if id in id_real:
                if m['thumb']:
                    artwork_real.append(m['thumb'])
                if m['icon']:
                    artwork_real.append(m['icon'])
                if m['poster']:
                    artwork_real.append(m['poster'])
                if m['fanart']:
                    artwork_real.append(m['fanart'])
            else:
                id_bad.append(id)
                self.remove_thumb(m['thumb'])
                self.remove_thumb(m['icon'])
                self.remove_thumb(m['poster'])
                self.remove_thumb(m['fanart'])
                self.remove_cache_thumb(m['thumb'])
                self.remove_cache_thumb(m['icon'])
                self.remove_cache_thumb(m['poster'])
                self.remove_cache_thumb(m['fanart'])

        for id in id_bad:
            del self._matches[id]

        dir_thumb = os.path.join(self._plugin.userdata(), 'thumb')
        files = os.listdir(dir_thumb)

        # подчищаем хвосты
        for file in files:
            f = os.path.join(dir_thumb, file)
            if f not in artwork_real:  # and file not in exception_file:
                os.remove(f)
                self.remove_cache_thumb(f)

        self.dump()

    def remove_thumb(self, thumb):
        if os.path.exists(thumb):
            os.remove(thumb)

    def remove_cache_thumb(self, thumb):
        # определяем кеши картинок и удаляем кеши картинок из системы
        if self._plugin.get_cache_thumb_name:
            thumb_cache = self._plugin.get_cache_thumb_name(thumb)
            self._plugin.log(thumb_cache)
            if os.path.exists(thumb_cache):
                os.remove(thumb_cache)

    # def _get_minute_delta_now(self, id):
    #     return (self._matches[id]['date_broadcast'] - datetime.datetime.now().replace(tzinfo=tzlocal())).total_seconds() / 60

    def get_href_match(self, id):

        links = []

        self._plugin.log(type(id))

        for mm in self._matches:
            self._plugin.log(mm)
        try:

            links = self._matches[id]['href']
        except Exception as e:
            self._plugin.log(e)


        # dt = (self._matches[id]['date_broadcast'] - datetime.datetime.now().replace(
        #     tzinfo=tzlocal())).total_seconds() / 60
        if links: # or dt < 0 or dt > 60:
            return links

        #html = GET_FILE(os.path.join(self._plugin.path(), 'Link1.html'))
        html = self._http_get(self._matches[id]['url_links'])

        soup = bs4.BeautifulSoup(html, 'html.parser')

        broadcast_table = soup.find('table', {'class': 'broadcast-table'})

        if broadcast_table is None:
            return None

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

    def is_not_update(self):
        try:
            fp = os.path.join(self._plugin.userdata(), 'match.pickle')
            if not os.path.exists(fp):
                return False
            if not self._matches:
                return False
            # Время сканирования меньше текущего времени на self._plugin.get_setting('delta_scan', True) - мин.
            dt = (datetime.datetime.now() - self._date_scan).total_seconds() / 60
            if dt > self._plugin.get_setting('delta_scan', True):
                return False
            #
            #
            #
            #
        except Exception as e:
            self._plugin.log(e)
            return False
        return True

    def matches(self):

        self.update()
        now_date = datetime.datetime.now().replace(tzinfo=tzlocal())

        try:
            for m in self._matches.values():
                # date_broadcast = parse(m.date_broadcast)
                status = 'FFFFFFFF'
                date_broadcast = m['date_broadcast']
                if date_broadcast > now_date:
                    dt = date_broadcast - now_date
                    plot = format_timedelta(dt, u'Через')
                    status = 'FFFFFFFF'
                else:
                    dt = now_date - date_broadcast
                    if int(dt.total_seconds() / 60) < 110:
                        plot = u'Прямой эфир %s мин.' % int(dt.total_seconds() / 60)
                        status = 'FFFF0000'
                    else:
                        plot = format_timedelta(dt, u'Закончен')
                        status = 'FF999999'

                title = u'[COLOR %s]%s[/COLOR]\n[B]%s[/B]\n[UPPERCASE]%s[/UPPERCASE]' % (
                    status, date_broadcast.strftime('%d.%m %H:%M'), m['match'], m['league'])

                
                label = u'[COLOR %s]%s[/COLOR] - [B]%s[/B]' % (
                    status, date_broadcast.strftime('%H:%M'), m['match'])
                plot = title + '\n\n' + plot
                
                # yield {'label': m.match,
                #         'thumb': m.thumb,
                #         'fanart': m.fanart,
                #         'art': {'poster': m.poster},
                #         'info': {'video': {'title':title, 'plot': plot}},
                #         'icon': m.icon,
                #         'is_folder': False,
                #         'is_playable': True,
                #         'url': self._plugin.get_url(action='links', id=m.id),
                #         }

                yield {
                    'label': label,                    
                    'art': {       
                        'thumb': m['thumb'],
                        'poster': m['poster'],
                        'fanart': m['fanart'],
                        'icon': m['thumb']
                    },
                    'info': {
                        'video': {
                            # 'imdbnumber': ,
                            # 'count': ,
                            # 'cast': ,
                            # 'dateadded': ,
                            # 'director': ,
                            # 'genre': ,
                            # 'country': ,
                            # 'year': ,
                            # 'rating': ,
                            'plot': plot,
                            # 'plotoutline': ,
                            # 'title': ,
                            # 'sorttitle': ,
                            # 'duration': ,
                            # 'originaltitle': ,
                            # 'premiered': ,
                            # 'votes': ,
                            # 'trailer': ,
                            # 'mediatype': ,
                            # 'tagline': ,
                            # 'mpaa': ,
                            # 'playcount': ,
                        }
                    },
                    'is_folder': True,
                    'is_playable': False,
                    'url': self._plugin.get_url(action='links', id=m['id']),
                    # 'context_menu': ,
                    # 'online_db_ids':
                }

        except Exception as e:
            print(e)
