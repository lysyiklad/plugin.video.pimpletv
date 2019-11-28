# -*- coding: utf-8 -*-
import os
from urlparse import urlparse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# import urllib

from resources.lib.pimpletv import PimpleTV
from resources.lib.plugin import PimpletvPlugin


ID_PLUGIN = 'plugin.video.pimpletv'
__addon__ = xbmcaddon.Addon(id=ID_PLUGIN)
__path__ = __addon__.getAddonInfo('path')

plugin = PimpletvPlugin()

pimpletv = PimpleTV(plugin)


@plugin.action()
def root():    
    return plugin.create_listing(pimpletv.matches(), 
                                content='movies', 
                                sort_methods=(xbmcplugin.SORT_METHOD_DATEADDED, xbmcplugin.SORT_METHOD_VIDEO_RATING), 
                                cache_to_disk=True)
    #return pimpletv.matches()


@plugin.action()
def links(params):
    id = params['id']
    links = pimpletv.get_href_match(int(id))
    plugin.log(links)

    for link in links:
        
        urlprs = urlparse(link['href'])

        plot = ''   #plot_base

        if urlprs.scheme == 'acestream':
            icon = os.path.join(plugin.media(), 'ace.png')
        elif urlprs.scheme == 'sop':
            icon = os.path.join(plugin.media(), 'sop.png')
            plot = '\n\n\nДля просмотра SopCast необходим плагин Plexus'
        else:
            icon = os.path.join(plugin.media(), 'http.png')

        yield {'label': '%s - %s - %s' % (link['title'], link['kbps'], link['resol']),
                 'info': {'video': {'title': '', 'plot': plot}},
                 'thumb': icon,
                 'icon': icon,
                 'fanart': '',
                 'art': {'icon': icon, 'thumb': icon, },
                  'url': plugin.get_url(action='play', href=link['href']),
                  'is_playable': True}



@plugin.action()
def play(params):
    path = ''
    item = 0
    url = urlparse(params['href'])
    if url.scheme == 'acestream':
        if __addon__.getSetting('is_default_play') == 'true':        
            item = int(__addon__.getSetting('default_ace'))
        else:
            dialog = xbmcgui.Dialog()
            item = dialog.contextmenu(
                ['ACESTREAM %s [%s]' % ('hls' if __addon__.getSetting(
                    'is_hls1') == 'true' else '', __addon__.getSetting('ipace1')),
                 'ACESTREAM %s [%s]' % ('hls' if __addon__.getSetting(
                     'is_hls2') == 'true' else '', __addon__.getSetting('ipace2')),
                 'HTTPAceProxy [%s]' % __addon__.getSetting('ipproxy'), 'Add-on TAM [127.0.0.1]'])
            if item == -1:
                return

        cid = url.netloc

        if item == 0:
            path = 'http://%s:6878/ace/%s?id=%s' % (
                __addon__.getSetting('ipace1'), 'manifest.m3u8' if __addon__.getSetting(
                    'is_hls1') == 'true' else 'getstream', cid)
        elif item == 1:
            path = 'http://%s:6878/ace/%s?id=%s' % (
                __addon__.getSetting('ipace2'), 'manifest.m3u8' if __addon__.getSetting(
                    'is_hls2') == 'true' else 'getstream', cid)
        elif item == 2:
            path = "http://%s:8000/pid/%s/stream.mp4" % (
                __addon__.getSetting('ipproxy'), cid)
        elif item == 3:
            path = "plugin://plugin.video.tam/?mode=play&url=%s&engine=ace_proxy" % params['url']
    elif url.scheme == 'sop':
        path = "plugin://program.plexus/?mode=2&url=" + \
            url.geturl() + "&name=Sopcast"
    else:
        path = url.geturl()

    plugin.log('PPPPPPPPPPPPPPPPPPPPPPPPPPPP %s' % path)

    return PimpletvPlugin.resolve_url(path, succeeded=True)


if __name__ == '__main__':
    plugin.run()
