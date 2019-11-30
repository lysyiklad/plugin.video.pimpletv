# -*- coding: utf-8 -*-
import os
from urlparse import urlparse
import xbmc
import xbmcgui
import xbmcplugin
#import xbmcaddon

from resources.lib.plugin import PimpletvPlugin

# ID_PLUGIN = 'plugin.video.pimpletv'
# __addon__ = xbmcaddon.Addon(id=ID_PLUGIN)
# __path__ = __addon__.getAddonInfo('path')

plugin = PimpletvPlugin()


@plugin.action()
def root():    
    return plugin.create_listing(plugin.matches(), 
                                content='movies', 
                                sort_methods=(xbmcplugin.SORT_METHOD_DATEADDED, xbmcplugin.SORT_METHOD_VIDEO_RATING), 
                                cache_to_disk=True)
    


@plugin.action()
def links(params):
    id = int(params['id'])
    links = plugin.get_href_match(id)
    plugin.logd('links', links)

    if not links:                
        yield {'label': 'Ссылок на трансляции нет, возможно появятся позже!',
                        'info': {'video': {'title': 'https://www.pimpletv.ru', 'plot': 'https://www.pimpletv.ru'}},
                        'art': {'icon': plugin.icon, 'thumb': plugin.icon, },
                        'url': plugin.get_url(action='play', href='https://www.ixbt.com/multimedia/video-methodology/camcorders-and-others/htc-one-x-avc-baseline@l3.2-1280x720-variable-fps-aac-2ch.mp4'),
                        'is_playable': True}
        return

    match = plugin.get_match(id)

    for link in links:
        
        urlprs = urlparse(link['href'])

        plot = ''   #plot_base

        if urlprs.scheme == 'acestream':
            icon = os.path.join(plugin.dir('media'), 'ace.png')
        elif urlprs.scheme == 'sop':
            icon = os.path.join(plugin.dir('media'), 'sop.png')
            plot = '\n\n\nДля просмотра SopCast необходим плагин Plexus'
        else:
            icon = os.path.join(plugin.dir('media'), 'http.png')

        yield {'label': '%s - %s - %s' % (link['title'], link['kbps'], link['resol']),
               'info': {'video': {'title': match['match'], 'plot': plot}},
                 'thumb': icon,
                 'icon': icon,
                 'fanart': '',
                 'art': {'icon': icon, 'thumb': icon, },
                  'url': plugin.get_url(action='play', href=link['href'], id=id),
                  'is_playable': True }


                  
def get_path_acestream(href):
    path = ''
    item = 0
    url = urlparse(href)
    if plugin.get_setting('is_default_ace'):
        item = plugin.get_setting('default_ace')
    else:
        dialog = xbmcgui.Dialog()
        list = ['ACESTREAM %s [%s]' % ('hls' if plugin.get_setting('is_hls1') else '', plugin.get_setting('ipace1')),
             'ACESTREAM %s [%s]' % ('hls' if plugin.get_setting('is_hls2') else '', plugin.get_setting('ipace2')),
             'HTTPAceProxy [%s]' % plugin.get_setting('ipproxy'), 
             'Add-on TAM [127.0.0.1]']        
             
        
        if plugin.version_kodi < 17:
            item = dialog.select('Выбор способа воспроизведения Ace Straem', list=list)
        else:
            item = dialog.contextmenu(list)
          
             
        if item == -1:
            return None

    cid = url.netloc

    if item == 0:
        path = 'http://%s:6878/ace/%s?id=%s' % (
            plugin.get_setting('ipace1'), 'manifest.m3u8' if plugin.get_setting(
                'is_hls1') else 'getstream', cid)
    elif item == 1:
        path = 'http://%s:6878/ace/%s?id=%s' % (
            plugin.get_setting('ipace2'), 'manifest.m3u8' if plugin.get_setting(
                'is_hls2') else 'getstream', cid)
    elif item == 2:
        path = "http://%s:8000/pid/%s/stream.mp4" % (
            plugin.get_setting('ipproxy'), cid)
    elif item == 3:
        path = "plugin://plugin.video.tam/?mode=play&url=%s&engine=ace_proxy" % href
        
    return path

def get_path_sopcast(href):
    url = urlparse(href)
    path = "plugin://program.plexus/?mode=2&url=" + url.geturl() + "&name=Sopcast"    
    return path
    
def notification_nolinks(msg):
    title = plugin.name.encode('utf-8')
    time = 500 
    icon = plugin.icon.encode('utf-8')
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (title, msg, time, icon))


@plugin.action()
def play(params):
    path = ''    
    plugin.logd('play', params)
    if 'href' not in params or not params['href']:
        links = plugin.get_href_match(int(params['id']))
        plugin.logd('play', links)
        for h in links:
            if h['title'] == plugin.get_setting('play_engine').decode('utf-8'):
                params['href'] = h['href']
                break
        if 'href' not in params or not params['href']:
            msg = 'НЕТ ССЫЛОК НА ТРАНСЛЯЦИЮ МАТЧА!'
            plugin.logd('play', msg)
            notification_nolinks(msg)
            return None


    href = params['href']
    url = urlparse(href)    
    if url.scheme == 'acestream':
        path = get_path_acestream(href)
    elif url.scheme == 'sop':
        path = get_path_sopcast(href)
    else:
        path = url.geturl()
    
    if not path:
        msg = 'ПУСТОЙ ПУТЬ НА ТРАНСЛЯЦИЮ МАТЧА!'
        notification_nolinks(msg)
        plugin.logd('play', msg)
        return None
    
    plugin.logd('play', 'PATH PLAY: %s' % path)
    
    return PimpletvPlugin.resolve_url(path, succeeded=True)                  

if __name__ == '__main__':
    plugin.run()
