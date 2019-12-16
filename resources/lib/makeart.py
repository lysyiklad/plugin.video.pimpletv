# -*- coding: utf-8 -*-

import os
import urllib2
import io
from PIL import Image, ImageDraw, ImageFont
import datetime

# locale.setlocale(locale.LC_ALL, '')

MAX_LENGTH_TEXT = 370

WEEKDAY = [u"Понедельник", u"Вторник", u"Среда",
           u"Четверг", u"Пятница", u"Суббота", u"Воскресенье"]

MONTHS = [u"января", u"февраля", u"марта", u"апреля", u"мая", u"июня", u"июля", u"августа",
          u"сентября", u"октября", u"ноября", u"декабря"]

SIZE_FONT_LEAGUE = 45
SIZE_FONT_COMMAND = 55
SIZE_FONT_TIME = 60
SIZE_FONT_WEEKDAY = 35

SIZE_FONT_LARGE1 = 50

ARTWORK_DATA = {
    'poster': {
        'league': 25,
        'com_home': 300,
        'vs': 365,
        'com_away': 410,
        'weekday': 530,
        'month': 575,
        'time': 645,
        'size': (150, 150),
        'pos_home': (50, 100),
        'pos_away': (270, 100), },

    'thumb': {
        'league': 10,
        'com_home': 220,
        'vs': None,
        'com_away': 280,
        'weekday': 335,
        'month': 380,
        'time': 420,
        'size': (150, 150),
        'pos_home': (50, 60),
        'pos_away': (270, 60), },

    'fanart': {
        'league': None,
        'com_home': None,
        'vs': None,
        'com_away': None,
        'weekday': None,
        'month': None,
        'time': None,
        'size': (250, 250),
        'pos_home': (100, 100),
        'pos_away': (460, 100), },
}


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



def _http_get_image(url):
    """
    :param url:
    :return:
    """
    try:
        req = urllib2.Request(url=url)
        req.add_header('User-Agent',
                       'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko')
        req.add_header('Content-Type',
                       'image/png')

        resp = urllib2.urlopen(req, timeout=10)
        http = resp.read()
        resp.close()
        return http
    except Exception as e:
        raise Exception('ERROR GET HTTP LOGO [%s] - %s' % (e, url))


def _open_url_image(url):
    fd = _http_get_image(url)
    image_file = io.BytesIO(fd)
    image_file.seek(0)
    ic1 = Image.open(image_file)
    return ic1


class ArtWorkFootBall(object):

    def __init__(self, plugin, **kwargs):
        self._plugin = plugin
        self._data = kwargs
        self.color_font = (0, 0, 0)
        # dark light transparent
        self._theme = 'light'

    def log(self, msg):
        if self._plugin:
            self._plugin.logd('ArtWorkFootBall', msg)

    @property
    def plugin(self):
        return self._plugin

    @property
    def league(self):
        return self._data['league']

    @property
    def weekday(self):
        return WEEKDAY[self._data['date'].weekday()]

    @property
    def month(self):
        return u'%s %s %s' % (self._data['date'].day, MONTHS[self._data['date'].month - 1], self._data['date'].year)

    @property
    def time(self):
        return self._data['date'].strftime("%H:%M")

    @property
    def vs(self):
        return 'vs'

    @property
    def logo_home(self):
        return self._data['logo_home']

    @property
    def logo_away(self):
        return self._data['logo_away']

    def file(self, type):
        return os.path.join(self.plugin.dir('thumb'), '%s_%s.png' % (type, str(self._data['id'])))

    def font(self, file, size):
        return ImageFont.truetype(os.path.join(self.plugin.dir('font'), file), size)

    @property
    def theme(self):
        return self._theme
   

    def _draw_text(self, draw, text, font, padding_top):
        if padding_top is None:
            return
        width_bkg = draw.im.size[0]
        text = _cuttext(text, font)
        draw.text((_get_indent_left_for_center(text, width_bkg, font),
                padding_top), text, self.color_font, font=font)

    def _paste_logo(self, type, ifon):
        try:
            ihome = _open_url_image(self.logo_home)
            iaway = _open_url_image(self.logo_away)
        except Exception as e:
            self.log('ERROR PASTE LOGO [%s] - %s - %s' %
                     (e, self.logo_home, self.logo_away))
            ihome = Image.open(self.plugin.icon)
            iaway = Image.open(self.plugin.icon)
            # ic2.thumbnail(ARTWORK_DATA[type]['size_thumbaway'], Image.ANTIALIAS)
        ihome = ihome.convert("RGBA")
        iaway = iaway.convert("RGBA")
        ihome = ihome.resize(ARTWORK_DATA[type]['size'], Image.ANTIALIAS)
        iaway = iaway.resize(ARTWORK_DATA[type]['size'], Image.ANTIALIAS)
        ifon.paste(ihome, ARTWORK_DATA[type]['pos_home'], ihome)
        ifon.paste(iaway, ARTWORK_DATA[type]['pos_away'], iaway)

    def _create_art(self, type):

        file = self.file(type)
        if os.path.exists(file):
            self.log('exists -%s' % file)
            return file
        try:

            ifon = Image.open(os.path.join(
                self.plugin.dir('media'), 'fon_%s%s.png' % (self.theme, type)))
            ifon = ifon.convert("RGBA")
            draw = ImageDraw.Draw(ifon)

            self._draw_text(draw, self.league, self.font(
                'ubuntu_condensed', SIZE_FONT_LEAGUE), ARTWORK_DATA[type]['league'])
            self._draw_text(draw, self._data['home'], self.font(
                'bandera_pro', SIZE_FONT_COMMAND), ARTWORK_DATA[type]['com_home'])
            self._draw_text(draw, self.vs, self.font('ubuntu',
                                                SIZE_FONT_WEEKDAY), ARTWORK_DATA[type]['vs'])
            self._draw_text(draw, self._data['away'], self.font(
                'bandera_pro', SIZE_FONT_COMMAND), ARTWORK_DATA[type]['com_away'])
            self._draw_text(draw, self.weekday, self.font(
                'ubuntu', SIZE_FONT_WEEKDAY), ARTWORK_DATA[type]['weekday'])
            self._draw_text(draw, self.month, self.font(
                'ubuntu', SIZE_FONT_WEEKDAY), ARTWORK_DATA[type]['month'])
            self._draw_text(draw, self.time, self.font('bandera_pro',
                                                  SIZE_FONT_TIME), ARTWORK_DATA[type]['time'])

            self._paste_logo(type, ifon)

            ifon.save(file)
            return file
        except Exception as e:
            self.log('ERROR CREATE ART [%s] - %s' % (e, file))
            return ''

    def create_poster(self):
        return self._create_art('poster')

    def create_thumb(self):
        return self._create_art('thumb')

    def create_fanart(self):
        theme = self._theme
        self._theme = ''
        fanart =  self._create_art('fanart')
        self._theme = theme
        return fanart

    def set_dark_theme(self):
        self._theme = 'dark'
        self.color_font = (255, 255, 255)

    def set_light_theme(self):
        self._theme = 'light'
        self.color_font = (0, 0, 0)

    def set_transparent_theme(self):
        self._theme = 'transparent'
        self.color_font = (255, 255, 255)

    def set_blue_theme(self):
        self._theme = 'blue'
        self.color_font = (255, 255, 255)
