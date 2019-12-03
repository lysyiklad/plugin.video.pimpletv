# -*- coding: utf-8 -*-

import datetime
import os
# from collections import OrderedDict
from urlparse import urlparse

import bs4
from dateutil.parser import *
from dateutil.tz import tzlocal, tzoffset

from .makepic import CreatePictures
from .plugin import Plugin

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


class PimpleTV(Plugin):
    """

            self._listing = {
                id : {
                    time: datetime,
                    id: int,
                    match: '',
                    league: '',
                    date: datetime,
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

    def __init__(self):
        super(PimpleTV, self).__init__()
        self._picmake = CreatePictures(self)

    def _parse_listing(self, html):
        """
        Парсим страницу для основного списка
        :param html:
        :return:
        """

        listing = {}

        soup = bs4.BeautifulSoup(html, 'html.parser')

        streams_day_soup = soup.findAll('div', {'class': 'streams-day'})

        for day_soup in streams_day_soup:
            day = '%s %s %s %s' % (
                day_soup.text.split()[0], MONTHS[day_soup.text.split()[1]], datetime.datetime.now().year, '%s')

            self.logd('update', day)

            for row in list(day_soup.next_siblings):
                try:
                    # if isinstance(row, bs4.element.Tag) and row['class'] == ['row']:
                    if row['class'] == ['row']:
                        cols = row.findAll(
                            'div', {'class': 'broadcast preview'})
                        for col in cols:

                            str_time = col.find('div', 'bottom-line').span.text
                            dt = parse(day % str_time)

                            date_local = self.convert_local_datetime(dt)

                            match = col.find('div', 'live-teams').text

                            # Создаем хэш
                            id = self.create_id(str(date_local) + match)

                            # id_real.append(id)

                            league = col.find('div', 'broadcast-category').text

                            poster, thumb, fanart = self._picmake.create(
                                home_logo=self._site +
                                          col.find('div', 'home-logo').img['src'],
                                away_logo=self._site +
                                          col.find('div', 'away-logo').img['src'],
                                # home_logo=os.path.join(self._plugin.media(), 'home.png'),
                                # away_logo=os.path.join(self._plugin.media(), 'away.png'),
                                id=id, date_broadcast=date_local, match=match, league=league)

                            # if id is not self._listing:
                            #    self._listing[id] = {}

                            self.logd(
                                'parse_listing', 'ADD MATCH - %s - %s' % (date_local, match))

                            listing[id] = {}
                            item = listing[id]
                            item['id'] = id
                            item['match'] = match
                            item['league'] = league
                            item['date'] = date_local
                            item['thumb'] = thumb
                            item['icon'] = ''
                            item['poster'] = poster
                            item['fanart'] = fanart
                            item['url_links'] = self._site + \
                                                col.find('div', 'live-teams').a['href']
                            if 'href' is not item:
                                item['href'] = []

                    else:
                        break
                except Exception as e:
                    self.logd('parse_listing', e)

        return listing

    def _parse_links(self, html):
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

    def _get_links(self, id):
        """
        Возвращаем список ссылок для папки конкретного элемента
        :param id:
        :return:
        """
        item = self.item(id)
        links = []

        for link in self.links(id):

            urlprs = urlparse(link['href'])

            plot = ''

            if urlprs.scheme == 'acestream':
                icon = os.path.join(self.dir('media'), 'ace.png')
            elif urlprs.scheme == 'sop':
                icon = os.path.join(self.dir('media'), 'sop.png')
                plot = '\n\n\nДля просмотра SopCast необходим плагин Plexus'
            else:
                icon = os.path.join(self.dir('media'), 'http.png')

            links.append({'label': '%s - %s - %s' % (link['title'], link['kbps'], link['resol']),
                          'info': {'video': {'title': item['match'], 'plot': plot}},
                          'thumb': icon,
                          'icon': icon,
                          'fanart': '',
                          'art': {'icon': icon, 'thumb': icon, },
                          'url': self.get_url(action='play', href=link['href'], id=id),
                          'is_playable': True})

        return links

    def _get_listing(self):
        """
        Возвращаем список для корневой виртуальной папки
        :return:
        """

        listing = []

        now_date = datetime.datetime.now().replace(tzinfo=tzlocal())

        self.logd('pimpletv._get_listing()', '%s' % now_date)

        try:
            for item in self._listing.values():
                status = 'FFFFFFFF'
                date_broadcast = item['date']
                if date_broadcast > now_date:
                    dt = date_broadcast - now_date
                    plot = self.format_timedelta(dt, u'Через')
                    status = 'FFFFFFFF'
                else:
                    dt = now_date - date_broadcast
                    if int(dt.total_seconds() / 60) < 110:
                        plot = u'Прямой эфир %s мин.' % int(
                            dt.total_seconds() / 60)
                        status = 'FFFF0000'
                    else:
                        plot = self.format_timedelta(dt, u'Закончен')
                        status = 'FF999999'

                title = u'[COLOR %s]%s[/COLOR]\n[B]%s[/B]\n[UPPERCASE]%s[/UPPERCASE]' % (
                    status, date_broadcast.strftime('%d.%m %H:%M'), item['match'], item['league'])

                label = u'[COLOR %s]%s[/COLOR] - [B]%s[/B]' % (
                    status, date_broadcast.strftime('%H:%M'), item['match'])
                plot = title + '\n' + plot                

                is_folder = True
                is_playable = False
                get_url = self.get_url(action='links', id=item['id'])

                # Сразу воспроизводить ссылку по-умолчанию
                if self.get_setting('is_play'):
                    is_folder = False
                    is_playable = True
                    href = ''

                    for h in item['href']:
                        if h['title'] == self.get_setting('play_engine').decode('utf-8'):
                            href = h['href']
                            break

                    get_url = self.get_url(
                        action='play', href=href, id=item['id'])

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
                            # 'imdbnumber': ,
                            # 'count': ,
                            # 'cast': ,
                            # 'dateadded': ,
                            # 'director': ,
                            # 'genre': ,
                            # 'country': ,
                            # 'year': '2019',
                            # 'rating': ,
                            'plot': plot,
                            # 'plotoutline': ,
                            'title': label,
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
                    'is_folder': is_folder,
                    'is_playable': is_playable,
                    'url': get_url,
                    # 'context_menu': ,
                    # 'online_db_ids':
                })

        except Exception as e:
            self.logd('pimpletv.matches() ERROR', '%s' % e)

        return listing
