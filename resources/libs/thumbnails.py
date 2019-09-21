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


locale.setlocale(locale.LC_ALL, '')

ID_PLUGIN = 'plugin.video.pimpletv'

__addon__ = xbmcaddon.Addon(id=ID_PLUGIN)
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__media__ = os.path.join(__path__, 'resources', 'media')
__image__ = os.path.join(__media__, 'image')
__libs__ = os.path.join(__path__, 'resources', 'libs')

MAX_LENGTH_TEXT = 420

# FONT_LARGE = ImageFont.truetype("resources/libs/BanderaProLight.otf", 40)
# FONT_LARGE_BOLD = ImageFont.truetype("resources/libs/BanderaPro-Bold.otf", 40)
# FONT_SMALL = ImageFont.truetype("resources/libs/BanderaPro.otf", 24)
FONT_LARGE = ImageFont.truetype(os.path.join(__libs__, 'ubuntu.ttf'), 40)
FONT_LARGE_BOLD = ImageFont.truetype(os.path.join(__libs__, 'ubuntu.ttf'), 44)
FONT_SMALL = ImageFont.truetype(os.path.join(__libs__, 'ubuntu.ttf'), 24)


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
    except Exception, e:
        print('[%s]: GET EXCEPT [%s]' % ('', e), 4)
        print url

def _cuttext(text, font, maxlength_text=MAX_LENGTH_TEXT):
    w, h = font.getsize(text)

    if w > maxlength_text:
        for i, ch in enumerate(text):
            print(text[0:i])
            w, h = font.getsize(text[0:i])
            print(w)
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

def create(**kwargs):
    thumb = os.path.join(kwargs['dir'], '%s_%s.png' % (kwargs['date_broadcast'], kwargs['match']))
    if not os.path.exists(thumb):
        ifon = Image.open(os.path.join(__image__, 'fon.png'))
        draw = ImageDraw.Draw(ifon)
        league = _cuttext(kwargs['league'], FONT_SMALL)
        vs = u'vs'
        d = kwargs['date_broadcast'].strftime(u"%A %d %B %Y").decode('utf-8')
        t = kwargs['date_broadcast'].strftime(u"%H:%M").decode('utf-8')

        com_home = _cuttext(kwargs['match'].split(u'\u2014')[0].strip(), FONT_LARGE_BOLD)
        com_away = _cuttext(kwargs['match'].split(u'\u2014')[1].strip(), FONT_LARGE_BOLD)

        _draw_text(draw, league, FONT_SMALL, ifon.size[0], 15)
        _draw_text(draw, com_home, FONT_LARGE_BOLD, ifon.size[0], 260)
        _draw_text(draw, vs, FONT_SMALL, ifon.size[0], 320)
        _draw_text(draw, com_away, FONT_LARGE_BOLD, ifon.size[0], 350)
        _draw_text(draw, d, FONT_SMALL, ifon.size[0], 430)
        _draw_text(draw, t, FONT_SMALL, ifon.size[0], 470)

        fd = _http_get_image(kwargs['home_logo'])
        image_file = io.BytesIO(fd)
        image_file.seek(0)
        ic1 = Image.open(image_file)
        ic1 = ic1.convert("RGBA")
        #print ic1.mode
        ic1.thumbnail((150, 150), Image.ANTIALIAS)
        fd = _http_get_image(kwargs['away_logo'])
        image_file = io.BytesIO(fd)
        image_file.seek(0)
        ic2 = Image.open(image_file)
        ic2.thumbnail((150, 150), Image.ANTIALIAS)
        ic2 = ic2.convert("RGBA")

        ifon.paste(ic1, (50, 80), ic1)
        ifon.paste(ic2, (300, 80), ic2)

        ifon.save(thumb)

    return thumb
