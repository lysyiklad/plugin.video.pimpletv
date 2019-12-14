# -*- coding: utf-8 -*-

import datetime
import os

import bs4
from dateutil.parser import *
from urlparse import urlparse

from .plugin import Plugin
from . import makeart

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

    def __init__(self):
        super(PimpleTV, self).__init__()

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

        for day_soup in streams_day_soup:
            day = '%s %s %s %s' % (
                day_soup.text.split()[0], MONTHS[day_soup.text.split()[1]], datetime.datetime.now().year, '%s')

            self.logd('update', day)

            for row in list(day_soup.next_siblings):
                try:
                    if row['class'] == ['row']:
                        cols = row.findAll(
                            'div', {'class': 'broadcast preview'})
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

                            if self.is_create_artwork():
                                art = makeart.ArtWorkFootBall(self,
                                                              id=id_,
                                                              date=self.time_to_local(date_utc),
                                                              league=league,
                                                              home=home,
                                                              away=away,
                                                              logo_home=self._site +
                                                              col.find(
                                                                  'div', 'home-logo').img['src'],
                                                              logo_away=self._site +
                                                              col.find(
                                                                  'div', 'away-logo').img['src'])

                                if self.get_setting('is_thumb'):
                                    thumb = art.create_thumb()
                                    self.logd('_parse_listing', thumb)
                                if self.get_setting('is_fanart'):
                                    fanart = art.create_fanart()
                                    self.logd('_parse_listing', fanart)
                                if self.get_setting('is_poster'):
                                    poster = art.create_poster()
                                    self.logd('_parse_listing', poster)

                            self.logd(
                                'parse_listing', 'ADD MATCH - %s - %s' % (self.time_to_local(date_utc), match))

                            i += 2
                            if progress:
                                progress.update(i, message=match)

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

        return l

    def _get_listing(self):
        """
        Возвращаем список для корневой виртуальной папки
        :return:
        """

        listing = []

        now_utc = self.time_now_utc()

        self.logd('pimpletv._get_listing()', '%s' %
                  self.time_to_local(now_utc))

        try:
            for item in self._listing.values():
                date_ = item['date']
                if date_ > now_utc:
                    dt = date_ - now_utc
                    plot = self.format_timedelta(dt, u'Через')
                    status = 'FFFFFFFF'
                else:
                    dt = now_utc - date_
                    if int(dt.total_seconds() / 60) < 110:
                        plot = u'Прямой эфир %s мин.' % int(
                            dt.total_seconds() / 60)
                        status = 'FFFF0000'
                    else:
                        plot = self.format_timedelta(dt, u'Закончен')
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
