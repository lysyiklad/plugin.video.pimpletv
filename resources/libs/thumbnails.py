#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import io
from StringIO import StringIO
from PIL import Image, ImageDraw, ImageFont
import datetime
import locale
import urllib2

import xbmcaddon
import xbmc


locale.setlocale(locale.LC_ALL, '')
#locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

ID_PLUGIN = 'plugin.video.pimpletv'

__addon__ = xbmcaddon.Addon(id=ID_PLUGIN)
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__media__ = os.path.join(__path__, 'resources', 'media')
__image__ = os.path.join(__media__, 'image')
__libs__ = os.path.join(__path__, 'resources', 'libs')

MAX_LENGTH_TEXT = 390

WEEKDAY = [u"Понедельник", u"Вторник", u"Среда",
           u"Четверг", u"Пятница", u"Суббота", u"Воскресенье"]

MONTHS = [u"января", u"февраля", u"марта", u"апреля", u"мая", u"июня", u"июля", u"августа",
          u"сентября", u"октября", u"ноября", u"декабря"]


# FONT_LARGE = ImageFont.truetype("resources/libs/BanderaProLight.otf", 40)
#FONT_LARGE_BOLD = ImageFont.truetype(
#    os.path.join(__libs__, "BanderaPro-Bold.otf"), 54)
#FONT_SMALL = ImageFont.truetype(os.path.join(__libs__, "BanderaPro.otf"), 30)

#FONT_LARGE = ImageFont.truetype(os.path.join(__libs__, 'ubuntu.ttf'), 40)
FONT_LARGE_BOLD = ImageFont.truetype(os.path.join(__libs__, 'UbuntuCondensed-Regular.ttf'), 52)
FONT_SMALL = ImageFont.truetype(os.path.join(__libs__, 'UbuntuCondensed-Regular.ttf'), 30)

def _http_get_image(url):
    try:
        req = urllib2.Request(url=url)
        req.add_header('User-Agent',
                       'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0'
                       ' (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; '
                       '.NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
        resp = urllib2.urlopen(req)
        print resp
        http = resp.read()
        print len(http)
        resp.close()
        return http
    except Exception, e:
        print('[%s]: GET EXCEPT [%s]' % ('', e), 4)
        print url

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
    text = _cuttext(text, font)
    draw.text((_get_indent_left_for_center(text, width_bkg, font), padding_top), text, (0, 0, 0), font=font)

def _open_url_image(url, size=None):
    fd = _http_get_image(url)
    image_file = io.BytesIO(fd)
    image_file.seek(0)
    ic1 = Image.open(image_file)
    if not size is None:
        ic1.thumbnail((150, 150), Image.ANTIALIAS)
    return ic1.convert("RGBA")


def create(**kwargs):
    thumb = os.path.join(kwargs['dir'], '%s.png' % str(hash(str(kwargs['date_broadcast']) + kwargs['match'])))    

    thumb_cached = xbmc.getCacheThumbName(thumb)
    thumb_cached = thumb_cached.replace('tbn', 'png')
    thumb_cached = os.path.join(os.path.join(xbmc.translatePath("special://thumbnails"), thumb_cached[0], thumb_cached))
    if not os.path.exists(thumb):
        ifon = Image.open(os.path.join(__image__, 'fon.png'))
        ifon = ifon.convert("RGBA")
        draw = ImageDraw.Draw(ifon)
        league = _cuttext(kwargs['league'], FONT_SMALL)
        vs = 'vs'
        a = WEEKDAY[kwargs['date_broadcast'].weekday()]
        d = u'%s %s %s' % (kwargs['date_broadcast'].day, MONTHS[kwargs['date_broadcast'].month], kwargs['date_broadcast'].year)
        t = kwargs['date_broadcast'].strftime("%H:%M").decode('utf-8')

        com_home = _cuttext(kwargs['match'].split(
            u'\u2014')[0].strip(), FONT_LARGE_BOLD)
        com_away = _cuttext(kwargs['match'].split(
            u'\u2014')[1].strip(), FONT_LARGE_BOLD)

        _draw_text(draw, league, FONT_SMALL, ifon.size[0], 25)
        _draw_text(draw, com_home, FONT_LARGE_BOLD, ifon.size[0], 300)
        _draw_text(draw, vs, FONT_SMALL, ifon.size[0], 380)
        _draw_text(draw, com_away, FONT_LARGE_BOLD, ifon.size[0], 420)
        _draw_text(draw, a, FONT_SMALL, ifon.size[0], 550)
        _draw_text(draw, d, FONT_SMALL, ifon.size[0], 585)
        _draw_text(draw, t, FONT_LARGE_BOLD, ifon.size[0], 645)

        ic1 = _open_url_image(kwargs['home_logo'], (150, 150))
        ic2 = _open_url_image(kwargs['away_logo'], (150, 150))
       
        ifon.paste(ic1, (50, 100), ic1)
        ifon.paste(ic2, (270, 100), ic2)
        
        ifon.save(thumb.encode('utf-8'))

        #os.remove(thumb)

    return thumb
