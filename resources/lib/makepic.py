# -*- coding: utf-8 -*-

import os
import urllib2
import io
from PIL import Image, ImageDraw, ImageFont

# locale.setlocale(locale.LC_ALL, '')

MAX_LENGTH_TEXT = 390

WEEKDAY = [u"Понедельник", u"Вторник", u"Среда",
           u"Четверг", u"Пятница", u"Суббота", u"Воскресенье"]

MONTHS = [u"января", u"февраля", u"марта", u"апреля", u"мая", u"июня", u"июля", u"августа",
          u"сентября", u"октября", u"ноября", u"декабря"]

ARTWORK_DATA = [
    {'type': 'poster',
     'league': 25,
     'com_home': 300,
     'vs': 380,
     'com_away': 420,
     'weekday': 550,
     'month': 585,
     'time_': 645,
     'size_thumbhome': (150, 150),
     'size_thumbaway': (150, 150),
     'pos_thumbhome': (50, 100),
     'pos_thumbaway': (270, 100), },

    {'type': 'thumb',
     'league': 10,
     'com_home': 220,
     'vs': None,
     'com_away': 280,
     'weekday': 350,
     'month': 380,
     'time_': 410,
     'size_thumbhome': (150, 150),
     'size_thumbaway': (150, 150),
     'pos_thumbhome': (50, 60),
     'pos_thumbaway': (270, 60), },

    {'type': 'fanart',
     'league': None,
     'com_home': None,
     'vs': None,
     'com_away': None,
     'weekday': None,
     'month': None,
     'time_': None,
     'size_thumbhome': (300, 300),
     'size_thumbaway': (300, 300),
     'pos_thumbhome': (100, 100),
     'pos_thumbaway': (460, 100), },
]


def _http_get_image(url):
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
        print('[%s]: GET EXCEPT [%s]' % ('', e), 4)
        print(url)


def _cuttext(text, font, maxlength_text=MAX_LENGTH_TEXT):
    w, h = font.getsize(text)
    if w > maxlength_text:
        for i, ch in enumerate(text):
            w, h = font.getsize(text[0:i])
            if w > maxlength_text:
                text = text[0:i]
                text += '...'
                break
    return text


def _get_indent_left_for_center(text, width_frame, font):
    w, h = font.getsize(text)
    return (width_frame - w) / 2


def _draw_text(draw, text, font, width_bkg, padding_top):
    if padding_top is None:
        return
    text = _cuttext(text, font)
    draw.text((_get_indent_left_for_center(text, width_bkg, font), padding_top), text, (0, 0, 0), font=font)


def _open_url_image(url):
    fd = _http_get_image(url)
    image_file = io.BytesIO(fd)
    image_file.seek(0)
    ic1 = Image.open(image_file)
    return ic1.convert("RGBA")


class CreatePictures(object):

    def __init__(self, plugin):
        self._plugin = plugin
        self.font_large_bolt = ImageFont.truetype(os.path.join(self._plugin.font(), 'BanderaPro.otf'), 50)
        self.font_small = ImageFont.truetype(os.path.join(self._plugin.font(), 'UbuntuCondensed-Regular.ttf'), 30)
        self.target_folder = os.path.join(self._plugin.userdata(), 'thumb')
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder)

    def create(self, **kwargs):

        league = _cuttext(kwargs['league'], self.font_small)
        vs = 'vs'
        weekday = WEEKDAY[kwargs['date_broadcast'].weekday()]  # a
        month = u'%s %s %s' % (
            kwargs['date_broadcast'].day, MONTHS[kwargs['date_broadcast'].month - 1],
            kwargs['date_broadcast'].year)
        # time_ = kwargs['date_broadcast'].strftime("%H:%M").decode('utf-8')
        time_ = kwargs['date_broadcast'].strftime("%H:%M")

        com_home = _cuttext(kwargs['match'].split(u'\u2014')[0].strip(), self.font_large_bolt)
        com_away = _cuttext(kwargs['match'].split(u'\u2014')[1].strip(), self.font_large_bolt)

        ic1 = _open_url_image(kwargs['home_logo'])
        ic2 = _open_url_image(kwargs['away_logo'])

        artwork = []

        for art in ARTWORK_DATA:
            if art['type'] == 'thumb' and not self._plugin.get_setting('is_thumb', True):
                artwork.append(artwork[0])
                continue
            if art['type'] == 'fanart' and not self._plugin.get_setting('is_fanart', True):
                artwork.append(self._plugin.fanart)
                continue

            file = os.path.join(self.target_folder, '%s_%s.png' %
                                (art['type'], str(kwargs['id'])))
            artwork.append(file)

            if not os.path.exists(file):
                ifon = Image.open(os.path.join(self._plugin.media(), 'fon_%s.png' % art['type']))
                ifon = ifon.convert("RGBA")
                draw = ImageDraw.Draw(ifon)

                _draw_text(draw, league, self.font_small, ifon.size[0], art['league'])
                _draw_text(draw, com_home, self.font_large_bolt, ifon.size[0], art['com_home'])
                _draw_text(draw, vs, self.font_small, ifon.size[0], art['vs'])
                _draw_text(draw, com_away, self.font_large_bolt, ifon.size[0], art['com_away'])
                _draw_text(draw, weekday, self.font_small, ifon.size[0], art['weekday'])
                _draw_text(draw, month, self.font_small, ifon.size[0], art['month'])
                _draw_text(draw, time_, self.font_large_bolt, ifon.size[0], art['time_'])

                # Сетевой рисунок
                # ic1 = _open_url_image(kwargs['home_logo'], art['size_thumbhome'])
                # ic2 = _open_url_image(kwargs['away_logo'], art['size_thumbaway'])

                ic1 = ic1.resize(art['size_thumbhome'], Image.ANTIALIAS)
                ic2 = ic2.resize(art['size_thumbaway'], Image.ANTIALIAS)

                # # Локальный рисунок
                # ic1 = Image.open(kwargs['home_logo'])
                # # ic1.thumbnail(art['size_thumbhome'], Image.ANTIALIAS)
                # ic1 = ic1.resize(art['size_thumbhome'], Image.ANTIALIAS)
                # ic1 = ic1.convert("RGBA")
                # ic2 = Image.open(kwargs['away_logo'])
                # ic2 = ic2.resize(art['size_thumbaway'], Image.ANTIALIAS)
                # # ic2.thumbnail(art['size_thumbaway'], Image.ANTIALIAS)
                # ic2 = ic2.convert("RGBA")

                ifon.paste(ic1, art['pos_thumbhome'], ic1)
                ifon.paste(ic2, art['pos_thumbaway'], ic2)

                # ifon.save(thumb.encode('utf-8'))
                ifon.save(file)

        artwork.append(artwork[1])
        return artwork
